import argparse
import json
from typing import List

from .report import list_runs, run_summary, compare_runs


def _cmd_list(args: argparse.Namespace):
    runs = list_runs(limit=args.limit)
    out = []
    for r in runs:
        env = r.get("env", {})
        git = env.get("git")
        branch = env.get("git_branch")
        dirty = env.get("git_dirty")
        if args.git is not None and git != args.git:
            continue
        if args.git_branch is not None and branch != args.git_branch:
            continue
        if args.dirty and not dirty:
            continue
        if args.clean and dirty:
            continue
        out.append(r)
    for r in out:
        rid = r["run_id"]
        name = r.get("name") or ""
        fw = r.get("framework")
        print(f"{rid}  [{fw}]  {name}")


def _cmd_summary(args: argparse.Namespace):
    s = run_summary(args.run_id)
    print(json.dumps(s, indent=2, sort_keys=True))


def _cmd_compare(args: argparse.Namespace):
    res = compare_runs(args.run_ids)
    print(json.dumps(res, indent=2, sort_keys=True))


def _cmd_serve(args: argparse.Namespace):
    from .server import serve

    serve(host=args.host, port=args.port)


def _cmd_diff_epoch(args: argparse.Namespace):
    from .diff import grad_diff_summary, grad_diff_ranked

    summary = grad_diff_summary(args.run_id, args.epoch_a, args.epoch_b, top_k=args.top_k)
    ranked = grad_diff_ranked(args.run_id, args.epoch_a, args.epoch_b, top_k=args.top_k, by_abs=args.by_abs)
    out = {"summary": summary, "ranked": ranked}
    print(json.dumps(out, indent=2, sort_keys=True))


def _cmd_diff_cross(args: argparse.Namespace):
    from .diff import grad_diff_cross_run

    delta = grad_diff_cross_run(args.run_a, args.run_b, epoch_a=args.epoch_a, epoch_b=args.epoch_b)
    items = sorted(delta.items(), key=lambda x: abs(x[1]), reverse=True)[: args.top_k]
    print(json.dumps(items, indent=2))


def _cmd_export(args: argparse.Namespace):
    from .export import export_run_json

    blob = export_run_json(
        args.run_id,
        path=args.path,
        include_metrics=not args.no_metrics,
        include_alerts=not args.no_alerts,
    )
    if args.path is None:
        print(blob)


def _cmd_diagnose(args: argparse.Namespace):
    from .report import quick_diagnostics

    diag = quick_diagnostics(args.run_id)
    print(json.dumps(diag, indent=2, sort_keys=True))


def _cmd_version(args: argparse.Namespace):
    from . import __version__

    print(f"gradscope {__version__}")


def main(argv: List[str] | None = None):
    parser = argparse.ArgumentParser(prog="gradscope", description="GradScope CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ver = sub.add_parser("version", help="Show version")
    p_ver.set_defaults(func=_cmd_version)

    p_list = sub.add_parser("list", help="List recent runs")
    p_list.add_argument("--limit", type=int, default=20)
    p_list.add_argument("--git", dest="git", help="Filter by git commit hash")
    p_list.add_argument("--git-branch", dest="git_branch", help="Filter by git branch")
    p_list.add_argument("--dirty", action="store_true", help="Only runs with dirty git state")
    p_list.add_argument("--clean", action="store_true", help="Only runs with clean git state")
    p_list.set_defaults(func=_cmd_list)

    p_sum = sub.add_parser("summary", help="Show summary for a run")
    p_sum.add_argument("run_id")
    p_sum.set_defaults(func=_cmd_summary)

    p_cmp = sub.add_parser("compare", help="Compare multiple runs")
    p_cmp.add_argument("run_ids", nargs="+")
    p_cmp.set_defaults(func=_cmd_compare)

    p_srv = sub.add_parser("serve", help="Run web server")
    p_srv.add_argument("--host", default="127.0.0.1")
    p_srv.add_argument("--port", type=int, default=8000)
    p_srv.set_defaults(func=_cmd_serve)

    p_diff = sub.add_parser("diff", help="Gradient diffs")
    diff_sub = p_diff.add_subparsers(dest="mode", required=True)

    p_diff_epoch = diff_sub.add_parser("epoch", help="Diff epochs in a run")
    p_diff_epoch.add_argument("run_id")
    p_diff_epoch.add_argument("epoch_a", type=int)
    p_diff_epoch.add_argument("epoch_b", type=int)
    p_diff_epoch.add_argument("--top-k", type=int, default=10)
    p_diff_epoch.add_argument("--by-abs", action="store_true", default=True)
    p_diff_epoch.set_defaults(func=_cmd_diff_epoch)

    p_diff_cross = diff_sub.add_parser("cross", help="Diff gradients across runs")
    p_diff_cross.add_argument("run_a")
    p_diff_cross.add_argument("run_b")
    p_diff_cross.add_argument("--epoch-a", type=int)
    p_diff_cross.add_argument("--epoch-b", type=int)
    p_diff_cross.add_argument("--top-k", type=int, default=10)
    p_diff_cross.set_defaults(func=_cmd_diff_cross)

    p_exp = sub.add_parser("export", help="Export run to JSON")
    p_exp.add_argument("run_id")
    p_exp.add_argument("--path")
    p_exp.add_argument("--no-metrics", action="store_true")
    p_exp.add_argument("--no-alerts", action="store_true")
    p_exp.set_defaults(func=_cmd_export)

    p_diag = sub.add_parser("diagnose", help="Quick diagnostics for a run")
    p_diag.add_argument("run_id")
    p_diag.set_defaults(func=_cmd_diagnose)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
