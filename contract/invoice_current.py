# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from dataclasses import dataclass
from datetime import datetime,timezone
import hashlib,json
def c(v,n=900):return str(v).strip()[:n]
def kid(v):
 x=c(v,72).upper()
 if not x:raise gl.vm.UserError('[EXPECTED] invoice id required')
 return x
def url(v):
 s=c(v,500);r=s[8:] if s.startswith('https://') else '';h=r.split('/')[0].lower();p=r[len(h):]
 if not h or '.' not in h or '@' in h or not p.startswith('/'):raise gl.vm.UserError('[EXPECTED] valid HTTPS source')
 return s,h
def obj(v):
 if isinstance(v,dict):return v
 s=str(v);a=s.find('{');b=s.rfind('}')
 if a<0 or b<=a:raise gl.vm.UserError('[LLM_ERROR] invalid JSON')
 return json.loads(s[a:b+1])
@allow_storage
@dataclass
class Invoice:owner:Address;debtor:str;amount:u256;sources:str;expiry:u256;state:str;decision:str;risks:str;digests:str
class InvoiceCurrent(gl.Contract):
 invoices:TreeMap[str,Invoice]
 def __init__(self):pass
 def _get(self,i):
  k=kid(i)
  if k not in self.invoices:raise gl.vm.UserError('[EXPECTED] invoice not found')
  return k,self.invoices[k]
 @gl.public.write
 def file(self,i:str,debtor:str,amount:u256,sources:list[str],expiry:u256)->None:
  k=kid(i)
  if k in self.invoices:raise gl.vm.UserError('[EXPECTED] duplicate invoice id')
  p=[url(x) for x in sources]
  if len(p)!=3 or len(set(x[1] for x in p))!=3 or int(amount)==0 or int(expiry)<=int(datetime.now(timezone.utc).timestamp()):raise gl.vm.UserError('[EXPECTED] complete three-party invoice required')
  self.invoices[k]=Invoice(gl.message.sender_address,c(debtor,120),amount,json.dumps([x[0] for x in p]),expiry,'FILED','','[]','[]')
 def _review(self,r):
  urls=json.loads(r.sources)
  def run():
   docs=[];dig=[]
   for ix,u in enumerate(urls):
    raw=gl.nondet.web.get(u).body[:14000];b=raw if isinstance(raw,bytes) else str(raw).encode();dig.append(hashlib.sha256(b).hexdigest());docs.append({'role':('invoice','delivery','debtor_policy')[ix],'body':b.decode(errors='replace')})
   q='Assess eligibility for a new contract-local receivable record. JSON only {"decision":"ELIGIBLE|REVIEW|REJECTED|INSUFFICIENT","risk_codes":[]}. Require matching invoice and delivery, debtor policy allowance, and amount consistency. AMOUNT:'+str(int(r.amount))+' DEBTOR:'+r.debtor+' DOCS:'+json.dumps(docs)
   x=obj(gl.nondet.exec_prompt(q,response_format='json'));d=c(x.get('decision'),20).upper()
   if d not in ('ELIGIBLE','REVIEW','REJECTED','INSUFFICIENT'):d='INSUFFICIENT'
   return {'decision':d,'risks':sorted(set(c(x,80).upper() for x in x.get('risk_codes',[])[:20] if c(x,80))),'digests':dig}
  def valid(x):
   if not isinstance(x,gl.vm.Return):return False
   try:
    g=x.calldata;docs=[];dig=[]
    for ix,u in enumerate(urls):
     raw=gl.nondet.web.get(u).body[:14000];b=raw if isinstance(raw,bytes) else str(raw).encode();dig.append(hashlib.sha256(b).hexdigest());docs.append({'role':ix,'body':b.decode(errors='replace')})
    if g['digests']!=dig or g['decision'] not in ('ELIGIBLE','REVIEW','REJECTED','INSUFFICIENT'):return False
    q='Verify exact eligibility and every risk code. JSON only {"valid":true}. PROPOSAL:'+json.dumps(g)+' DOCS:'+json.dumps(docs)
    return bool(obj(gl.nondet.exec_prompt(q,response_format='json')).get('valid',False))
   except:return False
  return gl.vm.run_nondet_unsafe(run,valid)
 @gl.public.write
 def assess(self,i:str)->None:
  _,r=self._get(i)
  if r.state!='FILED' or int(datetime.now(timezone.utc).timestamp())>int(r.expiry):raise gl.vm.UserError('[EXPECTED] assessment unavailable')
  x=self._review(r);r.decision=x['decision'];r.risks=json.dumps(x['risks']);r.digests=json.dumps(x['digests']);r.state=x['decision']
 @gl.public.write
 def settle(self,i:str)->None:
  _,r=self._get(i)
  if r.owner!=gl.message.sender_address or r.state!='ELIGIBLE':raise gl.vm.UserError('[EXPECTED] owner eligible invoice required')
  r.state='SETTLED'
 @gl.public.write
 def expire(self,i:str)->None:
  _,r=self._get(i)
  if r.state!='FILED' or int(datetime.now(timezone.utc).timestamp())<=int(r.expiry):raise gl.vm.UserError('[EXPECTED] expiry unavailable')
  r.state='EXPIRED'
 @gl.public.view
 def get_invoice(self,i:str)->dict:
  k,r=self._get(i);return {'id':k,'owner':r.owner.as_hex,'debtor':r.debtor,'amount':int(r.amount),'sources':json.loads(r.sources),'expiry':int(r.expiry),'state':r.state,'decision':r.decision,'riskCodes':json.loads(r.risks),'digests':json.loads(r.digests)}
