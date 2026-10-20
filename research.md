# GKMKB — Research

## Operating Mode
**Continuous.** Four-person team, long-running, tickets mandatory, handoff every Ojas session. Shared docs stay plain markdown so teammates need nothing from Ojas.

## Identity
GKMKB — Guarded Kill-chain Monitoring & Key Breach (formerly Operation Cactus / SENTINEL).
Course: BCY705 Capstone Phase-II, DSATM, B.E. CSE (Cyber Security).
Team: Ayush Rathod, Sharukh Khan, Shivansh Tripathi, Bhargav Moray. Guides on the paper: Gerard Deepak, Shalini Ranjan.

## Source Material
- `memory/handoffs/` Genesis handoff and `C:\Users\ayush\Downloads\operationCactusHandoff.md` (chat session decisions).
- `GKMKB_Phase2_Project_Description.md`, `GKMKB_Architecture_Methodology.md` (Downloads).
- `Operation_Cactus_Paper_Final(2).docx` — submitted Paper 1. Detection-layer baseline on 1,000 synthetic records, 8 features (4 FlowSight + 4 CoverTrace). LR 96.0% acc / 0.970 AUC, SVM 95.0%, XGBoost 91.5%. Synthetic only; the paper says so itself.
- `Operation Cactus/` agent prompts (SENTINEL tactical UI mock: Vite + React + Zustand, dummy data). UI reference only, not a backend.

## Facts To Respect
- Nothing real is built (2026-10-18). Every capability is "designed" until a merged PR proves it.
- Paper 1 describes C + libpcap capture and a fused classifier. The code must not contradict the paper, and reports must not claim more than the code does. See ADR 0001 and 0002.
- Demo and evaluation traffic: replayed or lab-generated only, never real users.
- Next deadline: "sometime after 24 Oct 2026", exact date unknown. Plan assumes a working demo slice by 2026-10-24 and polish after.
