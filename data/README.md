# Data

Datasets and pcaps. Big files are gitignored (`data/*` in `.gitignore`). Crafted lab pcaps are listed in `MANIFEST.md`.

## Honesty note (dataset spike, issue #10)

Written offline. Sizes, URLs and citations below come from the spike author's knowledge of the CIC pages, not from a live check. Status of each row is **Unverified** until a teammate opens the page, confirms licence text, size and link, and edits the row. `FetchData.py` has not been run against the network.

Update 2026-11-22 (ticket #52): the CIC-Bell-DNS-EXF-2021 row was checked by a person (page on 2026-10-29, download on 2026-11-22). The other dataset rows are still Unverified.

## Datasets considered

| Dataset | Form | Attacks | DNS tunneling? | Size (approx) | Licence | Citation | Source | Date fetched | Status |
|---|---|---|---|---|---|---|---|---|---|
| CIC-IDS2017 | CICFlowMeter CSV (`MachineLearningCSV.zip`) plus raw pcaps | Brute force FTP/SSH, DoS, Heartbleed, web attacks, infiltration, botnet, port scan, DDoS | No | CSV zip ~0.2 GB; pcaps ~50 GB | UNB CIC terms: free for research, cite the paper. No SPDX licence | Sharafaldin, Lashkari, Ghorbani. "Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization". ICISSP 2018 | https://www.unb.ca/cic/datasets/ids-2017.html | not fetched | Unverified |
| CIC-Bell-DNS-EXF-2021 | raw DNS pcaps (heavy attack, light attack, benign) plus CSVs with 30 features per DNS packet (CSVs not downloaded) | DNS exfiltration of six file types (audio, compressed, exe, image, text, video) with one tool, DNSExfiltrator (base64URL, 500 ms throttle, 63-character labels) | Yes | 270.8 MB in total per the page. Downloaded: 18 pcaps, 258.1 MiB (about 270.6 MB), zips about 65 MB. The page's prose swaps heavy and light (it says heavy 20.7 MB, light 147.6 MB); Table 2's attack figures (heavy 147.6 MB, light 20.7 MB) match the files, its benign rows (90.3 MB and 62.4 MB) do not (real benign pcaps total about 102 MB) | No named licence. Page allows redistribution, republishing and mirroring in any form; any use or redistribution must cite the dataset and the paper | Mahdavifar, Salem, Victor, Garzon, Razavi, Hellberg, Lashkari. "Lightweight Hybrid Detection of Data Exfiltration using DNS based on Machine Learning", 11th IEEE ICCNS, December 2021, Weihai, China | https://www.unb.ca/cic/datasets/dns-exf-2021.html . The download link (cicresearch.ca, http and https both load) opens a request form asking for name and details. After the form, the PCAP folder holds `Attack_heavy_Benign`, `Attack_Light_Benign` and a standalone `Benign.zip` | page and link checked by a person 2026-10-29; PCAP folder downloaded by a person 2026-11-22; files kept out of git | Verified (see download record below, ticket #52) |
| CIC-DoHBrw-2020 | CICFlowMeter-style CSV plus pcaps | DoH tunneling (dns2tcp, dnscat2, iodine over DoH) | Over DoH only, not plain DNS | ~ a few GB, unknown | UNB CIC terms: research use, cite the paper | MontazeriShatoori, Davidson, Kaur, Lashkari. "Detection of DoH Tunnels using Time-series Classification of Encrypted Traffic". DASC 2020 | https://www.unb.ca/cic/datasets/dohbrw-2020.html | not fetched | Unverified |
| Lab pcaps (ours) | crafted scapy pcaps | Synthetic DNS tunnel | Yes (synthetic) | < 5 MB each | Ours | n/a, see `MANIFEST.md` | `data/tools/MakeDnsPcaps.py` | 2026-10-21 | Working |

## CIC-Bell-DNS-EXF-2021 download record (ticket #52, 2026-11-22)

Stored under `data/cic-bell-dns-exf-2021/` (gitignored, not committed). Total 258.1 MiB across 18 pcaps, under the 1 GB limit. Sizes below are MiB as reported by PowerShell.

Tunnel pcaps (12, one tool: DNSExfiltrator):

| Group | Files (MiB) |
|---|---|
| Heavy attack (140.8) | heavy_audio 22.3, heavy_compressed 20.5, heavy_exe 19.6, heavy_image 23.2, heavy_text 33.6, heavy_video 21.6 |
| Light attack (19.6) | light_audio 6.5, light_compressed 5.4, light_exe 3.4, light_image 0.3, light_text 1.6, light_video 2.4 |

Benign pcaps (6, about 97.7 MiB):

| Group | Files (MiB) |
|---|---|
| Standalone (47.8) | benign_1 27.6, benign_2 20.2 |
| With heavy attack (38.2) | benign_heavy_1 11.7, benign_heavy_2 12.5, benign_heavy_3 14.0 |
| With light attack (11.7) | benign 11.7 |

Each benign group also ships `domains_*.txt` lists (the domains the benign traffic was generated from).

Notes for the report:

- One tunnelling tool only (DNSExfiltrator), so tool variety is limited.
- Benign traffic is script-generated from Alexa top-1M domains, not real users. That fits the ethics rule (no real user traffic) but is less realistic than human DNS.
- File signature: the first four bytes of all 18 pcaps are `d4c3b2a1` (classic pcap, little-endian), checked 2026-11-22.
- The CSV folder was not downloaded; its columns are unconfirmed.

sha256 of the downloaded zips:

| Zip | sha256 |
|---|---|
| `benign-standalone/Benign.zip` | `299787AC7F88F56DD9CAF1AA7DD60D21BD398F9F46E5AE4B2D165B0363ADD899` |
| `heavy/Attacks.zip` | `1D9DD77380DF3B004C5387E2771C24FAB8CE6756E3DC6F3E2A5675DF160DF343` |
| `heavy/Benign.zip` | `13D938E97F51BF92DBA021FAA30F74CA5EEE3863E5EC8D2DCFCAA808DC91B7CB` |
| `light/Attacks.zip` | `1AB347229846CFA92A100B3C603982B0EB95799CA35B422235D310A578287DD0` |
| `light/Benign.zip` | `99C653F3566DAF764C5C8E2B9328480FAAA69BC802C35A1440F5766CB7571897` |

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
3. **Use CIC-Bell-DNS-EXF-2021 as the optional real-traffic check for CoverTrace**, after confirming its size and licence. It has real tool-generated tunnels (one tool, DNSExfiltrator, so tool variety is a limitation), which our crafted pcaps do not. Ask Ayush before any download over 1 GB.
4. **Keep lab pcaps** as the demo input and the controlled tests (ADR 0007 part a).
5. Do not claim FlowSight is trained on real data until step 1 is run. Until then it is Designed, not Working (`GkmkbSpec.md` section 8).
Decision D8: **changed 2026-10-22** after the FlowSight grilling. CIC-IDS2017 is dropped for FlowSight: it has no DNS tunneling and its rows are whole flows, not windows. FlowSight trains on windows from real tool-generated captures (candidate CIC-Bell-DNS-EXF-2021 plus the team's laptop capture), split by capture. A person confirms the dataset page (licence, size, real link) before any download; downloads over 1 GB need Ayush's approval. See ADR 0007 addendum and ADR 0009. Recommendations 1 and 2 above are superseded.

## Evaluation sets (added 2026-10-22)

The evaluation spec (`docs/specs/EvalSpec.md`) adds: a labels file per pcap (each Entity tunnel or benign, written by the person who made the capture); a crafted benign set with CDN-hash names, `.local` and `.arpa` names and bursty human traffic, labelled "crafted" (ticket #81); and a consent record for each teammate and each benign capture (ticket #83). The CIC-Bell-DNS-EXF-2021 row was Unverified until the page check in ticket #52; it is now Verified (2026-11-22, see the download record above). Crafted and real data are never mixed in one result table.

## Fetch

No fetch script yet. The CIC-Bell-DNS-EXF-2021 download link opens a request form (name and details), so a plain download URL does not work and a script cannot fetch it unattended. A person submits the form, downloads the PCAP folder by hand into `data/cic-bell-dns-exf-2021/`, and records the sha256 of each file (see the download record above). Ask Ayush before anything over 1 GB.
