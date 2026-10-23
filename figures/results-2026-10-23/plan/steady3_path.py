# steady3: serpentine path over card% x PL x case rpm, wait times from the settled model + tau
import numpy as np, csv, math
CASE=[800,1000,1300,1600,1900,2400,3000]; CARD=[40,50,60,70,80,90,100]; PLS=[100,90,80,70]
PW={100:575,90:518,80:460,70:402}; RPM={40:1312,50:1595,60:1879,70:2162,80:2446,90:2729,100:3013}
TAU={40:130,50:100,60:90,70:64,80:55,90:55,100:55}; TIN=19.3
def core(g,c,pl): return TIN+2.111+PW[pl]*(0.053213+1/(8.1733*(RPM[g]/1000)**2.1384+5.5888*(c/1500)**1.0613))
path=[]; pls=PLS[:]; cases=CASE[:]
for g in CARD:
    for pl in pls:
        for c in cases: path.append((g,pl,c))
        cases=cases[::-1]
    pls=pls[::-1]
rows=[]; prev=None; t=0
for i,(g,pl,c) in enumerate(path,1):
    T=core(g,c,pl); dT=0 if prev is None else T-prev
    tau=TAU[g]; mn=480 if g==40 else 300
    w=mn if abs(dT)<1e-6 else max(mn, tau*math.log(max(1,60*abs(dT)/(0.1*tau))))
    w=min(w,900) if i>1 else 900+600   # first point: warm-up 10 min + hold
    t+=w; rows.append(dict(n=i,card=g,pl=pl,case=c,core=round(T,1),dT=round(dT,1),tau=tau,wait_s=round(w),t_h=round(t/3600,2))); prev=T
with open("plan/steady3_path.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
anch=int(t//10800)
print("points",len(rows),"hours",round(t/3600,1),"+anchors",anch,"(~",anch*8,"min)","max|dT|",max(abs(r['dT']) for r in rows))
import collections
for g in CARD:
    b=[r for r in rows if r['card']==g]
    print(g, "pts",len(b),"h",round(sum(r['wait_s'] for r in b)/3600,2),"maxdT",max(abs(r['dT']) for r in b),"first",b[0]['pl'],b[0]['case'],b[0]['dT'],"core",min(r['core'] for r in b),"-",max(r['core'] for r in b))
