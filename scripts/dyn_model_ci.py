import json,os,sys,time,numpy as np
sys.path.insert(0,os.getcwd()); import dyn_model as dm
J=json.load(open('results-2026-10-21/dyn-model.json')); p=dict(J['M2-pow']['params'])
D=dm.load('grid1c'); t=time.time(); y0=dm.core_pred(p,D,2)[0]; print('sim s',time.time()-t)
names=['Rjs','ra','Cs','k','m','q','th0']; res0=y0-D['core']; n=len(res0)
Jm=[]
for nm in names:
  h=abs(p[nm])*1e-4 or 1e-4; q=dict(p); q[nm]+=h; Jm.append((dm.core_pred(q,D,2)[0]-y0)/h)
Jm=np.array(Jm).T; s2=np.sum(res0**2)/(n-len(names))
cov=s2*np.linalg.inv(Jm.T@Jm)
rho=np.corrcoef(res0[:-1],res0[1:])[0,1]; neff=n*(1-rho)/(1+rho); infl=np.sqrt(n/neff)
print('n',n,'rho',rho,'neff',neff)
out={}
for i,nm in enumerate(names):
  se=np.sqrt(cov[i,i])*infl; out[nm]=(p[nm],1.96*se); print(nm,p[nm],'+-',1.96*se)
sd=np.sqrt(np.diag(cov)); C=cov/np.outer(sd,sd); print('corr Rjs+ra vs th0', C[0,6],C[1,6])
json.dump({k:[float(a),float(b)] for k,(a,b) in out.items()}|{'rho':float(rho),'neff':float(neff)},open('results-2026-10-21/dyn-model-ci.json','w'),indent=1)
