# Split manifests (proposed default)

These files contain split assignments and audit metadata, not model-ready features. `topic_primary` is an automatically generated **weak label**, not gold truth.

- `train_manifest.csv`: `publish_date` < 2025-01-01
- `validation_manifest.csv`: calendar year 2025
- `test_manifest.csv`: 2026-01-01 onward
- `split_manifest.csv`: all records with split assignment

`article_id` is included only as a row key for audit/rejoining; exclude it and the target label from model features. Review `../reports/near_duplicate_title_candidates.csv`, especially `cross_split=True`, and the duplicate-cluster warnings in `../reports/split_validation.md` before final evaluation. Re-run the audit script after changing the source data or split policy. No model training was performed.
