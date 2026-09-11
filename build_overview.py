#!/usr/bin/env python3
"""
python3 build_overview.py

Rebuilds site/public/data/overview.json (total messages sent, most active
conversation, your word ranking across every chat) from all conversations
you've already processed with process_chat.py.

This is a separate one-off step on purpose -- it rescans every already-
processed chat, so there's no point running it after each individual chat.
Process all the conversations you care about first, then run this once
(or again later if you process more).
"""
from process_chat import build_overview


def main():
    overview = build_overview()
    if overview is None:
        print("No processed chats found in site/public/data/.")
        print("Run process_chat.py on at least one conversation first.")
        return

    if overview.get("you"):
        print(
            f"✓ Wrote overview.json -- {overview['chat_count']} chats, "
            f"detected you as '{overview['you']}'"
        )
    else:
        print(f"✓ Wrote overview.json -- {overview['chat_count']} chat(s) so far")
        print("⚠ Couldn't yet tell which participant is you (need at least 2")
        print("  processed conversations to auto-detect). Process another chat")
        print("  and run this again.")


if __name__ == "__main__":
    main()