"""Vireo ticket triage - one command.

    python run.py                      # reads ./data, writes ./outputs
    python run.py --data path/to/pack --out somewhere
"""
import argparse
import time
from pathlib import Path

from triage.categorise import categorise
from triage.clean import load
from triage.evaluate import cross_check, evaluate, load_gold
from triage.metrics import headline
from triage.report import write_all


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="data", help="folder with tickets.csv and agents.csv")
    ap.add_argument("--out", default="outputs", help="folder for the report, charts and CSVs")
    ap.add_argument("--gold", default="gold/gold_labels.csv", help="hand-checked labels used for scoring")
    args = ap.parse_args()
    start = time.time()

    print("1/4 Loading and cleaning ...")
    tickets, _agents, notes = load(args.data)
    for n in notes:
        print("    -", n)

    print("2/4 Categorising (agent notes + text model on the customer's first message) ...")
    gold = load_gold(args.gold)
    tickets, info = categorise(tickets, holdout_ids=gold["ticket_id"])
    print(f"    notes named the issue on {info['notes_coverage']:.1%} of tickets; "
          f"model trained on {info['trained_on']:,} of them")

    print("3/4 Scoring against the gold sample ...")
    eval_md, eval_res = evaluate(tickets, gold)
    for r in eval_res.itertuples():
        print(f"    {r.method:<48} wrong team {r.team_errors:>3}/{r.tickets} ({r.team_error_rate:.1%})")
    cc_md, cc = cross_check(tickets)
    eval_md += "\n" + cc_md
    print(f"    cross-check vs agent notes (5-fold): {cc['disagree']} of {cc['checked']:,} disagree; "
          f"{cc['low_confidence']} low-confidence (<0.60)")

    print("4/4 Numbers, charts and report ...")
    h = headline(tickets)
    out = Path(args.out)
    write_all(tickets, h, notes, eval_md, eval_res, info, out)

    fc = h["flow_compare"]
    print()
    print(f"  Share of tickets   bot tag: Billing {h['bot_share']['Billing']:.1%}, Logistics {h['bot_share']['Logistics']:.1%}")
    print(f"                     re-categorised: Billing {h['owner_share']['Billing']:.1%}, "
          f"Logistics {h['owner_share']['Logistics']:.1%}")
    print(f"  Billing's queue that isn't Billing's: {h['billing_inbound_not_billing']:,} of {h['billing_inbound']:,} "
          f"({h['billing_inbound_not_billing'] / h['billing_inbound']:.0%}); delivery complaints {h['billing_inbound_delivery']:,}")
    print(f"  Delivery complaints sent to Billing vs straight to Logistics: breach "
          f"{fc['routed_to_billing']['sla_breach_rate']:.0%} vs {fc['routed_to_logistics']['sla_breach_rate']:.0%}, "
          f"median resolution {fc['routed_to_billing']['median_resolution_hours']:.0f}h vs "
          f"{fc['routed_to_logistics']['median_resolution_hours']:.0f}h, CSAT "
          f"{fc['routed_to_billing']['avg_csat']:.2f} vs {fc['routed_to_logistics']['avg_csat']:.2f}")
    print(f"  Cost of that misrouting: Rs {h['flow_cost_per_quarter']:,} a quarter "
          f"(transfers Rs {h['flow_cost_transfers_per_quarter']:,} + SLA credits Rs {h['flow_cost_credits_per_quarter']:,})")
    print(f"  Goal: delivery complaints from {h['goal_now_share_of_billing_intake']:.0%} of Billing's intake to under "
          f"{h['goal_target_share']:.0%} -> saves about Rs {h['goal_saving_per_quarter']:,} a quarter "
          f"(Rs {h['goal_saving_per_quarter_at_650_week']:,} if volume is ~650/week)")
    print(f"\nDone in {time.time() - start:.0f}s. Open {out / 'report.html'}")


if __name__ == "__main__":
    main()
