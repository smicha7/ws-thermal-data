// Builds the "Statistical tests" section of research/gpu-cooling-method.html from steady-stats.json (+ steady-points.csv,
// steady-stats-steady2.json) and writes it between <!--stats:start--> and <!--stats:end-->; also the Key-findings sentence
// between <!--kf-stats--> markers and the per-100 W lookup table between <!--per100:start--> markers.
// Usage: node stats_section.js <figure version> <first figure number> '<sizes json>'
const katex=require('katex'),fs=require('fs');
const JP=t=>JSON.parse(t.replace(/\bNaN\b/g,'null').replace(/-?\bInfinity\b/g,'null'));
const G='/Users/smicha/Applications/Pasek/research/gpu-map/', RD=G+'results-2026-10-22/';
const F='/Users/smicha/Claude/gruency-site/research/gpu-cooling-method.html'; let s=fs.readFileSync(F,'utf8');
const J=JP(fs.readFileSync(RD+'steady-stats.json','utf8')); const V=process.argv[2]||'1'; const FN=+(process.argv[3]||13);
const sz=JSON.parse(process.argv[4]||'{}');
const J2=fs.existsSync(RD+'steady-stats-steady2.json')?JP(fs.readFileSync(RD+'steady-stats-steady2.json','utf8')):null;
const DYN=JP(fs.readFileSync(G+'results-2026-10-21/dyn-model.json','utf8'))['M2-pow'].params;
// settled points: which core source per session
const pl=fs.readFileSync(RD+'steady-points.csv','utf8').trim().split('\n'); const ph=pl[0].split(',');
const pts=pl.slice(1).map(l=>{const v=l.split(',');const o={};ph.forEach((h,k)=>o[h]=v[k]);return o;});
const tableInt=pts.filter(p=>p.core_src==='table'&&Math.abs(+p.core_settled-Math.round(+p.core_settled))<1e-9).length;
const tableN=pts.filter(p=>p.core_src==='table').length, tableS=[...new Set(pts.filter(p=>p.core_src==='table').map(p=>p.session))];
const i=t=>katex.renderToString(t,{throwOnError:true}), d=t=>katex.renderToString(t,{displayMode:true,throwOnError:true});
const R=String.raw;
const f=(x,n=2)=>{const t=Math.abs(x).toFixed(n); return (x<0&&+t!==0?'&minus;':'')+t;};
const fp=p=>p<0.001?'&lt; 0.001':p.toFixed(p<0.01?3:2);
const P={}; J.params.forEach(p=>P[p.param]=p);
const sessName={val1:'val1 (21 October, evening)',val2:'val2 (21 to 22 October, night)',afternoon:'second run, afternoon (21 October)',night:'first-run night grid (20 to 21 October)',steady2:'steady2 (22 October)'};
const ns=Object.entries(J.sessions).map(([k,v])=>`${sessName[k]||k}: ${v}`).join('; ');
const T={}; J.tests.forEach(t=>T[t.test]=t);
const rej=k=>T[k]&&T[k].verdict.startsWith('reject');
const sym={'θ0':i('\\theta_0'),'r∞':i('r_\\infty'),'gN':i('g_N'),'m':i('m'),'gC':i('g_C'),'s':i('s')};
const unitH={'°C':'&deg;C','m°C/W':'m&deg;C/W','W/°C':'W/&deg;C','':''};
const prow=p=>{const name=p.param.startsWith('θ[')?`${i('\\theta_j')}, ${sessName[p.param.slice(2,-1)]||p.param.slice(2,-1)} &minus; ${J.ref}`:sym[p.param];
  return `<tr><td>${name}</td><td>${f(p.est)} ${unitH[p.unit]??p.unit}</td><td>${p.se_classic.toFixed(2)}</td><td>${p.se_HC3.toFixed(2)}</td><td>${p.se_cluster.toFixed(2)}</td><td>${p.se_cluster_series.toFixed(2)}</td><td>${f(p.ci95_HC3[0])} to ${f(p.ci95_HC3[1])}</td></tr>`;};
