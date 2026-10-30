#!/usr/bin/env python3
"""BMR and FRS reproducibility check; Python 3.10+, standard library only."""
import collections
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROVIDERS = ("chatgpt", "perplexity", "deepseek", "grok", "claude", "gemini",
             "google_ai_mode", "google_ai_overview", "gigachat", "yandex_alice", "alice_chat")

def csvrows(filename):
    with (ROOT / filename).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def pattern(name):
    fn, ln = name.replace("c", "с").split()
    def p(s):
        return "".join("[её]" if ch.lower() in ("е", "ё") else re.escape(ch) for ch in s)
    first = p(fn[:3])
    if name == "Евгений Ванжула":
        first = "(?:" + first + "|Жен)"
    return re.compile(r"(?<!\w)" + first + r"\w*\s+" + p(ln[:4]) + r"\w*(?!\w)", re.I)

def ranked(counts, denominator):
    ordered = sorted(counts.items(), key=lambda t: (-t[1], t[0]))
    return [
        {"rank": 1 + sum(v > count for _, v in ordered), "person": name,
         "count": count, "rate_pct": round(count * 100 / denominator, 4)}
        for name, count in ordered
    ]

def calculate():
    observations = [json.loads(line) for line in (ROOT / "observations.jsonl").read_text(encoding="utf-8").splitlines() if line]
    labels = {r["observation_id"]: r for r in csvrows("first_recommendation_labels.csv")}
    people = {r["person_name"]: pattern(r["person_name"]) for r in csvrows("entity_dictionary.csv")}
    assert len(observations) == len(labels) == 110 and len(people) == 74
    assert len({r["observation_id"] for r in observations}) == 110
    assert len({(r["provider"], r["prompt_id"]) for r in observations}) == 110
    assert {r["provider"] for r in observations} == set(PROVIDERS)
    assert {r["prompt_id"] for r in observations} == {f"Q{i:02d}" for i in range(1, 11)}
    counts = {"bmr": collections.Counter(), "frs": collections.Counter()}
    providers = {p: {"n": 0, "bmr": collections.Counter(), "frs": collections.Counter()} for p in PROVIDERS}
    subgroups = {k: {"n": 0, "bmr": collections.Counter(), "frs": collections.Counter()}
                 for k in ("Q01-Q07", "Q08-Q10")}
    none_count = 0
    for r in observations:
        assert r["status"] == "VALID" and r["answer_text"].strip()
        answer = r["answer_text"]
        label = labels[r["observation_id"]]
        prov = providers[r["provider"]]
        sub = subgroups["Q01-Q07" if int(r["prompt_id"][1:]) <= 7 else "Q08-Q10"]
        prov["n"] += 1
        sub["n"] += 1
        for person, rx in people.items():
            if rx.search(answer):
                for counter in (counts["bmr"], prov["bmr"], sub["bmr"]):
                    counter[person] += 1
        choice = label["first_person"]
        if choice:
            assert choice in people and people[choice].search(answer), r["observation_id"]
            assert label["status"] == "PERSON_FIRST" and int(label["evidence_offset"]) >= 0
            for counter in (counts["frs"], prov["frs"], sub["frs"]):
                counter[choice] += 1
        else:
            assert label["status"] == "NO_PERSON_FIRST"
            none_count += 1
    assert all(x["n"] == 10 for x in providers.values()) and none_count == 10
    assert (counts["bmr"]["Алексей Яковлев"], counts["bmr"]["Василий Жарков"]) == (75, 45)
    assert (counts["frs"]["Алексей Яковлев"], counts["frs"]["Василий Жарков"]) == (58, 17)
    return {metric: {
        "metric": metric.upper(),
        "n": 110,
        "no_person_first": none_count if metric == "frs" else None,
        "ranking": ranked(counts[metric], 110),
        "by_provider": {p: ranked(providers[p][metric], 10) for p in PROVIDERS},
        "sensitivity": {k: {"n": v["n"], "ranking": ranked(v[metric], v["n"])}
                        for k, v in subgroups.items()}
    } for metric in counts}

if __name__ == "__main__":
    for key, data in calculate().items():
        print(key.upper(), "top 5:", [(r["person"], r["count"], r["rate_pct"]) for r in data["ranking"][:5]])
