# Vireo Audio — support ticket triage

Re-categorises every Vireo support ticket from what the customer actually wrote, then shows monthly volume
**by category** and **by team** — three ways: where the chat bot sent the ticket, who resolved it, and who
should own it. It also prices the cost of tickets landing in the wrong queue.

No paid API calls and no API key. One run takes about 30 seconds on a laptop.

**Headline result (Jan 2025 – Jun 2026, 11,641 tickets):** by the bot's tags Billing looks like the biggest
specialist queue (21% of tickets vs Logistics 16%). Re-categorised, **Billing owns 14% and Logistics 29%**.
45% of what the bot sends to Billing is other teams' work, mostly "I paid but my order hasn't arrived".
Those delivery complaints breach the first-response SLA 37% of the time (vs 9% when they go straight to
Logistics) and cost about **Rs 63,000 a quarter** in extra transfers and SLA credits.
The memo to Priya is in [`docs/memo-to-priya.md`](docs/memo-to-priya.md).

---

## Run it (clean machine, about 5 minutes)

You need **Python 3.10 or newer**. Check with `python3 --version` (Windows: `py --version`).
If you don't have it, install it from https://www.python.org/downloads/ (on Windows, tick
"Add python.exe to PATH" during install).

**1. Get the code**

```bash
git clone <this-repo-url> vireo-ticket-triage
cd vireo-ticket-triage
```

(Or download the ZIP from GitHub, unzip it, and open a terminal in that folder.)

**2. Put the Vireo data pack in the `data/` folder**

Copy these files from the pack into `data/` (they are not in the repo because they contain customer data):

```
data/tickets.csv   data/agents.csv   data/products.csv      (required: tickets, agents; products is used for one check)
data/orders.csv    data/customers.csv                        (optional, not used)
```

**3. Create a private Python environment and install four libraries**

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

(A "venv" is just a folder holding this project's own copy of Python libraries, so nothing on your
machine is changed. If PowerShell refuses to run the activate script, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again.)

**4. Run**

```bash
python run.py
```

You should see four numbered steps and a summary ending in `Done in ~30s. Open outputs/report.html`.
Open `outputs/report.html` in any browser.

Options: `python run.py --data path/to/pack --out path/to/results`.

---

## What you get (in `outputs/`)

| File | What it is |
|---|---|
| `report.html` | One-page report: headline numbers, the three charts, tables behind every chart, accuracy, data fixes |
| `chart_team_share.png` | Each team's share of tickets: bot tag vs re-categorised |
| `chart_monthly_by_team.png` | Monthly tickets per team: where the bot sent them vs who should own them |
| `chart_monthly_by_category.png` | Monthly tickets per category: bot tag vs re-categorised |
| `monthly_by_*.csv`, `team_views.csv` | The numbers behind the charts (open in Excel) |
| `tickets_categorised.csv` | One row per ticket: bot tag, new category, how it was decided, teams, SLA, transfers (no customer text) |
| `headline_numbers.json` | Every number quoted in the memo, straight from the run |
| `evaluation.md` | Accuracy against the hand-checked sample, plus every mistake found |
| `data_quality.md` | Every data fix applied, with counts |

## How it works (plain English)

1. **Clean the export** (`triage/clean.py`). Fixes found in the data, each explained in
   [`docs/decisions.md`](docs/decisions.md): legacy resolution times were stored in UTC (2,379 tickets
   appeared to be resolved before they were opened); 139 tickets from 2024 fall outside the window;
   blank `transfers` means "unknown", not zero; two agents share a name, so everything joins on `agent_id`;
   blank CSAT means no response.
2. **Categorise** (`triage/categorise.py`), two signals:
   - **The agent's closing note.** Agents write what the problem really was ("issue: shipment not received").
     A short phrase list turns that into a category. Covers 89.5% of tickets.
   - **The customer's first message.** A small text classifier (TF-IDF + logistic regression, scikit-learn)
     learns from the tickets whose notes were clear, then reads only the customer's first message. That's
     what makes it usable *at intake*, before an agent touches the ticket, which is the fix we recommend.
   - Final category = the note when it's clear, otherwise the message model.
3. **Map category → owning team** using Vireo's own policy (section 6): delivery → Logistics, payments/invoices
   → Billing, returns/refunds → Returns Desk, warranty/repairs → Escalations & Warranty, everything else →
   the Frontline team for that channel (social is worked by Chat Frontline).
4. **Price the misrouting** (`triage/metrics.py`). For each wrongly routed ticket, extra transfers
   (Rs 305 each) and extra SLA breaches (Rs 350 credit each) compared with correctly routed tickets of the
   same category, using Q4 2025 – Q2 2026 (the quarters where transfers were recorded).
5. **Report** (`triage/report.py`) and **score** (`triage/evaluate.py`).

## How good is it?

| Check | Result |
|---|---|
| Hand-checked random sample, 300 tickets (held out of training) | Tool: **0 wrong** (95% CI 0–1.3%). Bot tag today: 57 sent to the wrong team (19%) |
| Message model vs the agent's own note, 5-fold, 10,424 tickets | 4 disagreements (0.04%) |
| Kind of case it gets wrong | Very short messages with the key word misspelt ("cnacel order", "no poewr"). All 4 scored < 0.60 confidence; 0.16% of tickets do, and should go to a person |

Caveats: the gold labels were made with LLM help and reviewed by hand (see [`gold/LABELLING.md`](gold/LABELLING.md));
the export's messages are very regular, so expect lower accuracy on live traffic. Details in `outputs/evaluation.md`.

## Repo map

```
run.py                  one command: clean -> categorise -> score -> report
triage/clean.py         loading + every data fix
triage/categorise.py    agent-note rules + message model + category->team map
triage/metrics.py       volumes, misrouting cost, the goal
triage/evaluate.py      gold-sample scoring + 5-fold cross-check
triage/report.py        charts, CSVs, report.html
gold/                   300 hand-checked labels + how they were made
docs/                   memo to Priya, decisions log, AI/prompt log, recording script
submission-form.md      the completed submission form
```

Known issues and what was deliberately left out: [`submission-form.md`](submission-form.md) and
[`docs/decisions.md`](docs/decisions.md).