const formName={pow:'power, k N<sup>&minus;m</sup> C<sup>&minus;q</sup>',exp:'exponential in N',rat:'rational in N',cond:'<b>two parallel conductances (chosen)</b>',flow:'effective airflow, k (N + bC)<sup>&minus;m</sup>','R-resp cond':'per-watt response, same form','log-log':'log-log with interactions',spline:'natural cubic spline in ln N',tensor:'tensor spline surface (benchmark)'};
const crow=r=>{const base=r.model.replace(' +S','');return `<tr><td>${formName[base]||base}</td><td>${r.k}</td><td>${r.rmse.toFixed(2)}</td><td>${r.LOO.toFixed(2)}</td><td>${r.CV5.toFixed(2)}</td><td>${(r.LOSO??NaN).toFixed(2)}</td><td>${r.BIC.toFixed(1)}</td><td>${r.DWser.toFixed(2)}</td></tr>`;};
const withS=J.compare.filter(r=>r.model.endsWith('+S')); const without=J.compare.filter(r=>!r.model.endsWith('+S')&&r.model!=='tensor'&&r.model!=='spline');
const rmseNoS=[Math.min(...without.map(r=>r.rmse)),Math.max(...without.map(r=>r.rmse))];
const chosen=J.compare.find(r=>r.model===J.choice); const tensCmp=J.compare.find(r=>r.model==='tensor +S');
const vtxt=t=>t.verdict.startsWith('reject')?'rejected':'not rejected';
const testNames=[['Mean of residuals (t-test)','Mean residual is zero'],['Durbin–Watson, along N within (case, PL) series','Durbin–Watson along the GPU fans, within each series'],['Durbin–Watson, time order','Durbin–Watson in time order'],['Breusch–Godfrey LM, order 1, along N','Breusch–Godfrey, order 1, along the GPU fans'],['Breusch–Godfrey LM, order 2, along N','Breusch–Godfrey, order 2, along the GPU fans'],['Breusch–Godfrey LM, order 1, time (within session)','Breusch–Godfrey, order 1, in time'],['Breusch–Godfrey LM, order 2, time (within session)','Breusch–Godfrey, order 2, in time'],['corr(e, N)','Correlation of residuals with GPU fan speed'],['corr(e, C)','&hellip; with case fan speed'],['corr(e, P)','&hellip; with power'],['corr(e, Tin)','&hellip; with intake air'],['corr(e, time)','&hellip; with time'],['Breusch–Pagan (Koenker) on N, ln C, P','Breusch–Pagan (Koenker), constant variance'],['White (levels, squares, cross-products)','White, constant variance'],['White special (ŷ, ŷ²)','White, special form'],['Shapiro–Wilk','Shapiro–Wilk, normal residuals'],['Jarque–Bera','Jarque–Bera, normal residuals'],['Shapiro–Wilk without outliers |t*| > 3','Shapiro–Wilk without the largest outlier'],['Jarque–Bera without outliers |t*| > 3','Jarque–Bera without the largest outlier'],['Ramsey RESET (ŷ^2)','Ramsey RESET, squared fitted values'],['Ramsey RESET (ŷ^2,3)','Ramsey RESET, squares and cubes'],['Lack-of-fit F (pure error from replicates)','Lack of fit against pure error from replicates'],['Session effect = 0 (Wald, HC3)','Session offsets are zero (Wald, HC3)'],['Box–Cox λ (transform-both-sides), LR test λ = 1','Box&ndash;Cox, no transform needed (&lambda; = 1)'],['Within-session drift from repeated anchors (slope)','No drift within a session (repeated anchor points)']];
const fstat=t=>{const v=t.stat; if(t.test.startsWith('corr')) return `r = ${f(v)}`; if(t.test.startsWith('Mean')) return `${f(v,3)}&nbsp;&deg;C`;
  if(t.test.startsWith('Within-session')) return `${v>=0?'+':'&minus;'}${Math.abs(v).toFixed(3)}&nbsp;&deg;C/h`; if(t.test.startsWith('Shapiro')) return `W = ${v.toFixed(3)}`;
  if(t.test.startsWith('Box')) return `&lambda;&#770; = ${J.boxcox.lam.toFixed(2)}`; return v.toFixed(2);};
