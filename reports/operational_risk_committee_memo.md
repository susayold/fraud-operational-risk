# Operational Risk Committee Memo

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Executive decision

The synthetic incident portfolio contains **18 events**, including **12 High/Critical events**, with net loss exposure of **318,200.00 cost units**. The dominant concerns are score-scale failure, rule configuration, vendor dependency, override governance and alert capacity.

## Required actions

1. Enforce release blocking for invalid score scale and missing reason codes.
2. Test rules-only, conservative step-up and queue-outage fallbacks every release.
3. Protect Critical/High alert capacity and escalate backlog before SLA failure.
4. Require dual approval and immutable evidence for high-risk overrides.
5. Close open High/Critical remediation with independent validation evidence.

## Scenario exposure

The largest tail scenario is third-party compromise at **400,000 gross / 320,000 net cost units**. These are educational scenario estimates, not regulatory capital calculations.
