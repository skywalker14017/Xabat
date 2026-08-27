# 🛡️ Xabat

*A Discord bot that makes reporting predators simple and structured, so it actually gets in front of a human instead of being lost in a DM.*

![License: XESL v1.1](https://img.shields.io/badge/license-XESL_v1.1-bd93f9)
![Python](https://img.shields.io/badge/python-3.10%2B-8be9fd)
![discord.py](https://img.shields.io/badge/discord.py-2.x-ff79c6)
![Status](https://img.shields.io/badge/status-active-46e3b7)

[![Invite Xabat](https://img.shields.io/badge/Invite%20Xabat-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/oauth2/authorize?client_id=1534190800462807153&permissions=395673988176&integration_type=0&scope=bot)

> **If someone is in immediate danger, this bot is not the answer.** Contact local emergency services first. Xabat is a triage tool, not a 911 replacement.

## Table of Contents
- [What is this thing?](#what-is-this-thing)
- [What Xabat is (and isn't)](#what-xabat-is-and-isnt)
- [Features](#features)
- [Commands](#commands)
- [Self-hosting](#self-hosting)
- [Data retention](#data-retention)
- [License](#license)
- [Privacy & Terms](#privacy--terms)
- [Good to know](#good-to-know)
- [Contributing](#contributing)

## What is this thing?

Xabat lets people report grooming, sexual abuse, sextortion, child endangerment, rape, and other predatory behavior through a private, guided Discord flow instead of typing it into a public channel or cold-DMing a mod and hoping for the best.

Every report follows the same basic path: submit it, any evidence gets automatically screened, a real moderator reviews it, and the case gets resolved. Nothing explicit reaches a moderator unfiltered, nothing sits around forever, and the reporter decides how much of their identity is attached to it.

Xabat isn't law enforcement, a lawyer, or a promise that anything gets prosecuted. It's the on-ramp: a calmer, safer, more organized way to get a report in front of people who can actually do something with it.

## What Xabat is (and isn't)

**It is:**
- A guided reporting flow with attachment screening built into the safety architecture
- A moderator triage system with an audit trail behind it
- A private channel for the mod team to keep talking to the reporter
- Built to fail safe: if the screening layer can't initialize, Xabat doesn't run unprotected

**It isn't:**
- Law enforcement, a courtroom, or a guaranteed outcome
- A place to upload explicit images or CSAM (Child Sexual Abuse Material): screenshots are screened before they reach a human, and anything flagged is rejected
- Perfect: the screening layer can miss things, the age-reference data is a screening signal and not a legal ruling, and moderators are still just people

## Features

- 🚨 **`/report`** commands split by type: grooming, sexual abuse, rape, sextortion, endangerment, or other
- 🕵️ **Anonymous or named reporting**, reporter's choice
- 🔍 **Automatic image screening** on every attachment, before it ever reaches a moderator
- ✅ **Human triage queue**: mods approve or reject each image individually before it becomes case evidence
- 🧵 **Dedicated case threads**, plus a private conversation thread/DM relay between mods and the reporter
- 🌍 **Jurisdiction-aware screening flags**: cross-checks reported ages against a large country-by-country age-of-consent reference table, used purely to flag "a human needs to look at this," never as a legal verdict
- 🧹 **Automatic cleanup**: abandoned upload sessions, rate-limit records, evidence threads, closed cases, and old audit logs all expire on their own schedule
- ❤️ **`/resources`**: crisis hotlines and support orgs across several countries, sent privately
- 🐛 **`/system issue`**: routes bug reports to the dev team, with a built-in reply channel

## Commands

| Command | Who | Does what |
|---|---|---|
| `/report grooming` / `sexual_abuse` / `rape` / `sextortion` / `endangerment` / `other` | Anyone | Starts a report of that type |
| `/resources` | Anyone | Privately shows crisis and support hotlines |
| `/system issue` | Anyone | Sends a bug report straight to the dev team |
| `/reply <report_id> <message>` | Admins | Messages a reporter through the bot (they see "the moderation team," not an individual name) |

Moderators also get button controls right on each report and image: **Approve & Move**, **Delete (Prohibited)**, **Under Review**, **Resolved**, **False Report**.

## Self-hosting

### You'll need
- Python 3.10+
- A Discord bot application and token
- The image-screening dependency (`pip install nudenet`): Xabat's safety architecture depends on it, and the bot will not start if it cannot be loaded

### Environment variables

| Variable | Required | What it's for |
|---|---|---|
| `BOT_TOKEN` | Yes | Your Discord bot token |
| `SECURE_CHANNEL_ID` | Yes | Where new reports and image triage land |
| `MOD_LOG_CHANNEL_ID` | Yes | Status-change audit log channel |
| `MOD_ROLE_ID` | Yes | Role allowed to act on reports |
| `GUILD_ID` | Optional | Guild to instantly sync slash commands to (skip it for a slower global sync) |
| `ISSUE_CHANNEL_ID` | Optional | Where `/system issue` reports land |
| `FORUM_CHANNEL_ID` | Optional | Forum used for per-case discussion posts |
| `REPLIES_CHANNEL_ID` | Optional | Forum for mod-to-reporter threads (auto-locked to admins only) |

### Running it

1. Fork the repository on GitHub.
2. Clone your fork locally.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install nudenet
   ```
4. Copy `.env.example` to `.env` and fill in your values.
5. Run the bot:
   ```bash
   python bot.py
   ```

Originally deployed on **Render**, with a small built-in Flask endpoint so free-tier health checks don't spin the bot down.

## Data retention

Nothing sensitive sticks around longer than it has to:

| Data | Kept for |
|---|---|
| Incomplete upload sessions | 10 minutes idle, or 1 hour max |
| Rate-limit records | About 24 hours |
| Evidence threads | About 120 days |
| Closed cases (Resolved / False Report) | About 180 days |
| Audit log entries | About 365 days |

Full details live in the [Privacy Policy](./legal/privacy.html).

## License

Xabat ships under the **Xabat Ethical Source License (XESL) v1.1**, a custom source-available license loosely inspired by AGPLv3 concepts, but its own thing (not the AGPL, not FSF-affiliated).

Short version:
- Use, study, modify, self-host, and redistribute it freely
- Distribute a modified version? It stays under XESL, and you say what you changed
- Publicly host a modified version? Your users get access to that version's source
- The safety mechanisms (image screening, retention limits, access controls) are part of the license: stripping or weakening them is not what XESL is for
- Using Xabat to facilitate grooming, CSAM, or anything it exists to stop falls outside what the license permits

If the image-screening layer can't load, Xabat won't run unprotected. That's a design choice, not a footnote.

Full text: [`LICENSE`](./LICENSE)

## Privacy & Terms

- 📄 [Privacy Policy](./legal/privacy.html): what's collected, how long it's kept, who can see it
- 📄 [Terms of Service](./legal/tos.html): acceptable use, what Xabat is and isn't, moderation actions

## Good to know

- **Is this instead of calling the police?** No. If someone's in immediate danger, contact local emergency services first.
- **Is "anonymous" really anonymous?** Your name is hidden from moderators, but your Discord account is still linked internally so the bot can manage your case and reach you. Details in the Privacy Policy.
- **What if I upload something explicit by accident?** It gets screened and rejected before any moderator sees it.
- **What happens with false reports?** A moderator can close it as False Report, which also removes the case's public discussion post.

## Contributing

Built and maintained solo by **skywalker14017**, with a separate team handling day-to-day report triage. Contributions are welcome under XESL, especially bug fixes, accessibility, and safety improvements, though anything touching evidence handling or the screening pipeline gets extra scrutiny before it's merged.

## Questions or bugs?

Run `/system issue` in Discord. It goes to a channel the dev team actually watches, and replies come back to you through the bot.

Prefer to reach out directly? You can contact the maintainer on Discord at `skywalker_1401`.

---

*Reporting something awful shouldn't be complicated. Stay safe out there.*
