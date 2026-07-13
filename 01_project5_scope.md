# Project 5 Scope - Fraud Detection, Transaction Risk Controls and Operational Risk Governance

Status: Phase 0 locked for build.
Generated: 2026-07-11 03:35:36

## Executive Objective

Project 5 demonstrates how a Risk function detects suspicious transactions, prioritises alerts, balances fraud loss against customer friction, manages operational incidents and proves that controls work.

The project is not just a model. It is an end-to-end fraud-risk operating framework:

Transaction data -> risk indicators -> observed benchmark models -> deterministic rules -> hybrid decision engine -> alert queue -> investigation outcome -> fraud loss/prevented loss -> incident and control failure -> KRI monitoring -> management action.

## Two-Layer Design

Layer A: Observed PCA Fraud Benchmark.
- Source: Project 0 observed public fraud dataset.
- Current available population: 284,807 transactions, 492 fraud cases, fraud rate 0.1727%.
- Purpose: predictive benchmark, PR-AUC, precision/recall, fraud amount capture, threshold economics, calibration review.
- Boundary: PCA variables cannot support business reason codes such as device-risk or beneficiary-risk rules.

Layer B: Synthetic Controls-Testing Environment.
- Source: documented synthetic generation methodology.
- Purpose: interpretable fraud rules, reason codes, alert operations, incidents, KRIs, UAT/SIT and governance.
- Boundary: synthetic controls testing only, not observed fraud performance.

## Non-Claim

This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

## Phase 0 Build Lock

No model training is allowed before data, label, anti-circularity, threshold economics, probability calibration, friendly-fraud timing and fairness diagnostics are locked.