const trows=testNames.filter(([k])=>T[k]).map(([k,n])=>`<tr><td>${n}</td><td>${fstat(T[k])}</td><td>${fp(T[k].p)}</td><td>${vtxt(T[k])}</td></tr>`).join('');
const dwN=T['Durbin–Watson, along N within (case, PL) series'], dwT=T['Durbin–Watson, time order'];
const outlNote=(T['Shapiro–Wilk without outliers |t*| > 3']||{}).note||'';
const om=outlNote.match(/(\w+) card (\d+) % \/ case (\d+) rpm \/ PL (\d+) \(t = ([+\-0-9.]+)\)/);
const lof=T['Lack-of-fit F (pure error from replicates)']; const pe=(lof&&lof.note.match(/SD ([0-9.]+)/)||[])[1]; const pedf=(lof&&lof.note.match(/(\d+) replicate/)||[])[1];
const drift=T['Within-session drift from repeated anchors (slope)']; const driftSe=(drift.note.match(/± ([0-9.]+)/)||[])[1];
const reset=rej('Ramsey RESET (ŷ^2)')||rej('Ramsey RESET (ŷ^2,3)');
const VL=v=>{const M={'NVML table, whole °C (quantised)':'Core read in whole degrees (NVML)','NVAPI 0.01 °C, mean of last 60 s':'Core at 0.01&nbsp;&deg;C (NVAPI) where available, mean of the last 60&nbsp;s','NVAPI 0.01 °C, extrapolated to T∞ (settling-corrected)':'Core at 0.01&nbsp;&deg;C where available, extrapolated to the settled value (used)','without session effect':'Chosen form without session offsets','non-parametric benchmark: spline +S':'Spline in ln N, with session offsets','non-parametric benchmark: tensor +S':'Tensor spline, with session offsets','tensor spline R(N, C) + P² + session':'Tensor spline R(N,&nbsp;C) with a P<sup>2</sup> term and session offsets','chosen model, replicate points at equal N averaged':'Chosen model, repeated points averaged'}; if(M[v]) return M[v]; const b=v.match(/power curvature P\^β \(β = ([0-9.]+)\)/); return b?`Chosen form with power curvature P<sup>&beta;</sup>, &beta; = ${(+b[1]).toFixed(2)}`:v.replace('°C','&deg;C');};
const causes=J.dw_causes.map(c=>`<tr><td>${VL(c.variant)}</td><td>${c.rmse.toFixed(2)}</td><td>${c.DW_series.toFixed(2)}</td></tr>`).join('');
const tens=J.dw_causes.find(c=>c.variant.startsWith('tensor spline R'));
const nvml=J.dw_causes.find(c=>c.variant.startsWith('NVML')), nvapi=J.dw_causes.find(c=>c.variant.startsWith('NVAPI 0.01 °C, mean')), corr=J.dw_causes.find(c=>c.variant.startsWith('NVAPI 0.01 °C, extra'));
const beta=J.dw_causes.find(c=>c.variant.includes('P^β')); const betaV=beta?(+((beta.variant.match(/β = ([0-9.]+)/)||[])[1])).toFixed(2):null;
const fd=J.first_diff, el=J.elasticities, mx=J.mixed, fg=J.fgls;
const nS=Object.keys(J.sessions).length;
const pic=(name,th,alt,w,h,pw,ph)=>`<a class="ar-wide th-${th[0]}" href="/research/img/${name}-${th}.webp?v=${V}" aria-label="Open the chart at full size"><picture><source media="(max-width:620px)" srcset="/research/img/${name}-phone-${th}.webp?v=${V}" width="${pw}" height="${ph}"><img src="/research/img/${name}-${th}.webp?v=${V}" width="${w}" height="${h}" loading="lazy" decoding="async" alt="${alt}"></picture></a>`;
const fig=(name,alt,cap,w,h,pw,ph)=>`  <figure class="ar-fig">\n    ${pic(name,'light',alt,w,h,pw,ph)}${pic(name,'dark',alt,w,h,pw,ph)}\n    <figcaption>${cap}</figcaption>\n  </figure>\n`;
const DATA=`<a href="/research/data/gpu-map-steady-points.csv?v=${V}">settled points (CSV)</a>, <a href="/research/data/gpu-map-steady-residuals.csv?v=${V}">residuals (CSV)</a>, <a href="/research/data/gpu-map-steady-compare.csv?v=${V}">model comparison (CSV)</a> and <a href="/research/data/gpu-map-steady-stats.json?v=${V}">all results (JSON)</a>`;
const eq=d(R`T_\text{core} = T_\text{in} + \theta_0 + \theta_j + P\left[\, r_\infty + \frac{1}{g_N\,(N/1000)^{m} + g_C\,(C/1500)^{s}} \,\right] \tag{11}`);
const prov=tableN?`<p class="ar-status"><b>Provisional.</b> ${tableN} of the ${J.n} points, all from ${tableS.map(x=>sessName[x]||x).join(' and ')}, still use the core value from the run&rsquo;s summary table, ${tableInt} of them in whole degrees, without the settling correction, because their 1&nbsp;Hz log is still being copied from the test machine. The numbers below will be recomputed when it arrives, and again when the controller test ctrl1 ends at 16:40.</p>\n  `:'';
const hetero=[rej('Breusch–Pagan (Koenker) on N, ln C, P')?'Breusch&ndash;Pagan':null, rej('White (levels, squares, cross-products)')?'White':null].filter(Boolean);
const heteroTxt=hetero.length?`Because the ${hetero.join(' and the ')} test${hetero.length>1?'s reject':' rejects'} constant variance${hetero.length===1?(hetero[0]==='White'?' (Breusch&ndash;Pagan does not)':' (White does not)'):''}, we report heteroscedasticity-consistent (HC3) standard errors.`:'We report heteroscedasticity-consistent (HC3) standard errors as a precaution.';
const normalAll=!rej('Shapiro–Wilk')&&!rej('Jarque–Bera');
const normTxt=normalAll?'Their distribution is consistent with a normal one (Shapiro&ndash;Wilk and Jarque&ndash;Bera do not reject it)':'Their distribution is normal once the largest outlier is set aside';
const varTxt=hetero.length?'their variance is not constant, hence the HC3 errors':'their variance shows no clear dependence on the inputs';
const driftTxt=`the repeated anchor points drift by ${drift.stat>=0?'+':'&minus;'}${Math.abs(drift.stat).toFixed(3)}&nbsp;&deg;C per hour${driftSe?` (&plusmn;&nbsp;${driftSe})`:''}, ${drift.p<0.05?'which is significant at the 5&nbsp;% level':`not significant at the 5&nbsp;% level (p = ${fp(drift.p)})`}`;
const s2=J2?(()=>{const c=J2.compare.find(r=>r.model===J2.choice), cc=J2.compare.find(r=>r.model==='cond +S')||J2.compare.find(r=>r.model==='cond');
  const nm={flow:'the effective-airflow form',exp:'the exponential form',pow:'the power form',rat:'the rational form','log-log':'the log-log form','R-resp cond':'the per-watt form'}[J2.choice.replace(' +S','')];
  if(J2.choice.replace(' +S','')==='cond') return ` Fitted to steady2 alone, ${J2.n} points in one session, two parallel conductances also predict best (leave-one-out ${c.LOO.toFixed(2)}&nbsp;&deg;C).`;
  return ` Fitted to steady2 alone, ${J2.n} points in one session, ${nm||J2.choice} predicts slightly better (leave-one-out ${c.LOO.toFixed(2)}&nbsp;&deg;C) than two parallel conductances (${cc.LOO.toFixed(2)}&nbsp;&deg;C); with all sessions the order is reversed. The difference is within the noise, so we keep the physically motivated form.`;})():'';
