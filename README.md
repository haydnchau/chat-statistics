# ChatStats

See your most-used words, message counts, and more from your Instagram
DMs and group chats — entirely on your own computer. Nothing is
uploaded anywhere; everything happens locally.

You don't need to know how to code to set this up. Just follow the
steps below in order, copying and pasting the commands exactly as
shown.

---

## Before you start

You need two free programs installed on your computer:

- **Python** (version 3.10 or newer) — [download here](https://www.python.org/downloads/). On Windows, make sure you tick "Add Python to PATH" during install.
- **Node.js** (version 18 or newer) — [download here](https://nodejs.org/) (choose the "LTS" version).

You'll also need a **Terminal** (Mac/Linux) or **Command Prompt /
PowerShell** (Windows) — a text-based window where you type commands.
Every command below goes there, one at a time, followed by Enter.

> **New to the terminal?** On Mac, open Spotlight (⌘+Space), type
> "Terminal", press Enter. On Windows, press the Start key, type
> "PowerShell", press Enter.

---

## Step 1: Download your Instagram data

1. Open Instagram → tap your profile → **Settings** → **Accounts
   Center** → **Your information and permissions** → **Download your
   information**.
2. Choose **Download or transfer information**, select your account,
   and choose **Some of your information**.
3. Scroll down and select only **Messages** (uncheck everything else —
   it's a much smaller, faster download).
4. Set the format to **JSON** (not HTML) and the date range to **All
   time**.
5. Submit the request. Instagram will email you a download link,
   usually within a few minutes to a few hours.
6. Download the `.zip` file it sends you and unzip it somewhere you'll
   remember, like your Desktop or Downloads folder.

Inside, you're looking for a folder path that looks like:
`your_instagram_activity/messages/inbox`

---

## Step 2: Open this project in your terminal

Once you've downloaded/unzipped this project folder, navigate into it.
Replace the path below with wherever you actually put it:

```
cd path/to/chat-stats
```

(Tip: you can usually type `cd ` — with a trailing space — then drag
the folder into the terminal window, and it'll fill in the path for
you.)

---

## Step 3: Check your setup

```
python3 check_setup.py
```

This checks that Python and Node are installed correctly and offers to
install the website's dependencies for you. Just follow whatever it
prints — if it asks a yes/no question, type `y` and press Enter.

---

## Step 4: Process your chats

This step reads your downloaded Instagram data and turns it into stats
the website can display. You have two options:

**Option A — process everything at once (recommended):**

```
python3 process_chat.py --all /path/to/your_instagram_activity/messages/inbox
```

Replace the path with wherever you unzipped your download in Step 1.
This processes every conversation you have in one go and sets
everything up, including the Overview page.

**Option B — process one chat at a time:**

```
python3 process_chat.py /path/to/your_instagram_activity/messages/inbox
```

This shows you a numbered list of your conversations and lets you pick
one. Run it again (same command) to add more chats one by one. Handy
if you only care about a couple of specific chats rather than all of
them.

> Either way, if you run this again later with more chats, it just
> adds to what's already there — it won't erase your earlier progress.

---

## Step 5: Run the website

```
cd site
npm run dev
```

This starts the website on your computer. It'll print a web address
that looks like `http://localhost:5173` — open that in your browser
(Chrome, Safari, etc). You'll see your stats there.

To stop the website later, click back in the terminal window and press
`Ctrl + C`.

---

## What you'll see

- **Overview** — your total messages sent, most active
  conversation, reactions given, attachments sent, and your top words
  across *all* processed chats combined.
- **Individual chats** — pick any conversation from the sidebar to see
  its word ranking (overall or broken down by person), most-stretched
  words ("sooooo" → "soo"), attachments sent, and reactions given.

---

## Troubleshooting

- **"command not found: python3"** — Python isn't installed, or isn't
  on your system PATH. Reinstall from the link above and restart your
  terminal.
- **The website shows "Nothing processed yet"** — you haven't run
  `process_chat.py` yet, or it didn't find your inbox folder. Double
  check the path you gave it in Step 4.
- **The Overview page says it can't detect who you are** — this needs
  at least 2 processed conversations to figure out (it looks for the
  one name that appears in every chat). Process another chat and
  refresh.
- **Something looks broken/blank** — try fully stopping the website
  (`Ctrl + C` in the terminal) and running `npm run dev` again.

---

## For the technically curious

<details>
<summary>How it works, limitations, and internals</summary>

### How it works

- `process_chat.py` merges a conversation's `message_*.json` files,
  fixes Instagram's known UTF-8/Latin-1 mojibake bug, tokenizes each
  message, and counts word frequency overall and per sender.
- **Elongated words** ("soooo", "hiiii") are collapsed by squashing any
  run of 3+ repeated letters down to 2, so stretched variants count
  toward one word instead of scattering across many. This is a
  heuristic, not a dictionary lookup — a real English wordlist check
  (to also catch cases like `sooo` → `so`, not just `sooo` → `soo`)
  is a natural next step.
- `build_overview.py` (or the automatic rebuild at the end of
  `process_chat.py`) scans every processed chat's JSON and aggregates
  a cross-chat summary into `site/public/data/overview.json`. It
  figures out which participant is "you" by taking the intersection of
  the `participants` list across every chat you've processed — your
  name is the one that shows up in all of them.
- The React site (Vite, no backend) reads the generated JSON files as
  static assets and conditionally renders the chat picker, overview,
  and per-chat stats views.

### Known limitations / next steps

- English-only tokenization for now.
- Stopword list in `process_chat.py` is a rough cut, not exhaustive —
  edit `STOPWORDS` to tune it.
- No stemming/lemmatization yet ("run" and "running" count separately).
- Elongation normalization doesn't yet check against a real dictionary.
- "You" detection in the overview needs at least 2 processed
  conversations with different other participants to work.

</details>