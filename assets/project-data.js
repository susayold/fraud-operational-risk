window.PORTFOLIO_PROJECTS = {
  "5": {
    number: "05",
    status: "Completed | Controls and validation passed",
    statusClass: "complete",
    accent: "#b43c35",
    category: "Fraud Analytics & Operational Risk",
    title: "Fraud Detection, Controls & Operational Risk",
    thesis: "A two-layer fraud risk project that combines an observed imbalanced-class benchmark with a separately labeled synthetic controls environment, then connects detection to threshold economics, queue capacity, incidents and governance.",
    tags: ["Fraud analytics", "Imbalanced classification", "PR-AUC", "Calibration", "Threshold economics", "Rules", "Alert operations", "Operational risk"],
    metrics: [
      { value: "284,807", label: "Observed transactions" },
      { value: "0.7786", label: "Champion test PR-AUC" },
      { value: "84.93%", label: "Test fraud recall" },
      { value: "69.36%", label: "Test fraud-amount recall" },
      { value: "228/228", label: "Validation checks passed" }
    ],
    business: {
      question: "How should Risk combine predictive ranking, deterministic controls and operational capacity to reduce fraud loss without unacceptable customer friction or unmanaged alert backlogs?",
      context: "Fraud performance cannot be judged by ROC-AUC alone. Very low prevalence, amount capture, false positives, review capacity, incident ownership and residual risk determine whether a control is useful.",
      output: "Observed model benchmark, locked threshold economics, interpretable synthetic rules, hybrid routing, alert operations, incident/RCA packs, KRIs, testing and a 14-sheet management workbook."
    },
    dataLayers: [
      { meta: "Layer A - Observed", title: "PCA fraud benchmark", text: "284,807 transactions and 492 fraud cases support model ranking, calibration, amount capture and historical threshold economics." },
      { meta: "Layer B - Synthetic", title: "Controls-testing environment", text: "250,000 transactions with six hidden fraud archetypes support interpretable rules, reason codes, routing and operational workflows." },
      { meta: "Separate label", title: "Friendly-fraud disputes", text: "15,000 post-transaction claims remain distinct from transaction-fraud labels and are not folded into model performance." },
      { meta: "Operations", title: "Queues, capacity and incidents", text: "Alert priority, investigation outcomes, SLA/backlog sensitivity, 18 incidents, 10 scenarios, RCA and owner/action controls." }
    ],
    formulas: [
      { name: "Precision", expression: "Precision = True Fraud Alerts / All Alerts", meaning: "Measures investigator yield and customer-friction efficiency.", use: "Threshold and queue design." },
      { name: "Fraud recall", expression: "Recall = Captured Fraud / Total Fraud", meaning: "Measures the share of fraud cases detected.", use: "Core risk-appetite outcome." },
      { name: "Amount recall", expression: "Amount Recall = Captured Fraud Amount / Total Fraud Amount", meaning: "Weights detection by monetary materiality.", use: "Prevents a high-count, low-value strategy from looking complete." },
      { name: "Net benefit", expression: "Net Benefit = Prevented Loss - Investigation Cost - False-positive Friction Cost", meaning: "Translates threshold performance into a decision-economic view.", use: "Validation-only threshold selection." },
      { name: "Capacity utilization", expression: "Utilization = Alerts per period / Review capacity per period", meaning: "Tests whether a policy creates operational backlog.", use: "Release and stress-capacity control." }
    ],
    process: [
      { title: "Lock observed and synthetic boundaries", text: "Define allowed claims, label roles, data contracts and anti-circularity controls before model development.", evidence: "Observed and synthetic data boundaries documented" },
      { title: "Profile extreme class imbalance", text: "Measure prevalence, amount distribution, period stability and feature separation on observed data.", evidence: "492 fraud cases; 0.1727% rate" },
      { title: "Select champion on validation only", text: "Compare logistic, weighted logistic, tree, sampling and anomaly challengers using PR-AUC, capture and workload.", evidence: "Class-weighted logistic champion" },
      { title: "Lock economic alert threshold", text: "Choose the 0.50% validation alert-rate candidate using capacity, net benefit, recall, precision and amount-capture hierarchy.", evidence: "Untouched test alert rate 0.40%" },
      { title: "Build interpretable controls", text: "Generate synthetic observable features, 15 governed rules, reason codes, priorities, fallbacks and override policy.", evidence: "Rules do not recreate the hidden label" },
      { title: "Operate the alert queue", text: "Route hybrid alerts, test 250/day capacity, monitor SLA/backlog, record investigation outcomes and escalation.", evidence: "5,537 alerts; base backlog zero" },
      { title: "Govern incidents and residual risk", text: "Link KRIs, 18 incidents, 10 scenarios, RCA, fairness/proxy review, UAT/SIT and management actions.", evidence: "228/228 final checks" }
    ],
    resultTables: [
      {
        title: "Observed champion and challengers",
        note: "PR-AUC is the primary ranking metric because fraud prevalence is only 0.1727% overall.",
        headers: ["Model", "Test PR-AUC", "Test ROC-AUC", "Role"],
        rows: [
          ["Class-weighted logistic", "0.7786", "0.9814", "Champion"],
          ["Logistic baseline", "0.6897", "0.9714", "Transparent baseline"],
          ["Hist gradient boosting", "0.7095", "0.9262", "Tree challenger"],
          ["Logistic + SMOTE", "0.7370", "0.9797", "Sampling challenger"],
          ["Isolation Forest", "0.0784", "0.9487", "Anomaly benchmark"]
        ]
      },
      {
        title: "Locked alert policy",
        note: "The score threshold was selected on validation and then applied unchanged to the untouched test set.",
        headers: ["Population", "Alert rate", "Fraud recall", "Amount recall", "Precision", "Backtest net benefit under disclosed cost assumptions"],
        rows: [
          ["Validation", "0.50%", "81.36%", "63.46%", "16.00%", "3,431 cost units"],
          ["Test", "0.40%", "84.93%", "69.36%", "28.44%", "2,349 cost units"]
        ]
      },
      {
        title: "Operational control view",
        note: "These are synthetic controls-testing results and are not represented as observed payment operations.",
        headers: ["Control", "Result", "Interpretation"],
        rows: [
          ["Rules-only", "3.39% precision / 9.97% recall", "Rules add interpretable coverage without label leakage"],
          ["Final hybrid test", "2.44% alert / 7.38% precision", "Model, anomaly and rule routing trade-off"],
          ["Final hybrid capture", "15.89% count / 16.90% amount", "Synthetic control effectiveness"],
          ["Base operations", "184.6 alerts/day vs 250 capacity", "No base backlog; stress breaches retained"],
          ["Operational incidents", "18 incidents / 10 scenarios", "RCA, owner, action and residual risk documented"]
        ]
      }
    ],
    alerts: [
      { tone: "amber", text: "Fraud-amount recall remains an Amber appetite exception even though test recall, precision, capacity and net benefit are strong." },
      { tone: "red", text: "CRITICAL synthetic queue precision is low and requires priority redesign and complementary high-value overlays." },
      { tone: "amber", text: "Stress-capacity scenarios create backlog despite zero Base backlog; release controls must retain staffing and routing triggers." },
      { tone: "info", text: "PCA features support prediction but cannot support business reason codes; reason codes come only from the synthetic controls layer." }
    ],
    decision: {
      finding: "The validation-locked 0.50% alert policy generalizes well on the test set and creates positive backtest net benefit under disclosed cost assumptions, but amount capture does not meet the Green target. The best decision is therefore a controlled candidate with explicit residual-risk acceptance.",
      recommendation: "Adopt the candidate only with Risk Committee acceptance of the Amber amount-capture gap, complementary high-value controls, queue-priority remediation and stress-capacity monitoring."
    },
    charts: [
      { src: "assets/images/p5-model-comparison.png", alt: "Observed fraud model comparison across champion and challenger models", caption: "Observed benchmark: class-weighted logistic is selected using validation evidence only." },
      { src: "assets/images/p5-pr-curve.png", alt: "Precision recall curve for observed fraud models", caption: "Precision-recall evidence is emphasized because the positive class is extremely rare." },
      { src: "assets/images/p5-class-imbalance.png", alt: "Observed fraud class imbalance", caption: "Class imbalance: 492 fraud cases among 284,807 transactions." },
      { src: "assets/images/p5-period-rate.png", alt: "Observed fraud rate by monitoring period", caption: "Stability review: outcome prevalence is checked across ordered monitoring periods." }
    ],
    validation: {
      headline: "Content, integrity, testing and clean-package validation passed with no unresolved failures.",
      cards: [
        { title: "Validation", text: "228 of 228 checks passed with zero unresolved failures." },
        { title: "Manifest", text: "180 of 180 artifacts passed integrity checks." },
        { title: "Testing", text: "38 UAT, 18 SIT and 16 executable negative tests passed." },
        { title: "Extraction", text: "The complete package was rebuilt end to end and passed integrity validation." }
      ]
    },
    limitations: [
      "Observed PCA variables are anonymized and cannot support business reason-code interpretation.",
      "Synthetic controls, alerts, investigator outcomes, incidents and operational workload are controls-testing evidence only.",
      "No live payment platform, production fraud engine, AML system, legal fairness conclusion or regulatory operational-risk capital model is claimed.",
      "Economic outputs use disclosed cost assumptions rather than observed recoveries, vendor fees or customer-friction data.",
      "Independent model validation, production approval and organisational release sign-off have not been performed."
    ],
    employerValues: [
      { title: "Right metric choice", text: "Rare-event performance is evaluated using PR-AUC, amount capture and threshold economics." },
      { title: "Detection to operations", text: "Model scores are linked to rules, alerts, capacity, incidents and root-cause analysis." },
      { title: "Claim discipline", text: "Observed benchmark evidence remains separate from synthetic controls-testing evidence." }
    ],
    artifacts: [
      { label: "Fraud & Operational Risk README", type: "MD", href: "evidence/project-5/README.md", detail: "Architecture, results and claim boundary" },
      { label: "Executive project summary", type: "MD", href: "evidence/project-5/recruiter_summary.md", detail: "Concise business and risk summary" },
      { label: "Threshold recommendation", type: "MD", href: "evidence/project-5/threshold_recommendation_memo.md", detail: "Validation hierarchy and test outcome" },
      { label: "Validation report", type: "MD", href: "evidence/project-5/validation_report.md", detail: "228/228 final result" },
      { label: "Model comparison", type: "CSV", href: "evidence/project-5/model_comparison.csv", detail: "Champion and challenger metrics" }
    ],
    next: { href: "#artifacts", label: "Evidence pack", title: "Supporting evidence" }
  }
};
