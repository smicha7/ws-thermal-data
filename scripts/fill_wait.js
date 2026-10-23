const katex=require('katex'),fs=require('fs'); const F='/Users/smicha/Claude/gruency-site/research/gpu-cooling-method.html'; let s=fs.readFileSync(F,'utf8');
const i=t=>katex.renderToString(t,{throwOnError:true});
const M={'$$dT$$':i('\\Delta T'),'$$s0$$':i('60\\,|\\Delta T|/\\tau'),'$$decay$$':i('e^{-t/\\tau}'),'$$tw$$':i('t \\approx \\tau \\ln\\frac{60\\,|\\Delta T|}{0.1\\,\\tau}'),'$$tau$$':i('\\tau')};
for(const [k,v] of Object.entries(M)) s=s.split(k).join(v);
fs.writeFileSync(F,s); console.log('left', (s.match(/\$\$[a-z0-9]+\$\$/g)||[]).length);
