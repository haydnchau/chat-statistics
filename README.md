# wordcount

Ranks the most-used words in an Instagram DM or group chat, entirely
locally. Nothing leaves your machine.

## Setup

```
python3 check_setup.py
```

This checks for Node/npm and, if found, offers to run `npm install`
inside `site/`.

## Usage

1. Download your Instagram data (Settings -> Accounts Center -> Your
   information -> Download your information -> JSON format).
2. Process a chat:

   ```
   python3 process_chat.py /path/to/your_instagram_activity/messages/inbox
   ```

   (You can also point it at the export root, or run it with no
   argument from inside the `inbox` folder itself.) Pick a conversation
   from the numbered list. This writes `site/public/data/<id>.json`
   and updates `site/public/data/manifest.json`.

3. Run the site:

   ```
   cd site
   npm run dev
   ```

   Open the printed localhost URL. Pick a chat in the sidebar to see
   its word ranking, overall or per-person.

Repeat step 2 for as many chats as you want -- each run adds one to
the sidebar without touching the others.

## How it works

- `process_chat.py` merges a conversation's `message_*.json` files,
  fixes Instagram's known UTF-8/Latin-1 mojibake bug, tokenizes each
  message, and counts word frequency overall and per sender.
- **Elongated words** ("soooo", "hiiii") are collapsed by squashing any
  run of 3+ repeated letters down to 2, so stretched variants count
  toward one word instead of scattering across many. This is a
  heuristic, not a dictionary lookup -- a real English wordlist check
  (to also catch cases like `sooo` -> `so`, not just `sooo` -> `soo`)
  is a natural next step.
- The React site (Vite, no backend) reads the generated JSON files as
  static assets and conditionally renders the chat picker vs. the
  stats view.

## Known limitations / next steps

- English-only tokenization for now.
- Stopword list in `process_chat.py` is a rough cut, not exhaustive --
  edit `STOPWORDS` to tune it.
- No stemming/lemmatization yet ("run" and "running" count separately).
- Elongation normalization doesn't yet check against a real dictionary.
