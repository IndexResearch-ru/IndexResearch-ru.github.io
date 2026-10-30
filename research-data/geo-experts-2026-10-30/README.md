# GEO specialists: raw 110-answer snapshot for the BMR study, 30 October 2026

**Observed:** 110 valid responses from 11 AI interfaces × 10 prompts; 74 recognized people; no interface excluded. The current publication being prepared is the **BMR study of mention frequency**, not an expert quality ranking.

Primary data:

- [All 110 answer texts](observations.jsonl), with source answer IDs and actual query strings.
- [Exact prompt matrix](prompts.json), including the unequal «в России» wording between some interfaces.
- [Dictionary of 74 people and recognition patterns](entity_dictionary.csv).
- [Origin, timing and funding disclosure](DATA_PROVENANCE.md).
- [Privacy redactions](contact_redactions.csv): seven email addresses and one phone number.
- [Dataset manifest](manifest.json).
- [Executable calculation](reproduce.py), Python 3.10+, standard library.

The original dataset was also coded for a possible **separate first-recommendation metric (FRS)**; the [original annotation file](first_recommendation_labels.csv) and [provisional protocol](LABELING_PROTOCOL.md) are retained for transparency, but their independent review is pending. **No second FRS research article or rating is published by this BMR-only branch.** Both metrics refer to the same 110 observed answers, not independent empirical samples.

Run from the repository root:

```bash
python3 research-data/geo-experts-2026-10-30/reproduce.py
```

The BMR research article, including the complete 74-person ranking, is staged in [research/geo-experts-bmr-russia-2026/](../../research/geo-experts-bmr-russia-2026/). It is a **draft**, subject to conflict review and an explicit publication decision. IndexResearch is related to study participant Alexey Yakovlev through its co-founder, and GAEO funded the measurements. Mention frequency does not establish service quality or endorsement.
