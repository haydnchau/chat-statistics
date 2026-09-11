#!/usr/bin/env python3
"""
python3 process_chat.py [path-to-inbox]

Scans an Instagram data export's `inbox/` folder, lets you pick a
conversation, and writes word-frequency stats to site/public/data/
for the React site to read.

Expected layout (from an Instagram "Download your information" export):
    your_instagram_activity/messages/inbox/<conversation_id>/message_1.json
    your_instagram_activity/messages/inbox/<conversation_id>/message_2.json
    ...

If you point this at the whole export, or just at the `inbox` folder
directly, it will find it.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "site" / "public" / "data"
MANIFEST_PATH = DATA_DIR / "manifest.json"

# A small set of very common English words to exclude from "most used"
# rankings so results aren't dominated by "the", "you", "i", etc.
# Deliberately not exhaustive -- this is about surfacing interesting words,
# not linguistics.
STOPWORDS = {
    "i", "im", "you", "u", "the", "a", "an", "to", "and", "is", "it",
    "of", "in", "that", "on", "for", "with", "was", "this", "but",
    "are", "be", "at", "so", "just", "my", "me", "your", "have", "not",
    "do", "if", "or", "like", "he", "she", "we", "they", "as", "its",
    "no", "yes", "was", "were", "will", "would", "can", "cant", "dont",
    "did", "didnt", "then", "than", "there", "their", "them", "what",
    "when", "how", "why", "who", "which", "from", "by", "about", "up",
    "out", "get", "got", "ok", "okay", "lol", "lmao", "haha", "hahaha",
}

# \w+ (word chars: unicode letters, digits, underscore). Digits are allowed
# *inside* a word -- e.g. "youngs3o" -- instead of splitting on them like
# before, since that was chopping usernames in half. Pure-number tokens
# ("2024", "3") are filtered out separately in tokenize().
WORD_RE = re.compile(r"@\S+|\w+(?:'\w+)*", re.UNICODE)


# ---------------------------------------------------------------------------
# Instagram export quirks
# ---------------------------------------------------------------------------

def fix_mojibake(obj):
    """
    Instagram's JSON export has a long-standing bug: text is UTF-8 but the
    exporter escapes it as if it were Latin-1, so emoji/accents/curly quotes
    come out garbled (e.g. "café" -> "cafÃ©"). Re-encoding as Latin-1 then
    decoding as UTF-8 undoes it. Applied recursively across the whole
    parsed JSON structure.
    """
    if isinstance(obj, str):
        try:
            return obj.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return obj
    if isinstance(obj, list):
        return [fix_mojibake(x) for x in obj]
    if isinstance(obj, dict):
        return {k: fix_mojibake(v) for k, v in obj.items()}
    return obj


# ---------------------------------------------------------------------------
# Finding conversations
# ---------------------------------------------------------------------------

def find_inbox(start: Path) -> Path | None:
    """Locate the `inbox` folder whether the user points at it directly,
    the export root, or has this project extracted as a subfolder inside
    .../messages/inbox/ itself (the recommended setup)."""
    if start.name == "inbox" and start.is_dir():
        return start
    # Look upward first -- covers running from inbox/chat-stats/.
    for parent in [start, *start.parents]:
        if parent.name == "inbox" and parent.is_dir():
            return parent
    # Fall back to searching downward -- covers pointing at the export root.
    candidates = [c for c in start.rglob("inbox") if c.is_dir()]
    return candidates[0] if candidates else None


def load_conversations(inbox: Path):
    """Returns list of dicts: {path, id, title, participants, message_count}"""
    conversations = []
    for convo_dir in sorted(inbox.iterdir()):
        if not convo_dir.is_dir():
            continue
        msg_files = sorted(convo_dir.glob("message_*.json"))
        if not msg_files:
            continue
        try:
            first = fix_mojibake(json.loads(msg_files[0].read_text(encoding="utf-8")))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        participants = [p.get("name", "?") for p in first.get("participants", [])]
        msg_count = sum(
            len(fix_mojibake(json.loads(f.read_text(encoding="utf-8"))).get("messages", []))
            for f in msg_files
        )
        conversations.append({
            "path": convo_dir,
            "id": convo_dir.name,
            "title": first.get("title") or ", ".join(participants),
            "participants": participants,
            "message_count": msg_count,
        })
    return conversations


def prompt_for_conversation(conversations):
    print(f"\nFound {len(conversations)} conversations:\n")
    for i, c in enumerate(conversations, 1):
        print(f"  [{i:>3}] {c['title'][:45]:<45} {c['message_count']:>6} messages")
    print()
    choice = input("Pick a number (or paste a conversation folder id): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(conversations):
        return conversations[int(choice) - 1]
    for c in conversations:
        if c["id"] == choice:
            return c
    print("Not found.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Loading + normalizing messages
# ---------------------------------------------------------------------------

def load_all_messages(convo_dir: Path):
    all_msgs = []
    for f in sorted(convo_dir.glob("message_*.json")):
        data = fix_mojibake(json.loads(f.read_text(encoding="utf-8")))
        all_msgs.extend(data.get("messages", []))
    all_msgs.sort(key=lambda m: m.get("timestamp_ms", 0))
    return all_msgs


ELONGATION_RE = re.compile(r"(.)\1{2,}")  # 3+ repeats of any char


def normalize_word(word: str):
    """
    Collapse elongated words ("soooo" / "sooo") down to a canonical form
    so they count as one word instead of many distinct ones.

    Heuristic for now (no dictionary lookup yet -- flagged as a future
    improvement): collapse any run of 3+ repeated letters down to 2.
    "soooo" -> "soo", "hiiiii" -> "hii". This intentionally still
    distinguishes real double letters (e.g. "book") from stretched ones,
    while merging all degrees of stretching into one bucket.

    Returns (canonical_word, was_elongated).
    """
    collapsed = ELONGATION_RE.sub(lambda m: m.group(1) * 2, word)
    return collapsed, collapsed != word


ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")
TRAILING_PUNCT_RE = re.compile(r"[^\w]+$", re.UNICODE)


def tokenize(text: str):
    text = ZERO_WIDTH_RE.sub("", text)
    tokens = []
    for raw in WORD_RE.findall(text):
        if raw.startswith("@"):
            raw = TRAILING_PUNCT_RE.sub("", raw)
            if len(raw) <= 1:
                continue
        elif raw.isdigit():
            continue  # bare numbers ("2024", "3") aren't interesting as "words"
        tokens.append(raw.lower())
    return tokens


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Attachments (photos, videos, reels, links, ...)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Reactions & system-notification messages ("X reacted to your message",
# "X sent an attachment.", etc.) -- these aren't real chat words and were
# previously leaking into the word rankings.
# ---------------------------------------------------------------------------

# Some exports store a reaction as its own pseudo-message ("<name> reacted
# 😍 to your message") rather than (or in addition to) a `reactions` list
# on the reacted-to message. This extracts actor + emoji from that text.
REACTION_TEXT_RE = re.compile(
    r"^(?:(?P<actor>.+?)\s+)?[Rr]eacted\s+[\"'\u201c\u2018]?\s*(?P<emoji>\S+?)\s*[\"'\u201d\u2019\u201c]?\s+to\s+(?:your|a)\s+message\.?$",
    re.IGNORECASE,
)

# Best-effort match for other English-language system notifications that
# aren't real typed messages. Not exhaustive, and assumes an English
# account UI -- a language-independent detector would need real examples
# from other locales to build against.
SYSTEM_MESSAGE_RE = re.compile(
    r"^.*?\b(?:"
    r"sent an? (?:attachment|photo|video|voice message|link|gif|sticker|reel)|"
    r"liked a message|"
    r"shared a story|"
    r"started a video chat|"
    r"missed a video chat|"
    r"missed a call|"
    r"changed the group photo|"
    r"named the group"
    r")\b.*?\.?$",
    re.IGNORECASE,
)


def classify_attachment(msg):
    """
    Returns (type, quantity) for media/share messages, or (None, 0) for a
    normal text message. Detected via the actual JSON keys Instagram uses
    for each attachment kind -- not by pattern-matching the placeholder
    sentence ("X sent an attachment."), since that text is in whatever
    language the account's UI was set to and isn't reliable to parse.
    """
    if msg.get("audio_files"):
        return "voice message", len(msg["audio_files"])
    if msg.get("gifs"):
        return "gif", len(msg["gifs"])
    if msg.get("sticker"):
        return "sticker", 1
    if msg.get("share"):
        link = (msg["share"].get("link") or "").lower()
        if "/reel/" in link:
            return "reel", 1
        if "/stories/" in link:
            return "story", 1
        if "/p/" in link:
            return "post", 1
        return "link", 1
    return None, 0


def compute_stats(messages, exclude_stopwords=True):
    overall = Counter()
    per_sender = defaultdict(Counter)
    elongated_examples = defaultdict(set)  # canonical -> raw variants seen
    message_counts = Counter()
    attachment_counts = defaultdict(Counter)  # sender -> {type: qty}
    reaction_counts = Counter()  # actor -> reactions given
    reaction_emoji_counts = Counter()  # emoji -> times used
    total_words = 0
    unmatched_reaction_samples = []  # debug: content mentioning "react" that slipped through

    for msg in messages:
        sender = msg.get("sender_name", "Unknown")

        # Standard schema: reactions attached directly to the message.
        for r in msg.get("reactions", []):
            actor = r.get("actor", "Unknown")
            emoji = r.get("reaction", "")
            reaction_counts[actor] += 1
            if emoji:
                reaction_emoji_counts[emoji] += 1

        content = msg.get("content")

        # Fallback schema: reaction shows up as its own pseudo-message.
        if content and not msg.get("reactions"):
            m = REACTION_TEXT_RE.match(content.strip())
            if m:
                actor = m.group("actor") or sender
                reaction_counts[actor] += 1
                reaction_emoji_counts[m.group("emoji")] += 1
                continue

        attach_type, attach_qty = classify_attachment(msg)
        if attach_type:
            attachment_counts[sender][attach_type] += attach_qty
            continue  # don't tokenize the placeholder text for these

        if not content:
            continue  # unsent messages, etc.

        if SYSTEM_MESSAGE_RE.match(content.strip()):
            continue  # notification boilerplate, not a real message

        if "react" in content.lower() and len(unmatched_reaction_samples) < 5:
            unmatched_reaction_samples.append(content)

        message_counts[sender] += 1
        for raw_word in tokenize(content):
            canonical, was_elongated = normalize_word(raw_word)
            if exclude_stopwords and canonical in STOPWORDS:
                continue
            overall[canonical] += 1
            per_sender[sender][canonical] += 1
            total_words += 1
            if was_elongated:
                elongated_examples[canonical].add(raw_word)

    return {
        "total_words": total_words,
        "message_counts": dict(message_counts),
        "attachment_counts": {
            sender: dict(counter) for sender, counter in attachment_counts.items()
        },
        "reaction_counts": dict(reaction_counts),
        "reaction_emoji_counts": dict(
            Counter(reaction_emoji_counts).most_common(20)
        ),
        "_debug_unmatched_reaction_samples": unmatched_reaction_samples,
        "top_words_overall": overall.most_common(100),
        "top_words_by_sender": {
            sender: counter.most_common(50)
            for sender, counter in per_sender.items()
        },
        "most_stretched_words": sorted(
            (
                {"word": w, "variants": sorted(v, key=len, reverse=True)}
                for w, v in elongated_examples.items()
            ),
            key=lambda x: len(x["variants"][0]),
            reverse=True,
        )[:20],
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def safe_filename(convo_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", convo_id)


def write_output(convo, stats):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_id = safe_filename(convo["id"])
    out_path = DATA_DIR / f"{file_id}.json"
    out_path.write_text(json.dumps({
        "id": convo["id"],
        "title": convo["title"],
        "participants": convo["participants"],
        **{k: v for k, v in stats.items() if not k.startswith("_debug")},
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = []
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest = [m for m in manifest if m["file"] != f"{file_id}.json"]
    manifest.append({
        "file": f"{file_id}.json",
        "title": convo["title"],
        "participants": convo["participants"],
        "message_count": convo["message_count"],
    })
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main():
    start = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path.cwd()
    inbox = find_inbox(start)
    if inbox is None:
        print(f"Couldn't find an `inbox` folder under {start}.")
        print("Point this script at your export root or the inbox folder directly:")
        print("  python3 process_chat.py path/to/your_instagram_activity/messages/inbox")
        sys.exit(1)

    conversations = load_conversations(inbox)
    if not conversations:
        print("No conversations with messages found.")
        sys.exit(1)

    convo = prompt_for_conversation(conversations)
    messages = load_all_messages(convo["path"])
    stats = compute_stats(messages)
    out_path = write_output(convo, stats)

    print(f"\n✓ Wrote stats for '{convo['title']}' -> {out_path}")
    print(f"  {stats['total_words']} words counted across {sum(stats['message_counts'].values())} messages")

    samples = stats.get("_debug_unmatched_reaction_samples")
    if samples:
        print("\n⚠ Found messages mentioning 'react' that weren't recognized as")
        print("  reaction/system notifications -- their words got counted normally.")
        print("  Sample(s), for debugging the regex:")
        for s in samples:
            print(f"    {s!r}")

    print("\nRun the site with: cd site && npm run dev")


if __name__ == "__main__":
    main()