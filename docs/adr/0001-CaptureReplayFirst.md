# ADR 0001 — Replay-first capture in Python; C/libpcap is a stretch

Status: Accepted 2026-10-20 (Ayush)
Date: 2026-10-18

## Context
Nothing is built; the demo uses replayed pcaps only; four people on a short clock. Paper 1 and the brief say C + libpcap.

## Decision
`capture/` defines a `CaptureSource` interface. First implementation `ReplaySource` reads pcaps with scapy or dpkt in Python. A C/libpcap live agent may be added later behind the same interface.

## Consequences
Fastest path to a working pipeline; live capture is legally and technically out of scope for the review. The report must say capture is replay-based and must not claim libpcap until it exists. Paper 1 already says wiring libpcap is future work.

## Addendum 2026-10-20
Ayush proposed Rust for a later live capture agent. Rust is a good fit (memory-safe, fast pcap crates) but costs learning time and Windows build setup now, and adds a second deviation from Paper 1 (C + libpcap). Decision: Python replay now. A live agent (Rust or C, language open) is a stretch ticket that needs a volunteer owner and is never claimed in a report before it works.
