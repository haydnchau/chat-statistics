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

WORD_RE = re.compile(r"[a-zA-Z']+")


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
    the export root, or somewhere in between."""
    if start.name == "inbox" and start.is_dir():
        return start
    candidates = list(start.rglob("inbox"))
    candidates = [c for c in candidates if c.is_dir() and (c.parent.name == "messages" or True)]
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


def tokenize(text: str):
    return [w.lower() for w in WORD_RE.findall(text)]


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def compute_stats(messages, exclude_stopwords=True):
    overall = Counter()
    per_sender = defaultdict(Counter)
    elongated_examples = defaultdict(set)  # canonical -> raw variants seen
    message_counts = Counter()
    total_words = 0

    for msg in messages:
        sender = msg.get("sender_name", "Unknown")
        content = msg.get("content")
        if not content:
            continue  # reactions, shares, unsent messages, etc.
        message_counts[sender] += 1
        for raw_word in tokenize(content):
            canonical, was_elongated = normalize_word(raw_word)
            if exclude_stopwords and canonical in STOPWORDS:
                continue
            if len(canonical) < 2:
                continue
            overall[canonical] += 1
            per_sender[sender][canonical] += 1
            total_words += 1
            if was_elongated:
                elongated_examples[canonical].add(raw_word)

    return {
        "total_words": total_words,
        "message_counts": dict(message_counts),
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
        **stats,
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
    print("\nRun the site with: cd site && npm run dev")


if __name__ == "__main__":
    main()
