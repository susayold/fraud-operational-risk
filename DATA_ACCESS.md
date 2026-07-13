# Data Access and Rebuild Modes

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Full rebuild mode

Use the FULL package. It contains the 284,807-row observed PCA input, 250,000-row synthetic controls population, latent audit data and transaction-level outputs. Run `python scripts/run_full_pipeline.py` from the project folder.

## Reviewer quick-check mode

In the FULL package, run `python scripts/10_validate_final_outputs.py`. In the AI_REVIEW_LIGHT package, run `python scripts/validate_review_package.py`. These checks validate the included results, Excel, links, UAT/SIT, negative tests and claim boundaries without retraining.

## AI review mode

The AI_REVIEW_LIGHT package excludes large raw/generated transaction-level files and serialized models. It includes samples under `data/review_samples/`, aggregate outputs, reports, Excel, HTML, code and validation evidence. It is for review, not full retraining.

## GitHub publishing

Publish code, samples, aggregate outputs, HTML, Excel and reports in the repository. Store large full data/output artifacts in a release asset or governed external storage when repository-size policy requires it. Never replace the observed dataset with synthetic data without changing the claim boundary.
