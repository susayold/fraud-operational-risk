# Threshold Economics Methodology

> This project is an educational fraud and operational-risk framework. It combines an observed PCA-transformed fraud benchmark with a separately labelled synthetic controls-testing environment. It is not a production fraud platform, live payment control, AML system or regulatory model.

The candidate alert-rate grid was frozen before model review: 0.05%, 0.10%, 0.20%, 0.50%, 1.00%, 2.00% and 5.00%. Base costs are 5.00 cost units per investigation, 70% preventable loss and 2.00 cost units per false-positive action. Capacity is normalised to 250 alerts per `monitoring_period` proxy because the source lacks actual calendar time.

Realised economics uses observed labels and transaction amount. Prospective economics uses calibrated probability, amount and the preventable-loss assumption. The two views are reported separately. Validation alone selects the threshold; test is an untouched confirmation population.
