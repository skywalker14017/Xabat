🛡️ Xabat

A Discord bot that makes reporting predators simple and structured, so it actually gets in front of a human instead of getting lost in a DM nobody checks.

If someone is in immediate danger, this bot is not the answer. Contact local emergency services first. Xabat is a triage tool, not a 911 replacement.

Table of Contents

* What is this thing?⁠￼
* What Xabat is (and isn’t)⁠￼
* Features⁠￼
* Commands⁠￼
* Self-hosting⁠￼
* Data retention⁠￼
* License⁠￼
* Privacy & Terms⁠￼
* Good to know⁠￼
* Contributing⁠￼

What is this thing?

Xabat lets people report grooming, sexual abuse, sextortion, child endangerment, rape, and other predatory behavior through a private, guided Discord flow instead of typing it into a public channel or cold-DMing a mod and hoping for the best.

Every report follows the same basic path: submit it, attachments are automatically screened, a real moderator reviews the case, and the report gets resolved. Screening is designed to reduce unnecessary exposure to explicit material, while human moderators remain responsible for reviewing reports and making moderation decisions.

Xabat isn’t law enforcement, a lawyer, or a promise that anything gets prosecuted. It’s the on-ramp: a calmer, safer, more organized way to get a report in front of people who can actually do something with it.

What Xabat is (and isn’t)

It is:

* A guided reporting flow with automatic image screening
* A moderator triage system with an audit trail behind it
* A private channel for the mod team to keep talking to the reporter
* Designed to fail safe: if required safety checks aren’t available, Xabat won’t process reports until they’re restored

It isn’t:

* Law enforcement, a courtroom, or a guaranteed outcome
* A place to intentionally upload explicit images or CSAM (Child Sexual Abuse Material)
* A replacement for emergency services or professional support
* Perfect: automated screening can miss things, age-reference data is only a screening signal, and moderators are still just people

Features

* 🚨 /report commands split by type: grooming, sexual abuse, rape, sextortion, endangerment, or other
* 🕵️ Anonymous or named reporting, reporter’s choice
* 🔍 Automatic image screening on every attachment before moderator review
* ✅ Human triage queue: moderators review and approve or reject each attachment before it becomes case evidence
* 🧵 Dedicated case threads, plus a private conversation thread/DM relay between moderators and the reporter
* 🌍 Jurisdiction-aware screening flags: cross-checks reported ages against a country-by-country age-of-consent reference table, purely to flag cases that need human attention and never as a legal verdict
* 🧹 Automatic cleanup: abandoned upload sessions, rate-limit records, evidence threads, closed cases, and old audit logs expire on their own schedules
* ❤️ /resources: crisis hotlines and support organizations across several countries, sent privately
* 🐛 /system issue: routes bug reports to the dev team, with a built-in reply channel

Commands

Command	Who	Does what
/report grooming / sexual_abuse / rape / sextortion / endangerment / other	Anyone	Starts a report of that type
/resources	Anyone	Privately shows crisis and support hotlines
/system issue	Anyone	Sends a bug report straight to the dev team
/reply <report_id> <message>	Admins	Messages a reporter through the bot (they see “the moderation team,” not an individual name)

Moderators also get button controls right on each report and attachment:

Approve & Move · Delete (Prohibited) · Under Review · Resolved · False Report

Self-hosting

You’ll need

* Python 3.10+
* A Discord bot application and token
* NudeNet for attachment screening

Xabat requires its image-screening layer to be available before accepting reports. If the screening system fails to initialize, the bot stops rather than accepting unprotected evidence uploads.

Environment variables

Variable	Required	What it’s for
BOT_TOKEN	Yes	Your Discord bot token
SECURE_CHANNEL_ID	Yes	Where new reports and attachment triage land
MOD_LOG_CHANNEL_ID	Yes	Status-change audit log channel
MOD_ROLE_ID	Yes	Role allowed to act on reports
GUILD_ID	Optional	Guild to instantly sync slash commands to (skip it for a slower global sync)
ISSUE_CHANNEL_ID	Optional	Where /system issue reports land
FORUM_CHANNEL_ID	Optional	Forum used for per-case discussion posts
REPLIES_CHANNEL_ID	Optional	Forum for moderator-to-reporter threads

Running it

1. Fork this repository to your own GitHub account.
2. Clone your fork locally.
3. Install the dependencies:

cd xabat
pip install -r requirements.txt

4. Configure your environment:

cp .env.example .env

Fill in the required values in .env.

5. Start Xabat:

python bot.py

Originally deployed on Render, with a small built-in Flask endpoint so free-tier health checks don’t spin the bot down.

Data retention

Nothing sensitive sticks around longer than it has to:

Data	Kept for
Incomplete upload sessions	10 minutes idle, or 1 hour max
Rate-limit records	About 24 hours
Evidence threads	About 120 days
Closed cases (Resolved / False Report)	About 180 days
Audit log entries	About 365 days

Full details live in the Privacy Policy⁠￼.

License

Xabat ships under the Xabat Ethical Source License (XESL) v1.1, a custom source-available license loosely inspired by AGPLv3 concepts, but its own thing (not the AGPL, not FSF-affiliated).

Short version:

* Use, study, modify, self-host, and redistribute it freely
* Modified versions remain under XESL and must document their changes
* Publicly hosted modified versions must make their corresponding source available
* The safety mechanisms that protect reporters, moderators, and evidence cannot be intentionally removed or weakened while presenting the result as an Xabat-compliant version
* Using Xabat to facilitate grooming, CSAM, or other abuse it was designed to prevent is prohibited under the license

Full text: LICENSE⁠￼

Privacy & Terms

* 📄 Privacy Policy⁠￼: what’s collected, how long it’s kept, and who can see it
* 📄 Terms of Service⁠￼: acceptable use and moderation actions

Good to know

* Is this instead of calling the police? No. If someone’s in immediate danger, contact local emergency services first.
* Is “anonymous” really anonymous? Your name is hidden from moderators, but your Discord account is still linked internally so the bot can manage your case and reach you. Details are covered by the Privacy Policy.
* What if I upload something explicit by accident? Attachments are automatically screened before moderator review. Material flagged by the screening system is rejected rather than being sent through the normal evidence-review flow.
* What happens with false reports? A moderator can close a report as False Report, which also removes the case’s public discussion post.

Contributing

Built and maintained solo by skywalker14017, with a separate team handling day-to-day report triage.

Contributions are welcome under XESL, especially bug fixes, accessibility improvements, and safety improvements. Anything touching evidence handling or the screening pipeline gets extra scrutiny before it’s merged.

Questions or bugs?

Run /system issue in Discord. It goes to a channel the dev team actually watches, and replies come back to you through the bot.

Prefer to reach out directly? You can contact the maintainer on Discord at skywalker_1401.

⸻

Reporting something awful shouldn’t be complicated. Stay safe out there.
