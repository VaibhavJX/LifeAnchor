"""LifeLedger: persistent responsibility-case MCP server (SQLite + JSON-RPC over stdio)."""
import sys,json,os,sqlite3,uuid
from datetime import datetime,timezone
from pathlib import Path

DB=Path(os.environ.get("LIFEANCHOR_DB",Path(__file__).resolve().parents[2]/"data"/"lifeanchor.sqlite3"))
DB.parent.mkdir(parents=True,exist_ok=True)

def now():return datetime.now(timezone.utc).isoformat()
def connect():
    con=sqlite3.connect(DB)
    con.row_factory=sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS cases(
        id TEXT PRIMARY KEY,title TEXT NOT NULL,category TEXT,description TEXT,
        status TEXT,amount INTEGER,order_id TEXT,merchant TEXT,source_ref TEXT,
        source_type TEXT,due_at TEXT,next_check_at TEXT,user_confirmed INTEGER DEFAULT 0,
        evidence TEXT DEFAULT '[]', timeline TEXT DEFAULT '[]')""")
    con.execute("""CREATE TABLE IF NOT EXISTS actions(
        id TEXT PRIMARY KEY,case_id TEXT,body TEXT,status TEXT DEFAULT 'pending')""")
    con.commit()
    return con
def row(x):
    d=dict(x);d["evidence"]=json.loads(d["evidence"]);d["timeline"]=json.loads(d["timeline"])
    return d
def case(con,cid):
    x=con.execute("SELECT * FROM cases WHERE id=?",(cid,)).fetchone()
    if not x:raise ValueError("Case not found")
    return row(x)
def save(con,c):
    con.execute("UPDATE cases SET status=?,evidence=?,timeline=?,user_confirmed=? WHERE id=?",
                (c["status"],json.dumps(c["evidence"]),json.dumps(c["timeline"]),c["user_confirmed"],c["id"]))
    con.commit()
def event(c,label,detail):
    c["timeline"].append({"time":now(),"label":label,"detail":detail})
def execute(name,a):
    con=connect()
    try:
        if name=="get_cases":
            cases=[row(x) for x in con.execute("SELECT * FROM cases ORDER BY rowid DESC")]
            actions=[dict(x) for x in con.execute("SELECT * FROM actions ORDER BY rowid DESC")]
            return {"cases":cases,"actions":actions}
        if name=="create_life_case":
            cid="LA-"+uuid.uuid4().hex[:8].upper()
            c={"id":cid,"title":a["title"],"category":a.get("category","personal"),
               "description":a.get("description",""),"status":"open",
               "amount":a.get("amount"),"order_id":a.get("order_id"),
               "merchant":a.get("merchant"),"source_ref":a.get("source_ref","user"),
               "source_type":a.get("source_type","manual"),"due_at":a.get("due_at"),
               "next_check_at":a.get("next_check_at"),"user_confirmed":0,
               "evidence":[],"timeline":[]}
            event(c,"Case created","Responsibility saved with source and deadline")
            cols=list(c);vals=[json.dumps(c[x]) if x in ("evidence","timeline") else c[x] for x in cols]
            con.execute("INSERT INTO cases ("+",".join(cols)+") VALUES ("+",".join("?" for _ in vals)+")",vals)
            con.commit()
            return {"case_id":cid,"status":"open"}
        if name=="reset_demo":
            con.execute("DELETE FROM actions");con.execute("DELETE FROM cases");con.commit()
            return {"reset":True}
        cid=a.get("case_id")
        c=case(con,cid)
        if name=="record_followup_check":
            em=a.get("email")
            if not em:
                c["status"]="waiting";result="No new confirmation found. This does not prove the refund failed."
            elif (str(em.get("order_id"))!=str(c["order_id"]) or em.get("amount")!=c["amount"]):
                c["status"]="waiting";result="Confirmation mismatch. Keep case open."
            else:
                c["status"]="awaiting_user_confirmation"
                c["evidence"].append({"source_ref":em.get("id"),"type":"merchant_refund_issued","observed_at":now()})
                result="Merchant reports refund issued; ask user to confirm bank receipt."
            event(c,"Follow-up checked",result);save(con,c)
            return {"status":c["status"],"message":result}
        if name=="prepare_followup_draft":
            aid="ACT-"+uuid.uuid4().hex[:8].upper()
            body=f"Hello, I am following up on order #{c.get('order_id') or 'unknown'} and my pending refund. Could you please confirm the status? Thank you."
            con.execute("INSERT INTO actions(id,case_id,body,status) VALUES (?,?,?,?)",
                        (aid,cid,body,"pending"));con.commit()
            event(c,"Draft prepared","Email requires approval; no email has been sent");save(con,c)
            return {"action_id":aid,"body":body,"status":"pending","sent":False}
        if name=="review_draft":
            act=con.execute("SELECT * FROM actions WHERE id=? AND case_id=?",(a["action_id"],cid)).fetchone()
            if not act:raise ValueError("Action not found")
            decision=a.get("decision")
            if decision not in ("approve","reject"):raise ValueError("Invalid decision")
            # Approval is recorded, but fixture mode has no send tool.
            status="approved_not_sent" if decision=="approve" else "rejected"
            con.execute("UPDATE actions SET status=? WHERE id=?",(status,act["id"]));con.commit()
            event(c,"Draft reviewed","Approval recorded; no external email sent" if decision=="approve" else "Draft rejected")
            save(con,c)
            return {"status":status,"sent":False}
        if name=="verify_completion":
            if not c["evidence"]:
                return {"status":c["status"],"verified":False,"reason":"No matching evidence"}
            if not a.get("user_confirmed"):
                return {"status":c["status"],"verified":False,"reason":"User receipt confirmation needed"}
            c["user_confirmed"]=1;c["status"]="resolved"
            event(c,"Verified","Matching merchant evidence + user confirmed receipt");save(con,c)
            return {"status":"resolved","verified":True}
        raise ValueError("Tool not found")
    finally:con.close()

NAMES=["get_cases","create_life_case","record_followup_check","prepare_followup_draft","review_draft","verify_completion","reset_demo"]
def respond(msg):
    mid=msg.get("id")
    if mid is None:return
    try:
        method=msg.get("method")
        if method=="initialize":
            r={"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"LifeLedger","version":"0.1"}}
        elif method=="tools/list":
            r={"tools":[{"name":n,"description":n.replace("_"," "), "inputSchema":{"type":"object","additionalProperties":True}} for n in NAMES]}
        elif method=="tools/call":
            p=msg.get("params",{});r={"content":[{"type":"text","text":json.dumps(execute(p.get("name"),p.get("arguments",{})))}]}
        else:raise ValueError("Unknown MCP method")
        print(json.dumps({"jsonrpc":"2.0","id":mid,"result":r}),flush=True)
    except Exception as e:
        print(json.dumps({"jsonrpc":"2.0","id":mid,"error":{"code":-32000,"message":str(e)}}),flush=True)
for line in sys.stdin:
    try:respond(json.loads(line))
    except Exception:pass
