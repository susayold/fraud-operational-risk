# Rollback and Fallback Plan

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Trigger and response

| Trigger | Immediate mode | Recovery evidence |
| --- | --- | --- |
| Model unavailable | Rules-only mode | Model health restored and SIT rerun |
| Rules engine unavailable | Model plus conservative step-up | Rule package checksum and regression PASS |
| Device vendor unavailable | Conservative step-up | Vendor feed freshness restored |
| Alert queue unavailable | Hold critical; allow low risk with logging | Queue replay reconciled |
| Score scale invalid | Release block | 0-1 boundary test and proposed independent-review evidence |

Rollback requires preserved pre-change artifact, versioned configuration, simulated owner approval, affected-decision reconciliation and post-rollback monitoring. This portfolio package does not claim actual organisational approval.
