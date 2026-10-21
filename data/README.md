# Data

Datasets and pcaps. Big files are gitignored (`data/*` in `.gitignore`). Crafted lab pcaps are listed in `MANIFEST.md`.

## Honesty note (dataset spike, issue #10)

Written offline. Sizes, URLs and citations below come from the spike author's knowledge of the CIC pages, not from a live check. Status of each row is **Unverified** until a teammate opens the page, confirms licence text, size and link, and edits the row. `FetchData.py` has not been run against the network.

## Datasets considered

| Dataset | Form | Attacks | DNS tunneling? | Size (approx) | Licence | Citation | Source | Date fetched | Status |
|---|---|---|---|---|---|---|---|---|---|
| CIC-IDS2017 | CICFlowMeter CSV (`MachineLearningCSV.zip`) plus raw pcaps | Brute force FTP/SSH, DoS, Heartbleed, web attacks, infiltration, botnet, port scan, DDoS | No | CSV zip ~0.2 GB; pcaps ~50 GB | UNB CIC terms: free for research, cite the paper. No SPDX licence | Sharafaldin, Lashkari, Ghorbani. "Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization". ICISSP 2018 | https://www.unb.ca/cic/datasets/ids-2017.html | not fetched | Unverified |
| CIC-Bell-DNS-EXF-2021 | pcaps plus stateless/stateful feature CSVs | DNS exfiltration via dnscat2, dns2tcp, iodine | Yes | Several GB, exact size unknown | UNB CIC terms: research use, cite the paper | Mahdavifar, Salem, Hanafy, Ghorbani. CIC-Bell-DNS-EXF-2021 (UNB CIC, 2021). Confirm venue on the page | https://www.unb.ca/cic/datasets/dns-exf-2021.html | not fetched | Unverified |
| CIC-DoHBrw-2020 | CICFlowMeter-style CSV plus pcaps | DoH tunneling (dns2tcp, dnscat2, iodine over DoH) | Over DoH only, not plain DNS | ~ a few GB, unknown | UNB CIC terms: research use, cite the paper | MontazeriShatoori, Davidson, Kaur, Lashkari. "Detection of DoH Tunnels using Time-series Classification of Encrypted Traffic". DASC 2020 | https://www.unb.ca/cic/datasets/dohbrw-2020.html | not fetched | Unverified |
| Lab pcaps (ours) | crafted scapy pcaps | Synthetic DNS tunnel | Yes (synthetic) | < 5 MB each | Ours | n/a, see `MANIFEST.md` | `data/tools/MakeDnsPcaps.py` | 2026-10-21 | Working |

## FlowSight feature mapping

Feature definitions are not written down in the repo yet. This table assumes: `flow_avg_pkt_size_log` = log of mean packet size in bytes; `flow_pkt_size_variance` = variance of packet size; `flow_iat_mean_ms` = mean inter-arrival time in ms; `flow_burst_ratio` = share of inter-arrival gaps under a configured burst threshold. Correct this table if the FlowSight owner defines them differently.

CICFlowMeter column names are from the public CIC-IDS2017 CSVs (units: IAT in microseconds). Check on the real header before training.

| Feature | CIC-IDS2017 CSV | CIC-Bell-DNS-EXF-2021 | CIC-DoHBrw-2020 | From pcap via ReplaySource |
|---|---|---|---|---|
| `flow_avg_pkt_size_log` | Derivable: `log1p(Packet Length Mean)` | Derivable if flow CSV has a packet size mean; else from pcap | Derivable: log of packet length mean | Direct from `pkt_sizes[]` |
| `flow_pkt_size_variance` | Direct: `Packet Length Variance` | Derivable from pcap; CSV columns unconfirmed | Direct: packet length variance | Direct from `pkt_sizes[]` |
| `flow_iat_mean_ms` | Derivable: `Flow IAT Mean` / 1000 (µs to ms) | Derivable from pcap; CSV columns unconfirmed | Derivable: flow IAT mean, unit to check | Direct from `iat_ms[]` |
| `flow_burst_ratio` | Missing. Only weak proxies (`Flow IAT Min/Max`, `Active Mean`, `Idle Mean`) | Missing in CSV, derivable from pcap | Missing in CSV, derivable from pcap | Direct from `iat_ms[]` with the burst threshold |

Takeaway: three of four features come from the CIC-IDS2017 CSV with trivial transforms. `flow_burst_ratio` needs per-packet timing, so it needs pcaps.

## Recommendation (for decision D8, Ayush confirms)

1. **Train and baseline FlowSight on CIC-IDS2017 CSVs.** Small download (~0.2 GB, under the 1 GB limit), well known so the panel recognises it, and three of four features map directly or by a one-line transform.
2. **Do not use CIC-IDS2017 for `flow_burst_ratio` or for any DNS tunnel claim.** It has no DNS tunneling and no per-packet timing in the CSV. Either drop burst ratio from the CIC-trained model, or compute it from a small slice of the raw pcaps (do not pull the full ~50 GB).
3. **Use CIC-Bell-DNS-EXF-2021 as the optional real-traffic check for CoverTrace**, after confirming its size and licence. It has real tool-generated tunnels (iodine, dnscat2), which our crafted pcaps do not. Ask Ayush before any download over 1 GB.
4. **Keep lab pcaps** as the demo input and the controlled tests (ADR 0007 part a).
5. Do not claim FlowSight is trained on real data until step 1 is run. Until then it is Designed, not Working (`GkmkbSpec.md` section 8).

Decision D8: **changed 2026-10-22** after the FlowSight grilling. CIC-IDS2017 is dropped for FlowSight: it has no DNS tunneling and its rows are whole flows, not windows. FlowSight trains on windows from real tool-generated captures (candidate CIC-Bell-DNS-EXF-2021 plus the team's laptop capture), split by capture. A person confirms the dataset page (licence, size, real link) before any download; downloads over 1 GB need Ayush's approval. See ADR 0007 addendum and ADR 0009. Recommendations 1 and 2 above are superseded.

## Evaluation sets (added 2026-10-22)

The evaluation spec (`docs/specs/EvalSpec.md`) adds: a labels file per pcap (each Entity tunnel or benign, written by the person who made the capture); a crafted benign set with CDN-hash names, `.local` and `.arpa` names and bursty human traffic, labelled "crafted" (ticket #81); and a consent record for each teammate and each benign capture (ticket #83). The CIC-Bell-DNS-EXF-2021 row stays Unverified until the page check in ticket #52. Crafted and real data are never mixed in one result table.

## Fetch

No fetch script yet. A first draft guessed the download URL over plain http, so it was dropped. Open the dataset page by hand, confirm the licence and the real HTTPS link, check the size, and only then add a download script (ask Ayush before anything over 1 GB).