const sec=`<!--stats:start-->
  <h2 id="stats">Statistical tests</h2>
  ${prov}<p>This section tests the steady-state model on settled points only. The data are ${J.n} points: ${ns}. For the points with a 1&nbsp;Hz log the core is read from the NVAPI sensor at 0.01&nbsp;&deg;C, and each point&rsquo;s final value ${i('T_\\infty')} comes from fitting ${i('T(t) = T_\\infty - A\\,e^{-t/\\tau}')} to its last minutes. The reference session, against which the others are offset, is ${J.ref}. Units are &deg;C throughout, thermal resistance in m&deg;C/W and conductance in W/&deg;C.</p>
  <h3 id="stats-model">The model</h3>
  ${eq}
  <p>${i('\\theta_j')} is an offset for each measuring session ${i('j')}, zero for the reference session. The heatsink passes heat to the air along two paths in parallel, one driven by the card&rsquo;s fans and one by the case airflow; their conductances add. That is why the case fans matter when the GPU fans are slow and hardly at all when they are fast. ${i('r_\\infty')} is the resistance that no airflow removes. The constants are estimated by nonlinear least squares (Levenberg&ndash;Marquardt).</p>
  <p>Equation (11) replaces the static fit (9) for settled points. Its exponent ${i('m')} = ${P['m'].est.toFixed(2)} is far above the 0.5 to 0.8 that convection alone would give (section <a href="#model">A model of the cooler</a>): here the conductance also carries the fan&rsquo;s own airflow curve, so ${i('m')} is an empirical constant.${P['gC'].ci95_HC3[0]<0?` The case-fan path ${i('g_C')} is the least certain constant; its interval includes zero.`:''}</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-st">
    <thead><tr><th scope="col">Constant</th><th scope="col">Estimate</th><th scope="col">SE</th><th scope="col">SE HC3</th><th scope="col">SE cluster, session</th><th scope="col">SE cluster, series</th><th scope="col">95&nbsp;% interval, HC3</th></tr></thead>
    <tbody>${J.params.map(prow).join('')}</tbody>
  </table>
  </div>
  <p>The fit has an RMSE of ${chosen.rmse.toFixed(2)}&nbsp;&deg;C. Refitted with each point left out in turn, it predicts that point with an RMSE of ${chosen.LOO.toFixed(2)}&nbsp;&deg;C (leave-one-out); five-fold cross-validation gives ${chosen.CV5.toFixed(2)}&nbsp;&deg;C. ${heteroTxt} Cluster-robust errors by session rest on only ${nS} clusters and are indicative only.</p>
${fig('gpu-map-steady-two-ways','Two panels of settled core temperatures with the fitted model: on the left against GPU fan speed with the case fans at 1500 rpm, on the right against case fan speed with the GPU fans at 40 %, one curve per power limit; residuals below each panel stay within about one degree',`<b>Figure ${FN}.</b> Settled points and equation (11), two ways. Left: case fans at 1500&nbsp;rpm, GPU fans in rpm and %. Right: GPU fans at 40&nbsp;%, case fans in rpm and %. Points are moved to the reference session and the mean intake air, so all sessions share one curve per power limit; marker shape shows the session. Below: residuals.`,sz.tw||2200,sz.th||1480,sz.tpw||1000,sz.tph||3000)}
  <h3 id="stats-forms">Forms and transforms we tried</h3>
  <p>We fitted nine forms of the resistance, each with and without session offsets, and compared them by leave-one-out and five-fold cross-validation, by leaving out whole sessions, and by the Bayesian information criterion (BIC). Without session offsets the simple forms leave an RMSE of ${rmseNoS[0].toFixed(2)} to ${rmseNoS[1].toFixed(2)}&nbsp;&deg;C; the sessions differ by more than the forms do. With offsets:</p>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-st">
    <thead><tr><th scope="col">Form of R(N,&nbsp;C), with session offsets</th><th scope="col">Constants</th><th scope="col">RMSE</th><th scope="col">Leave-one-out</th><th scope="col">5-fold</th><th scope="col">Leave session out</th><th scope="col">BIC</th><th scope="col">DW along N</th></tr></thead>
    <tbody>${withS.map(crow).join('')}</tbody>
  </table>
  </div>
  <p class="ar-note">RMSE and cross-validation errors in &deg;C. BIC on the scale of ${i('T - T_\\text{in}')}, with the Jacobian term for transformed responses.</p>
  <p>The tensor spline fits the points most closely but predicts new ones worse (leave-one-out ${tensCmp.LOO.toFixed(2)}&nbsp;&deg;C), so it serves as a benchmark, not a model. Among the parametric forms, two conductances in parallel predict best.${s2} We also tried transforming the response. The Box&ndash;Cox profile, transforming both sides, gives ${i('\\hat\\lambda')} = ${J.boxcox.lam.toFixed(2)} with a 95&nbsp;% interval from ${f(J.boxcox.ci[0])} to ${f(J.boxcox.ci[1])}, which ${J.boxcox.ci[0]<=1&&J.boxcox.ci[1]>=1?'includes 1, no transform':'excludes 1'}${J.boxcox.ci[0]>0?' and excludes 0, the logarithm':''}. Modelling the per-watt rise ${i('R = (T - T_\\text{in})/P')} instead is the same mean with weights proportional to ${i('1/P^2')} and gives nearly the same constants. A log-log regression gives elasticities at the mean of ${el.P.toFixed(2)} for power, ${f(el.N)} for the GPU fans and ${f(el.C)} for the case fans: the rise is almost proportional to power.${betaV?` A power curvature ${i('P^{\\beta}')} gives ${i('\\beta')} = ${betaV} and only a small gain (RMSE ${beta.rmse.toFixed(2)}&nbsp;&deg;C).`:''}</p>
  <p>A first-difference estimator along the GPU fans, within each series of fixed session, case speed and power limit, removes ${i('\\theta_0')} and the session offsets altogether. On ${fd.n_pairs} pairs it gives ${i('g_N')} = ${fd.params.gN[0].toFixed(1)} &plusmn; ${fd.params.gN[1].toFixed(1)}&nbsp;W/&deg;C and ${i('m')} = ${fd.params.m[0].toFixed(2)} &plusmn; ${fd.params.m[1].toFixed(2)}, against ${P['gN'].est.toFixed(1)}&nbsp;W/&deg;C and ${P['m'].est.toFixed(2)} from the fit on levels.</p>
  <h3 id="stats-tests">The tests</h3>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-st ar-tests">
    <thead><tr><th scope="col">Test</th><th scope="col">Statistic</th><th scope="col">p</th><th scope="col">Verdict on the null</th></tr></thead>
    <tbody>${trows}</tbody>
  </table>
  </div>
  <p class="ar-note">Durbin&ndash;Watson p-values are exact, by Monte Carlo under the null given the regressors.${om?` The largest outlier is a ${om[1]==='night'?'first-run night-grid':om[1]} point at GPU fans ${om[2]}&nbsp;%, case fans ${om[3]}&nbsp;rpm and power limit ${om[4]}&nbsp;%, with a studentised residual of ${om[5].replace('-','&minus;')}.`:''}</p>
  <p>The residuals average zero and do not correlate with any input, with the fitted value or with time. In time order they show no autocorrelation (Durbin&ndash;Watson ${dwT.stat.toFixed(2)}), and ${driftTxt}. ${normTxt}; ${varTxt}. The session offsets are real: ${i('\\chi^2')} = ${T['Session effect = 0 (Wald, HC3)'].stat.toFixed(1)}, p ${fp(T['Session effect = 0 (Wald, HC3)'].p)}.</p>
  <h3 id="stats-open">An open item: the residuals run along the GPU fans</h3>
  <p>Within each series the residuals change sign slowly as the GPU fans speed up: Durbin&ndash;Watson along the fan axis is ${dwN.stat.toFixed(2)}, p ${fp(dwN.p)}, and the lack-of-fit test against the pure error of repeated points${pe?` (${pedf} degrees of freedom, standard deviation ${pe}&nbsp;&deg;C)`:''} ${rej('Lack-of-fit F (pure error from replicates)')?'rejects':'does not reject'} the form, p ${fp(lof.p)}.${reset?` The Ramsey RESET test now rejects it as well.`:''} We tested three causes.</p>
  <ul>
    <li><b>Sensor rounding is not the cause.</b> Durbin&ndash;Watson is ${nvml.DW_series.toFixed(2)} with the whole-degree NVML readings, ${nvapi.DW_series.toFixed(2)} with the 0.01&nbsp;&deg;C readings and ${corr.DW_series.toFixed(2)} after the settling correction.</li>
    <li><b>${drift.p<0.05?'Drift does not explain it.':'Drift is not the cause.'}</b> In time order Durbin&ndash;Watson is ${dwT.stat.toFixed(2)} and the Breusch&ndash;Godfrey test in time is ${rej('Breusch–Godfrey LM, order 1, time (within session)')?'significant':'not significant'}. ${drift.p<0.05?`The repeated anchor points do show a small drift, ${drift.stat>=0?'+':'&minus;'}${Math.abs(drift.stat).toFixed(2)}&nbsp;&deg;C per hour, about half a degree over a four-hour session; it is real but slow, and it cannot produce a pattern that reverses within one sweep of the GPU fans.`:`The ${driftTxt.replace('the repeated','repeated')}.`}</li>
    <li><b>The shape of the curve is the main cause.</b> A tensor-spline surface ${i('R(N, C)')} with a ${i('P^2')} term and session offsets brings Durbin&ndash;Watson to ${tens.DW_series.toFixed(2)}${tens.p_MC!=null&&!isNaN(tens.p_MC)?` (p = ${tens.p_MC.toFixed(2)})`:''} and the RMSE to ${tens.rmse.toFixed(2)}&nbsp;&deg;C${pe?`, against a pure error of ${pe}&nbsp;&deg;C`:''}.</li>
  </ul>
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-st">
    <thead><tr><th scope="col">Variant</th><th scope="col">RMSE, &deg;C</th><th scope="col">DW along N</th></tr></thead>
    <tbody>${causes}</tbody>
  </table>
  </div>
  <p>What remains, a few tenths of a degree, is a smooth error in the shape of the fan-response surface, with a slight concavity in power. We do not &ldquo;correct&rdquo; it with generalised least squares, because it is a symptom of the form, not of the noise; a Prais&ndash;Winsten fit with ${i('\\rho')} = ${fg.rho.toFixed(2)} moves the constants within their standard errors. ${J.sessions.steady2?`The dense steady2 grid has raised Durbin&ndash;Watson along the fans from 0.42 to ${dwN.stat.toFixed(2)}, but not to 2; a richer form of the fan response is the next step.`:'The steady2 series of 22 October, a dense grid of case speed by power limit in one session with repeated anchor points, is filling the empty cells of the design.'}</p>
${fig('gpu-map-steady-diagnostics','Six residual diagnostics of the steady-state model: against fitted values, along the GPU fans within each series with lines joining the points of a series, against case fan speed, against power, in time order, and a normal quantile plot',`<b>Figure ${FN+1}.</b> Residuals of equation (11): against the fitted value, along the GPU fans within each series (lines join the points of one series; Durbin&ndash;Watson ${dwN.stat.toFixed(2)}), against the case fans in rpm and %, against power, in time order (Durbin&ndash;Watson ${dwT.stat.toFixed(2)}), and a normal quantile plot. Colour shows the session.`,sz.dw||2400,sz.dh||1520,sz.dpw||1000,sz.dph||4200)}
  <h3 id="stats-sessions">Sessions</h3>
  <p>A mixed model with a random intercept per session (REML, shape constants held at their least-squares values) puts the spread between sessions at ${mx.sigma_session.toFixed(2)}&nbsp;&deg;C and the residual spread at ${mx.sigma_resid.toFixed(2)}&nbsp;&deg;C; the intra-class correlation is ${mx.ICC.toFixed(2)}. ${mx.re.night!==undefined?`The night session sits ${f(mx.re.night,1)}&nbsp;&deg;C from the average session, while the daytime sessions lie within ${(Math.max(...Object.entries(mx.re).filter(([k])=>k!=='night').map(([,v])=>v))-Math.min(...Object.entries(mx.re).filter(([k])=>k!=='night').map(([,v])=>v))).toFixed(1)}&nbsp;&deg;C of each other. `:''}Predicting a session the model has never seen costs about ${chosen.LOSO.toFixed(1)}&nbsp;&deg;C RMSE. The state of the case on the day, most likely the temperature of the air reaching the card, matters more than any remaining error of shape.</p>
  <p class="ar-note">Data: ${DATA}. Scripts: steady_data.py, steady_stats.py, fig_steady.py in the <a href="https://github.com/smicha7/ws-thermal-data">public data repository</a>.</p>
<!--stats:end-->`;
let a=s.indexOf('<!--stats:start-->'), b=s.indexOf('<!--stats:end-->'); if(a<0||b<0) throw 'markers missing';
s=s.slice(0,a)+sec+s.slice(b+'<!--stats:end-->'.length);
const kf=`<!--kf-stats--> On ${J.n} settled points from ${nS} sessions, the two-path model (11) fits within ${chosen.rmse.toFixed(2)}&nbsp;&deg;C (leave-one-out ${chosen.LOO.toFixed(2)}&nbsp;&deg;C)${tableN?'; provisional while part of the latest series is re-read at 0.01&nbsp;&deg;C':''}. <a href="#stats">Statistical tests</a><!--/kf-stats-->`;
a=s.indexOf('<!--kf-stats-->'); b=s.indexOf('<!--/kf-stats-->'); if(a<0||b<a) throw 'kf markers'; s=s.slice(0,a)+kf+s.slice(b+16);
// per-100 W lookup table at case 1500 rpm: (11) from steady fit, (10) dynamic, (9) static
const Rs=n=>P['r∞'].est/1000+1/(P['gN'].est*Math.pow(n/1000,P['m'].est)+P['gC'].est);
const Rd=n=>DYN.Rjs+DYN.ra+DYN.k*Math.pow(Math.sqrt(n*n+300*300)/1000,-DYN.m);
const S9=JP(fs.readFileSync(G+'article_tools/static/core-model.json','utf8')).full; const R9=n=>S9.rinf+S9.k*Math.pow(n/1000,-S9.m);
const rows=[[40,1312],[50,1595],[60,1879],[70,2162],[80,2446],[90,2729],[100,3012]].map(([g,n])=>`<tr><td>${g}&nbsp;%</td><td>${Math.round(n/10)*10}</td><td>${(100*Rs(n)).toFixed(1)}</td><td>${(100*Rd(n)).toFixed(1)}</td><td>${(100*R9(n)).toFixed(1)}</td></tr>`).join('');
const per=`<!--per100:start-->
  <div class="ar-tw">
  <table class="ar-tab ar-num ar-set">
    <thead><tr><th scope="col">GPU fans</th><th scope="col">rpm</th><th scope="col">&deg;C per 100&nbsp;W, (11)</th><th scope="col">&deg;C per 100&nbsp;W, (10)</th><th scope="col">&deg;C per 100&nbsp;W, (9)</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>
  </div>
  <p class="ar-note">Case fans 1500&nbsp;rpm. Column (11) is the settled-point model of the <a href="#stats">statistical tests</a>, fitted to ${J.n} settled points${tableN?' (provisional)':''}; (10) is the dynamic model; (9) the static fit on mostly 60-second points, which keeps too much of the rise in its offset ${i('\\theta_0')}. The settled points of val1 and later support (10) and (11). Lowering the power limit by 100&nbsp;W cools the core about ${(Rs(1312)/Rs(3012)).toFixed(1)} times as much with the GPU fans at 40&nbsp;% as at 100&nbsp;% by (11).</p>
<!--per100:end-->`;
a=s.indexOf('<!--per100:start-->'); b=s.indexOf('<!--per100:end-->'); if(a<0||b<a) throw 'per100 markers'; s=s.slice(0,a)+per+s.slice(b+'<!--per100:end-->'.length);
fs.writeFileSync(F,s); console.log('written: n',J.n,'ref',J.ref,'choice',J.choice,'table pts',tableN, 'rmse',chosen.rmse,'loo',chosen.LOO);
