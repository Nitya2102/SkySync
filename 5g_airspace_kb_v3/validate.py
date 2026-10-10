import json,csv,sys,os
D=os.path.dirname(os.path.abspath(__file__)); err=[]
src={r["source_id"]:r for r in csv.DictReader(open(f"{D}/sources.csv"))}
cl=[json.loads(l) for l in open(f"{D}/claims.jsonl")]; ids={c["claim_id"] for c in cl}
ch=[json.loads(l) for l in open(f"{D}/rag_chunks.jsonl")]
if len(ids)!=len(cl): err.append("duplicate claim ids")
for c in cl:
    if c["source_id"] not in src: err.append(f'{c["claim_id"]}: unknown source {c["source_id"]}')
    if not c.get("legacy"):
        for f in("locator","verification","legal_status","jurisdiction"):
            if not c.get(f): err.append(f'{c["claim_id"]}: missing {f}')
        if len(c["claim"].split())<8: err.append(f'{c["claim_id"]}: too short')
for c in ch:
    if c["source_id"] not in src: err.append(f'{c["chunk_id"]}: unknown source')
    for x in c.get("claim_ids",[]):
        if x not in ids: err.append(f'{c["chunk_id"]}: unknown claim {x}')
for k in json.load(open(f"{D}/constraints.json"))["constraints"]:
    for x in k["evidence_claims"]:
        if x not in ids: err.append(f'{k["constraint_id"]}: unknown claim {x}')
for g in json.load(open(f"{D}/policy_gaps.json")):
    for x in g["evidence_claims"]:
        if x not in ids: err.append(f'{g["gap_id"]}: unknown claim {x}')
for k in json.load(open(f"{D}/conflicts.json")):
    for p in k["positions"]:
        for x in p["claims"]:
            if x not in ids: err.append(f'{k["conflict_id"]}: unknown claim {x}')
g=json.load(open(f"{D}/graph.json")); nid={n["id"] for n in g["nodes"]}
for e in g["edges"]:
    if e["source"] not in nid: err.append(f'edge bad source {e["source"]}')
    for x in e["evidence_claims"]:
        if x not in ids: err.append(f'edge unknown claim {x}')
# every agent must have retrievable non-legacy evidence
for a in ["network","airspace_safety","spectrum","policy_institutional","optimization","arbitration"]:
    n=sum(1 for c in cl if a in c.get("agents",[]) and not c.get("legacy")); 
    print(f"agent {a:22s} non-legacy claims: {n}")
    if n<5: err.append(f"thin coverage for {a}")
unused=[s for s in src if not any(c["source_id"]==s for c in cl)]
print("claims",len(cl),"sources",len(src),"chunks",len(ch),"sources without claims:",len(unused))
print("ERRORS:",err if err else "none"); sys.exit(1 if err else 0)
