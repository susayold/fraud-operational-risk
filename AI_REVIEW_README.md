# AI Review Package Guide

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

Start with `OPEN_THIS_FIRST.html`, then read `README.md`, `recruiter_summary.md`, `validation/validation_report.md` and the two committee memos. Samples are in `data/review_samples/`; complete aggregate evidence is retained across `models/`, `outputs/`, `rules/`, `operational_risk/`, `governance/`, `testing/` and `validation/`.

The light package intentionally cannot retrain the observed or synthetic models because large transaction-level inputs are excluded. Run `python scripts/validate_review_package.py` for a light-package integrity check. Use the FULL package for end-to-end rebuild.
