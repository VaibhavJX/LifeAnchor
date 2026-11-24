"""LifeAnchor API: MCP calls + persistent case dashboard. Gmail is a TEST FIXTURE."""
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field
from .mcp_bridge import call_mcp
ROOT=Path(__file__).resolve().parents[1]
app=FastAPI(title="LifeAnchor — MCP Follow-through Prototype",version="0.1")
TRACE=[]
def mcp(server,tool,args=None):
    try:
        result=call_mcp(server,tool,args or {})
        TRACE.insert(0,{"at":datetime.now().isoformat(timespec="seconds"),"server":server,
                        "tool":tool,"status":"ok","fixture":server=="gmail_demo"})
        del TRACE[40:]
        return result
    except Exception as exc:
        TRACE.insert(0,{"at":datetime.now().isoformat(timespec="seconds"),
                        "server":server,"tool":tool,"status":"error"})
        raise HTTPException(status_code=400,detail=str(exc))
class NewCase(BaseModel):
    title:str=Field(min_length=3,max_length=160)
    category:str="personal"
    description:str=""
    due_at:str|None=None
class Followup(BaseModel):
    case_id:str
    scenario:str
class CaseId(BaseModel):
    case_id:str
class Review(BaseModel):
    case_id:str
    action_id:str
    decision:str
@app.get("/api/state")
def state():
    return {**mcp("lifeledger","get_cases"),"trace":TRACE,"gmail_mode":"fixture","mcp_mode":"JSON-RPC over stdio"}
@app.get("/api/health")
def health():return {"ok":True,"gmail_simulated":True}
@app.post("/api/demo/discover")
def discover():
    found=mcp("gmail_demo","search_return_email",{"query":"order 1042"})
    email=found["email"]
    old=mcp("lifeledger","get_cases")["cases"]
    for c in old:
        if c["source_ref"]==email["id"]:return {"case_id":c["id"],"already_existing":True}
    r=mcp("lifeledger","create_life_case",{
      "title":"Track ₹2,499 headphone refund","category":"refund",
      "description":"Awaiting refund from "+email["merchant"],"source_ref":email["id"],
      "source_type":"Gmail fixture","amount":email["amount"],"order_id":email["order_id"],
      "merchant":email["merchant"],"due_at":email["expected_date"]})
    return {**r,"source":email,"simulated":True}
@app.post("/api/cases")
def create_case(item:NewCase):
    return mcp("lifeledger","create_life_case",item.model_dump())
@app.post("/api/demo/check")
def check(item:Followup):
    email=mcp("gmail_demo","check_refund_update",{"scenario":item.scenario})["email"]
    return mcp("lifeledger","record_followup_check",{"case_id":item.case_id,"email":email})
@app.post("/api/demo/draft")
def draft(item:CaseId):
    return mcp("lifeledger","prepare_followup_draft",item.model_dump())
@app.post("/api/demo/review")
def review(item:Review):
    return mcp("lifeledger","review_draft",item.model_dump())
@app.post("/api/demo/verify")
def verify(item:CaseId):
    return mcp("lifeledger","verify_completion",{"case_id":item.case_id,"user_confirmed":True})
@app.post("/api/demo/reset")
def reset():
    TRACE.clear()
    return mcp("lifeledger","reset_demo")
@app.get("/")
def index():
    return FileResponse(ROOT/"netlify"/"index.html")
