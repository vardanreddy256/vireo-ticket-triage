# Submission form: Vireo Audio, Support Tickets (Set E)

**What did you build, and what business outcome does it move? State the number and the money.**

A Python tool (`python run.py`, ~30 s, no API key) that re-categorises every ticket from the agent's closing
note and, where that's blank, a small text model reading the customer's first message. It produces Priya's
monthly charts by category and by team, with team shown three ways: where the bot sent it, who resolved it,
and who should own it. It also prices misrouting.

The finding: by the bot's tags Billing is 21% of tickets and Logistics 16%; re-categorised, Billing is 14% and
Logistics 29%. 45% of what the bot sends to Billing is other teams' work, mainly "I paid but it never arrived".

**Goal: cut delivery complaints landing in Billing from 38% of Billing's intake to under 5% by December 2026,
worth about Rs 58,000 a quarter (Rs 2.3 lakh a year)** in avoided transfers (Rs 305 each) and SLA breach
credits (Rs 350 each). The flow costs Rs 63,400 a quarter today (Q4 2025 – Q2 2026 average: Rs 46,300 of
transfers + Rs 17,100 of credits); hitting 5% removes 91% of it. If Vireo's real volume is ~650 tickets/week
rather than the export's ~184, it is about Rs 2 lakh a quarter. It also changes the hiring decision: don't
hire into Billing; fix routing, re-measure, and if a hire is still needed it is Logistics (672 tickets per
agent over 18 months vs Billing's 406).

**What does one run cost, and what would a month cost at Vireo's volume (roughly 650 tickets a week)? Show the
arithmetic. If you used no paid calls, say so.**

No paid calls. The model is scikit-learn, trained and run locally on every run.

- One run (11,780 tickets: clean, train, score, 5-fold cross-check, charts) takes about 30 s of laptop CPU.
  At ~30 W that is 30 W × 30 s = 0.00025 kWh, about Rs 0.002 of electricity. API cost Rs 0.
- A month at 650/week is 650 × 52 / 12 ≈ 2,817 tickets. Run monthly on the full history, it takes about the
  same 30 s: **Rs 0 in API fees**. Scoring new tickets at intake is milliseconds each.
- If an LLM were later added only for low-confidence tickets (0.16% ≈ 5 a month), that's a few calls a month,
  i.e. rupees, not thousands.
- Building it used my existing Claude subscription (no per-call spend).

**How do you know it works? Sample size, how you checked, error rate, and the kind of case it gets wrong.**

1. **Gold sample: 300 tickets** drawn at random (seed 42) and labelled from the customer message and agent
   note before the tool existed, using written definitions (`gold/LABELLING.md`). The labels were produced with
   Claude and reviewed by me. They are held out of training. **Tool: 0 wrong** on category and on team (95%
   CI 0–1.3%). **The bot's tag today: 57 / 300 (19%) sent to the wrong team, 70 / 300 (23%) wrong category.**
2. **Cross-check on 10,424 tickets** whose agent note names the issue. The message model, never trained on
   the ticket it scores (5-fold), disagreed with the agent on **4 (0.04%)**.
3. **The kind of case it gets wrong:** very short messages with the one key word misspelt ("cnacel order",
   "no poewr on teh orbit mini", "no udpate on my repaair"). It reads them as delivery or connectivity. All 4
   scored below 0.60 confidence; 0.16% of tickets do, and at intake those should go to a person.

Caveat: the export's messages are templated, so live accuracy will be lower. Re-check 50 tickets a month.

**Did you change, narrow, or push back on the client's ask? What, when, and why.**

Yes. All of this came at the start, after reading the email thread and profiling the data, before building.

- **Pushed back on "most volume gets the hires".** Volume by bot tag measures the bot, not the work. Taken
  literally the rule gives the hires to Chat Frontline (26%, the biggest team, and the least loaded per
  agent). So I compared per agent, excluded Tier 2 (policy s.6), and recommended fixing routing before
  hiring, which is Arjun's "fix a process" option.
- **Changed "by team" into three views** (sent / resolved / should own), because `assigned_team` is just the
  bot's tag in another column.
- **Narrowed the money to one flow.** Only delivery complaints sent to Billing carry extra cost; other
  misroutes cost about Rs 0.
- **Corrected the 22%.** It counts 139 tickets from 2024 that fall outside her 18 months (20.8% in window).

**What is wrong with what you are handing us? Be specific: bugs, shortcuts, things you know are off.**

- **Gold labels were made with an LLM** reading the same agent notes the tool learns from. Shared blind spots
  are possible where an agent's note is wrong. Nobody at Vireo has checked them.
- **Too-good accuracy.** 0/300 reflects templated data, not the real world.
- **Volume mismatch.** The export is ~184 tickets/week vs the ~650 quoted; 44 agents for 184 tickets/week can't
  be the whole workload. Rupees are sized on the export; per-agent figures are relative only.
- **Phrase list is hand-written** (`NOTE_PHRASES`). A new issue type gets pushed into the nearest known
  category by the model. The model never predicts "Other" because it never saw it in training.
- **Cancellations mapped to Frontline** is my call; the policy names no owner.
- **Cost method** compares misrouted tickets with correctly routed ones of the same category and channel. It
  doesn't control for month or priority.
- **Transfers exist only from 14 Sep 2025**, so costs use three quarters (Q4 2025 – Q2 2026).
- **No capacity or time-spent data**, so tickets per agent is not workload.
- **Engineering shortcuts:** the model retrains on every run (fine at this size; save it for production),
  there are no unit tests (the evaluation script is the test), and the roster join assumes no gaps between
  roster rows.

**What did you deliberately leave out, and why that rather than something else?**

- **LLM classification per ticket.** The local model already matched the gold sample; an LLM adds a key,
  cost and run-to-run variation. It's the add-on for the 0.16% low-confidence tickets on messier live traffic.
- **A capacity or staffing model** (agent-hours, shrinkage, shifts). The export can't support it. Better to
  say so than build false precision.
- **A dashboard or web app.** One HTML report plus CSVs answers a monthly decision; a small thing that runs.
- **Deep dives outside the headcount question:** goodwill-cap breaches, the replacement flag, CSAT drivers,
  product and lot quality. Some are noted below, but none change where the hires go.

I spent the time instead on the three things that decide the answer: getting the categories right,
checking them, and pricing the one routing error that matters.

**Anything you built or found that nobody asked for?**

- **Logistics is blamed for Billing's queue.** Breaches are reported against the resolving agent, so 250 of
  the 423 breaches in Logistics' standard report were on tickets the bot sent to Billing first.
- **Resolution times are wrong** in any report that mixes systems. Legacy `resolved_at` is UTC: 2,379
  tickets were "resolved before they were opened".
- **Why the bot misroutes.** 73% of delivery complaints that mention paying ("paid", "money debited") go to
  Billing, vs 9% of those that don't.
- **Goodwill over the cap.** 29 of 35 GW-OTHER refunds exceed the Rs 500 policy cap (Rs 59,148 above the cap
  in total). Worth a Team Lead check.
- **Unreliable replacement flag.** It disagrees with agent notes on about 900 tickets (650 notes say a
  replacement went out while the flag says N). Don't use it for replacement costs.
- **A named "Order Cancellation" category.** The bot hides these in "Other" (26% of it).

**What did you use AI for? Which tools and models, where they helped, where they wasted your time, what you
threw away. Link your three-minute screen recording here.**

Claude in the Claude desktop app (Cowork mode, configured model `claude-opus-5-5`) did most of the build from
one prompt: the pasted brief, the data pack and "complete this task". It read the pack, profiled the data,
wrote the Python, labelled the 300-ticket gold sample and drafted the memo and this form. I reviewed and
edited. The tool itself uses no LLM (scikit-learn only).

- **Helped:** fast profiling, spotting the UTC shift, isolating the one costly flow, reading 300 tickets.
- **Wasted time or thrown away:**
  - a whole-note keyword matcher (1,564 notes matched two categories);
  - a "refund + replacement" leakage finding that was really different issues on the same order;
  - a bad-lot theory and a night-shift theory, both no effect;
  - a duplicate rule that would have deleted a real repeat contact;
  - a confidence figure first measured on training data.

  Details: `docs/ai-log.md`.

Recording: **[paste public Google Drive link]**

**Someone picks this up on Monday and you are unreachable. The three things they need to know.**

1. `python run.py` rebuilds everything from the CSVs in `data/` in about 30 s. Every number in the memo is in
   `outputs/headline_numbers.json`; don't hand-edit numbers.
2. Categories come from the agent-note phrase list first (`triage/categorise.py`, `NOTE_PHRASES`), the text
   model second. If Vireo adds an issue type, add its phrases, re-run, and read `outputs/evaluation.md`.
3. The open question is volume. The export is ~184 tickets/week; the brief says ~650. Ask Sameer whether
   the export is complete before quoting rupees; everything scales linearly. The agreed next step is the bot
   routing change, then re-run on October–November tickets before any hiring decision.


