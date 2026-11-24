# 🚀 LifeAnchor — Open the Live Hackathon Demo

**[▶ LAUNCH LIVE DEMO — Click here to open LifeAnchor on Render](https://lifeanchor-hackathon.onrender.com)**

Live demo: https://lifeanchor-hackathon.onrender.com

[GitHub Release](https://github.com/VaibhavJX/LifeAnchor/releases/tag/demo) · [Demo Script](DEMO_SCRIPT.md)

> The hosted prototype uses a simulated Gmail mailbox, not live Gmail access. The free hosting service may take time to start after inactivity.

---


> **Don't just remind me. Help me make sure it gets done.**

**wHACKiest 2026 — Track 1: Make MCP Matter: Less Magic, More Utility**

LifeAnchor is an interactive hackathon prototype for persistent responsibility tracking. It keeps the source, due date, next steps and evidence together; follows up through an MCP workflow; and does not treat an email or reminder as proof of task completion.

## Scope and honesty

- **Implemented:** Custom LifeLedger MCP server, minimal stdio JSON-RPC MCP client, persistent SQLite case storage, FastAPI API, and responsive browser dashboard.
- **Implemented with fixtures:** Gmail-like MCP server for controlled refund return/confirmation scenarios. This uses sample messages and **does not connect to real Gmail**.
- **Static Netlify preview:** Fully interactive browser-local simulation. It stores demonstration state in localStorage; it is **not the Python service** and shows no actual MCP network activity.
- **Not implemented yet:** Live Gmail OAuth, real sending, scheduled background workers, multi-account security, Calendar/Drive, and production-grade authorization.
- **Approval demo:** Approval records a decision; it never sends mail. The UI and returned result say so.

## How to run the full Python + MCP prototype

Requires Python 3.10+.

```bash
git clone https://github.com/VaibhavJX/LifeAnchor.git
cd LifeAnchor
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open **http://127.0.0.1:8000**.

The application invokes two separate MCP servers with JSON-RPC over stdio:

1. `gmail_demo.py` exposes `search_return_email` and `check_refund_update` using sample data.
2. `lifeledger.py` exposes `create_life_case`, `get_cases`, `record_followup_check`, `prepare_followup_draft`, `review_draft`, `verify_completion`, and `reset_demo`.

The LifeLedger server stores cases, evidence references, approvals and timestamps in `data/lifeanchor.sqlite3` (excluded from Git).

## Run the hackathon demo

1. Select **Discover sample refund** to import an illustrative returned-headphones email (₹2,499; order 1042).
2. Open the case. Try **No confirmation found**; the case remains waiting/open.
3. Try **Wrong order number** and **Wrong refund amount**; neither can resolve the case.
4. Try **Matching refund issued email**; this records matching merchant-issued evidence but still requests user confirmation of bank receipt.
5. Choose **I confirm bank receipt** only as a deliberate demo action; the case becomes resolved.
6. Prepare a support-email draft and approve/reject it. Approval is recorded; **no email is sent**.
7. Reload the local Python app to observe persistent cases and inspect MCP tool activity.

A merchant's "refund issued" email **does not prove that the money reached the recipient's bank account**. Gmail searches alone also cannot prove a refund was not received.

## Architecture

```
Browser frontend / Netlify static preview
                |
            FastAPI API              [backend mode only]
                |
        MCP JSON-RPC client
             /       \
 Demo Gmail MCP      LifeLedger MCP
   fixtures             |
                   SQLite database
```

## Key files

| File | Responsibility |
| --- | --- |
| `netlify/index.html` | Self-contained frontend; works as static preview or with API |
| `backend/main.py` | FastAPI endpoints and tool trace |
| `backend/mcp_bridge.py` | MCP initialize + tool call client |
| `backend/mcp_servers/gmail_demo.py` | Simulated Gmail mailbox MCP server |
| `backend/mcp_servers/lifeledger.py` | Custom persistent case MCP server |
| `tests/test_flow.py` | Refund matching and approval tests |

## Netlify

Connect this GitHub repository to Netlify with:
- **Build command:** none
- **Publish directory:** `netlify`

The `netlify.toml` already sets the publish directory. Netlify serves only the static frontend, not the FastAPI backend. To provide real backend features online, host FastAPI separately and configure an authenticated API connection.

## Privacy and safety

No provider credentials are shipped or requested by the demo. Fixture email text is test data. Never commit `.env`, OAuth tokens or real user case databases. Before adding real accounts: implement scoped OAuth, user ownership, explicit approval for consequential actions, prompt-injection protections, secure token storage, and reliable job scheduling.

## Hackathon pitch

**Discover → Understand → Plan → Follow up → Verify**

The differentiator is *stateful, evidence-aware follow-through*, not merely a chatbot or another reminder list.

This repository is a hackathon demonstration and is not production-ready.
