# LifeAnchor: 2–3 minute judge demo

**00:00–00:20** Explain the follow-through gap: reminders tell you what to do, but do not establish whether an outcome occurred.

**00:20–00:40** Show LifeAnchor's overview. Explain the generic case model (refunds, applications, bills). Other automations are future scope.

**00:40–01:00** Click *Discover sample refund*. Observe two genuine MCP JSON-RPC servers (a mock Gmail MCP fixture and the LifeLedger MCP server) in the activity log; view the source email reference.

**01:00–01:25** Run "No confirmation", "Wrong order", or "Wrong amount". The case remains open.

**01:25–01:45** Run "Matching refund issued email." LifeAnchor records the evidence and asks the user to confirm bank receipt rather than making a false completion claim.

**01:45–02:05** Confirm bank receipt in the demo. LifeLedger resolves the case and records the evidence-backed timeline.

**02:05–02:25** Create a follow-up draft; approve or reject it. No real email is sent.

**02:25–02:45** Reload the Python-hosted app to demonstrate database persistence and point to the MCP activity trace.

**Close:** *Don't just remind me. Help me make sure it gets done.*

## Important disclaimers

- Gmail is simulated using test fixtures. Do not claim live Gmail OAuth.
- The Netlify-hostable browser preview is local simulation, with no real MCP calls.
- The full Python prototype makes real MCP JSON-RPC calls to its bundled servers.
- No bank account integration, actual refund verification, or email sending is implemented.
- The user must explicitly confirm bank receipt before the demo resolves the refund.
