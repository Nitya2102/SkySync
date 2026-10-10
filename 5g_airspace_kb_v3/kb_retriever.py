"""Dependency-free hybrid retriever for the 5G-airspace KB (BM25 + filters + claim/constraint expansion)."""
import json,math,re,collections,os,sys
D=os.path.dirname(os.path.abspath(__file__))
def _jl(p): return [json.loads(l) for l in open(os.path.join(D,p))]
tok=lambda s:re.findall(r"[a-z0-9\.\-]+",s.lower())
class KB:
    def __init__(s):
        s.chunks=_jl("rag_chunks.jsonl"); s.claims={c["claim_id"]:c for c in _jl("claims.jsonl")}
        s.cons=json.load(open(os.path.join(D,"constraints.json")))["constraints"]
        s.conf=json.load(open(os.path.join(D,"conflicts.json"))); s.gaps=json.load(open(os.path.join(D,"policy_gaps.json")))
        # index chunks AND decision-relevant claims as documents
        s.docs=[dict(kind="chunk",id=c["chunk_id"],text=c["text"],meta=c) for c in s.chunks]
        s.docs+=[dict(kind="claim",id=c["claim_id"],text=c["claim"]+" "+str(c.get("object","")),meta=c) for c in s.claims.values() if not c.get("legacy")]
        s.t=[tok(d["text"]) for d in s.docs]; s.N=len(s.docs); s.avg=sum(map(len,s.t))/s.N
        s.df=collections.Counter(w for t in s.t for w in set(t))
    def _bm(s,q,i,k1=1.4,b=.75):
        tf=collections.Counter(s.t[i]); L=len(s.t[i]); sc=0
        for w in tok(q):
            if w in tf: sc+=math.log(1+(s.N-s.df[w]+.5)/(s.df[w]+.5))*tf[w]*(k1+1)/(tf[w]+k1*(1-b+b*L/s.avg))
        return sc
    def search(s,q,agent=None,jurisdiction=None,k=4,as_of="2026-10-07"):
        out=[]
        for i,d in enumerate(s.docs):
            m=d["meta"]
            if agent and m.get("agents") and agent not in m["agents"]: continue
            j=m.get("jurisdiction","")
            if jurisdiction and j not in("n/a",) and jurisdiction.lower() not in j.lower() and "international" not in j.lower(): continue
            sc=s._bm(q,i)
            if sc<=0: continue
            tier=m.get("authority_tier",1)
            if m.get("legacy"): sc*=0.5
            if m.get("superseded_by"): sc*=0.3
            if d["kind"]=="claim": sc*= {"fetched_full_text_primary":1.15,"search_snippet_primary":1.0,"secondary_report":.6}.get(m.get("verification"),.9)
            else: sc*= {1:1.0,2:.9,3:.6}.get(tier,.8)
            out.append((sc,d))
        out.sort(key=lambda x:-x[0]); res=[]; seen=set()
        for sc,d in out[:k]:
            ids=d["meta"].get("claim_ids",[d["id"]] if d["kind"]=="claim" else [])
            cl=[s.claims[c] for c in ids if c in s.claims]
            cons=[c for c in s.cons if set(c["evidence_claims"])&set(ids)]
            warn=[f'{c["constraint_id"]} is {c["legal_status"]} (effective {c["effective_from"]})' for c in cons if "NOT_YET" in c["legal_status"] or c["legal_status"] in("evidence_gap","inference","voluntary_non_binding")]
            conf=[c["conflict_id"] for c in s.conf if any(set(p["claims"])&set(ids) for p in c["positions"])]
            if d["meta"].get("superseded_by"): warn.append("SUPERSEDED by "+d["meta"]["superseded_by"])
            key=d["id"]
            if key in seen: continue
            seen.add(key)
            res.append(dict(score=round(sc,2),id=d["id"],kind=d["kind"],text=d["text"][:220],evidence_ids=ids,
               constraints=[c["constraint_id"] for c in cons],conflicts=conf,warnings=warn,
               verification=sorted({c.get("verification") for c in cl}) ))
        return res
if __name__=="__main__":
    kb=KB(); q=" ".join(sys.argv[1:]) or "radio altimeter interference margin"
    for r in kb.search(q): print(json.dumps(r,indent=1))
