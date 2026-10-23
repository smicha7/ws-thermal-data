const katex=require('katex'),fs=require('fs'); const F='/Users/smicha/Claude/gruency-site/research/gpu-cooling-method.html'; let s=fs.readFileSync(F,'utf8');
const i=t=>katex.renderToString(t,{throwOnError:true});
s=s.replace('The settled points of all sessions give the time constant directly: each was fitted with ${tau}.','The settled points of all sessions give the time constant directly, from the exponential fitted to the last minutes of each point.');
s=s.split('${tau}').join(i('\\tau')); s=s.split('${dT}').join(i('\\Delta T'));
s=s.split('${tset}').join(i('t \\approx \\tau \\ln(\\Delta T / 0.1\\ {}^\\circ\\mathrm{C})'));
fs.writeFileSync(F,s); console.log((s.match(/\$\{/g)||[]).length);
