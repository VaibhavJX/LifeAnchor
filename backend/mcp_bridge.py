"""Minimal MCP JSON-RPC client; actual tool calls over stdio, fixture Gmail data."""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVERS = {"lifeledger": "lifeledger.py", "gmail_demo": "gmail_demo.py"}

def call_mcp(server, name, args=None):
    if server not in SERVERS:
        raise ValueError("Unknown MCP server")
    path = ROOT / "backend" / "mcp_servers" / SERVERS[server]
    commands = [
        {"jsonrpc":"2.0","id":1,"method":"initialize",
         "params":{"protocolVersion":"2024-11-05","capabilities":{},
                   "clientInfo":{"name":"LifeAnchor","version":"0.1"}}},
        {"jsonrpc":"2.0","method":"notifications/initialized","params":{}},
        {"jsonrpc":"2.0","id":2,"method":"tools/call",
         "params":{"name":name,"arguments":args or {}}}
    ]
    env=dict(os.environ)
    env["LIFEANCHOR_DB"]=str(ROOT/"data"/"lifeanchor.sqlite3")
    proc=subprocess.run([sys.executable,str(path)],
        input="\n".join(json.dumps(x) for x in commands)+"\n",
        text=True,capture_output=True,timeout=15,env=env)
    if proc.returncode:
        raise RuntimeError(proc.stderr[:300] or "MCP server failed")
    responses=[json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    msg=next((x for x in responses if x.get("id")==2),{})
    if "error" in msg: raise RuntimeError(str(msg["error"]))
    result=msg.get("result",{})
    if result.get("isError"): raise RuntimeError(str(result.get("content",[])))
    return json.loads(result["content"][0]["text"])
