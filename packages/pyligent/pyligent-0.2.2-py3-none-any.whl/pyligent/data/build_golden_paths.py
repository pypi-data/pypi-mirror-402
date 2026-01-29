import argparse
import json
import os
import re

from datasets import load_dataset

AFTER_HASHES_RE = re.compile(r"####\s*(.*)")


def split_steps(text: str):
    # 1) normalize line breaks and strip calculator annotations
    text = text.replace("\r", "\n").strip()
    text = re.sub(r"<<.*?>>", "", text, flags=re.DOTALL)

    # 2) split
    parts = re.split("\n", text)
    steps = [p.strip() for p in parts if p and not p.isspace()]

    # 3) drop any standalone answer line and strip inline trailing '#### <num>' if appended
    steps = [s for s in steps if s and not s.startswith("####")]

    return steps


def extract_after_hashes(text: str):
    m = AFTER_HASHES_RE.search(text)
    if not m:
        return None
    return m.group(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_config", type=str, required=True)
    ap.add_argument("--out", type=str, required=True)
    args = ap.parse_args()

    import yaml

    with open(args.data_config) as f:
        data_cfg = yaml.safe_load(f)

    os.makedirs(args.out, exist_ok=True)
    ds_train = load_dataset(
        data_cfg["dataset_name"],
        data_cfg["dataset_config"],
        split=data_cfg["split_train"],
    )
    ds_test = load_dataset(
        data_cfg["dataset_name"],
        data_cfg["dataset_config"],
        split=data_cfg["split_test"],
    )

    def proc_split(ds, fname):
        out = []
        for ex in ds:
            q = ex["question"].strip()
            a = ex["answer"].strip()
            steps = split_steps(a)
            final_answer = extract_after_hashes(a)
            if final_answer is None or len(steps) < 1:
                continue
            out.append(
                {
                    "question": q,
                    "steps": steps,
                    "final_answer": final_answer,
                }
            )
        with open(os.path.join(args.out, fname), "w") as f:
            for r in out:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    proc_split(ds_train, "train_golden.jsonl")
    proc_split(ds_test, "test_golden.jsonl")


if __name__ == "__main__":
    main()
