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

* **Python** (version 3.10 or newer) — [download here](https://www.python.org/downloads/). On Windows, make sure you tick "Add Python to PATH" during install.
* **Node.js** (version 18 or newer) — [download here](https://nodejs.org/) (choose the "LTS" version).

You'll also need a **Terminal** (Mac/Linux) or **Command Prompt /
PowerShell** (Windows) — a text-based window where you type commands.
Every command below goes there, one at a time, followed by Enter.

> **New to the terminal?** On Mac, open Spotlight (⌘+Space), type
> "Terminal", press Enter. On Windows, press the Start key, type
> "PowerShell", press Enter.

---

## Step 1: Download ChatStats

Open your Terminal / Command Prompt / PowerShell and run:

```bash
git clone https://github.com/haydnchau/chat-statistics.git
```

This downloads the ChatStats project to your computer.

Then enter the project folder:

```bash
cd chat-statistics
```

Keep this terminal window open — you'll use it for the remaining steps.

> **Don't have Git installed?** You can also download the project directly
> from GitHub as a ZIP and unzip it. Then open your terminal inside the
> extracted `chat-statistics` folder.

---

## Step 2: Download your Instagram data

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

```text
your_instagram_activity/messages/inbox
```

---

## Step 3: Check your setup (and start the site)

First, make sure you're inside the ChatStats project folder:

```bash
cd chat-statistics
```

Then run:

```bash
python3 check_setup.py
```

This checks that Python and Node are installed correctly and offers to
install the website's dependencies for you (just follow whatever it
prints — if it asks a yes/no question, type `y` and press Enter).

Once everything checks out, it'll ask you to paste the path to your
downloaded Instagram export (see Step 2 above) and **remembers it**,
so you won't need to type or paste that path again —
`process_chat.py` will use it automatically from here on. If you don't
have your export downloaded yet, just leave this blank and you can pass
the path manually the first time you run `process_chat.py` instead.

Then it **automatically starts the website and opens it in your
browser for you** — you don't need to run anything else to see it.
It'll be at `http://localhost:5173`.

Leave this terminal window open while you're using the site. To stop
it later, click back into the terminal and press `Ctrl + C`.

---

## Step 4: Process your chats

This step reads your downloaded Instagram data and turns it into stats
the website can display. You can do this before or after Step 3 —
if the site is already open, just refresh the page afterward to see
your data show up.

If you entered your export path in Step 3, you can leave it off the
commands below — it'll be used automatically. Otherwise, add it to the
end of the command, same as before.

**Option A — process everything at once (recommended):**

```bash
python3 process_chat.py --all
```

This processes every conversation you have in one go and sets
everything up, including the Overview page.

**Option B — process one chat at a time:**

```bash
python3 process_chat.py
```

This shows you a numbered list of your conversations and lets you pick
one. Run it again (same command) to add more chats one by one. Handy
if you only care about a couple of specific chats rather than all of
them.

> Either way, if you run this again later with more chats, it just
> adds to what's already there — it won't erase your earlier progress.
> Just refresh the site in your browser afterward to see the update.

---

## Restarting the site later

Closed the terminal or stopped the site? Just run Step 3 again:

```bash
python3 check_setup.py
```

It'll skip straight to opening the site since everything's already
installed.

---

## What you'll see

* **Overview** — your total messages sent, most active
  conversation, reactions given, attachments sent, and your top words
  across *all* processed chats combined.
* **Individual chats** — pick any conversation from the sidebar to see
  its word ranking (overall or broken down by person), most-stretched
  words ("sooooo" → "soo"), attachments sent, and reactions given.

---

## Troubleshooting

* **"command not found: python3"** — Python isn't installed, or isn't
  on your system PATH. Reinstall from the link above and restart your
  terminal.
* **"command not found: git"** — Git isn't installed. You can either
  install Git or download the project as a ZIP from GitHub instead.
* **The website shows "Nothing processed yet"** — you haven't run
  `process_chat.py` yet, or it didn't find your inbox folder. Double
  check the path you gave it in Step 4.
* **The Overview page says it can't detect who you are** — this needs
  at least 2 processed conversations to figure out (it looks for the
  one name that appears in every chat). Process another chat and
  refresh.
* **Something looks broken/blank** — stop the site (`Ctrl + C` in the
  terminal it's running in) and run `python3 check_setup.py` again to
  restart it.

---

## For the technically curious

<details>
<summary>How it works, limitations, and internals</summary>

### How it works

* `process_chat.py` merges a conversation's `message_*.json` files,
  fixes Instagram's known UTF-8/Latin-1 mojibake bug, tokenizes each
  message, and counts word frequency overall and per sender.
* **Elongated words** ("soooo", "hiiii") are collapsed by squashing any
  run of 3+ repeated letters down to 2, so stretched variants count
  toward one word instead of scattering across many. This is a
  heuristic, not a dictionary lookup — a real English wordlist check
  (to also catch cases like `sooo` → `so`, not just `sooo` → `soo`) is a
  natural next step.
* `build_overview.py` (or the automatic rebuild at the end of
  `process_chat.py`) scans every processed chat's JSON and aggregates
  a cross-chat summary into `site/public/data/overview.json`. It
  figures out which participant is "you" by taking the intersection of
  the `participants` list across every chat you've processed — your
  name is the one that shows up in all of them.
* The React site (Vite, no backend) reads the generated JSON files as
  static assets and conditionally renders the chat picker, overview,
  and per-chat stats views.

### Known limitations / next steps

* English-only tokenization for now.
* Stopword list in `process_chat.py` is a rough cut, not exhaustive —
  edit `STOPWORDS` to tune it.
* No stemming/lemmatization yet ("run" and "running" count separately).
* Elongation normalization doesn't yet check against a real dictionary.
* "You" detection in the overview needs at least 2 processed
  conversations with different other participants to work.

</details>
