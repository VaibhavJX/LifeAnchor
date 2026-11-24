"""MCP server with TEST FIXTURES, not a live Gmail integration."""
import sys,json
RETURN={"id":"mail-return-1042","subject":"Return accepted — Order #1042",
        "merchant":"Example Store","order_id":"1042","amount":2499,
        "expected_date":"2026-11-23","body":"Refund expected by 23 Nov for order #1042."}
TOOLS={
 "search_return_email":{"description":"Find a demonstration return email","inputSchema":{"type":"object","properties":{"query":{"type":"string"}}}},
 "check_refund_update":{"description":"Test refund follow-up with simulated outcomes","inputSchema":{"type":"object","properties":{"scenario":{"type":"string"}}}}
}
def execute(name,args):
    if name=="search_return_email":return {"found":True,"email":RETURN,"simulated":True}
    if name=="check_refund_update":
        scenario=args.get("scenario","none")
        emails={
         "none":None,
         "wrong_order":{"id":"mail-other","order_id":"9999","amount":2499,"status":"issued"},
         "wrong_amount":{"id":"mail-amount","order_id":"1042","amount":1499,"status":"issued"},
         "matching_issued":{"id":"mail-1042-issued","order_id":"1042","amount":2499,"status":"issued"}
        }
        if scenario not in emails: raise ValueError("Invalid scenario")
        return {"email":emails[scenario],"scenario":scenario,"simulated":True}
    raise ValueError("Tool not found")
def respond(msg):
    method=msg.get("method"); id=msg.get("id")
    if id is None:return
    try:
        if method=="initialize":
            result={"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"gmail-fixture","version":"0.1"}}
        elif method=="tools/list":
            result={"tools":[{"name":k,**v} for k,v in TOOLS.items()]}
        elif method=="tools/call":
            p=msg.get("params",{})
            value=execute(p.get("name"),p.get("arguments",{}))
            result={"content":[{"type":"text","text":json.dumps(value)}]}
        else:raise ValueError("Unknown method")
        print(json.dumps({"jsonrpc":"2.0","id":id,"result":result}),flush=True)
    except Exception as e:
        print(json.dumps({"jsonrpc":"2.0","id":id,"error":{"code":-32000,"message":str(e)}}),flush=True)
for line in sys.stdin:
    try:respond(json.loads(line))
    except Exception:pass
