# Datenübersicht

Zeilen pro Split × Label × Sprache (label 1 = Phishing/Spam), mean_len = mittlere Textlänge in Zeichen.

| split | label | lang | n | mean_len |
|---|---|---|---|---|
| train | 0 | de | 88 | 117.2 |
| train | 0 | en | 3599 | 71.0 |
| train | 1 | de | 156 | 134.8 |
| train | 1 | en | 505 | 135.5 |
| val | 0 | en | 450 | 67.7 |
| val | 1 | en | 63 | 135.2 |
| test | 0 | de | 18 | 155.7 |
| test | 0 | en | 450 | 74.6 |
| test | 1 | de | 86 | 146.6 |
| test | 1 | en | 63 | 131.5 |

## Gesamt pro Split

| split | n | spam-Anteil | mean_len |
|---|---|---|---|
| train | 4348 | 0.152 | 81.7 |
| val | 513 | 0.123 | 76.0 |
| test | 617 | 0.241 | 92.8 |

## Quellen pro Split

| source | train | val | test |
|---|---|---|---|
| german_legit | 18 | 0 | 18 |
| german_phishing | 86 | 0 | 86 |
| german_synthetic_legit | 70 | 0 | 0 |
| german_synthetic_phishing | 70 | 0 | 0 |
| uci_sms | 4104 | 513 | 513 |

Hinweis: URLs und der Platzhalter `*Link*` sind im Text durch `<URL>` ersetzt; synthetische deutsche Zeilen nur im Training; val enthält nur englische Zeilen.
