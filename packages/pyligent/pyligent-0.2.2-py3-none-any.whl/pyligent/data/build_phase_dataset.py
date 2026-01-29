import argparse
import json


def to_path_examples(rec, t):
    # rec = {"question": str, "steps": [str], "final_answer": int}
    # ft learns to finish in exactly t steps
    steps = rec["steps"]
    # ensure enough steps in the gold chain
    if len(steps) + 1 < t:
        return []
    # build prefix so that remaining steps == t
    prefix_len = len(steps) - t + 1
    context_nodes = []
    nid = 0
    # root node 0 is the question
    context_nodes.append(f"<node> {nid} {rec['question']} </node>")
    nid += 1
    for s in steps[:prefix_len]:
        context_nodes.append(f"<node> {nid} {s} </node>")
        nid += 1
    # target next action: if t == 1, next is <done>, else it's the next <node>
    # we create a target response for SFT
    targets = []
    if t == 1:
        solution_text = f"Final answer: {rec['final_answer']}"
        targets.append(f"<done> {solution_text} </done>")
    else:
        next_step = steps[prefix_len]
        targets.append(f"<node> {nid} {next_step} </node>")
    return [{"context": " ".join(context_nodes), "target": y} for y in targets]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden_jsonl", required=True)
    ap.add_argument("--t", type=int, required=True)
    ap.add_argument("--out_jsonl", required=True)
    args = ap.parse_args()
    out = []
    with open(args.golden_jsonl) as f:
        for line in f:
            rec = json.loads(line)
            out.extend(to_path_examples(rec, args.t))
    with open(args.out_jsonl, "w") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
