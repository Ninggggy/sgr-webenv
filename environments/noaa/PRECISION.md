# Numeric channels and task design

Data version: NClimDiv 20260904. The webpage, standard downloads and raw frontend input use distinct formatting channels.

| Query | Raw input | Webpage | Standard JSON/CSV |
|---|---:|---:|---:|
| 196612 / 24-month Z / 4104 Anomaly | -0.205 | -0.20 | -0.21 |
| 190704 / 10-month Z / 4101 Value | 1.325 | 1.32 | 1.33 |
| 190704 / 10-month Z / 4107 Anomaly | -0.945 | -0.94 | -0.95 |
| 192304 / 10-month Z / 4107 Anomaly | -0.175 | -0.17 | -0.18 |

Window aggregates and baseline calculations use rational arithmetic. Standard JSON/CSV/XML round at the indicator precision, with decimal midpoint rounding away from zero and normalized negative zero. Frontend raw values retain the precision expected by the original JavaScript formatter, which uses `Number(parseFloat(num).toFixed(precision))`.

Rank uses its own quantization and tie calculations. Tie and boundary windows can produce ranks different from the official archive. `rankStart` and `rankEnd` identify the tied positions.

When defining a task, specify the reading channel, units, precision, threshold comparison and operation order. Judge webpage-based calculations using the displayed values; judge download-based calculations using the specified export. If several channels are allowed, define the equivalence rule explicitly.
