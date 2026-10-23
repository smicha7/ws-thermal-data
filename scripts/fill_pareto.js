const katex=require('katex'),fs=require('fs'); const F='/Users/smicha/Claude/gruency-site/research/gpu-cooling-method.html'; let s=fs.readFileSync(F,'utf8');
const i=t=>katex.renderToString(t,{throwOnError:true});
s=s.split('${Lc}$').join(i('L_c = a + b\\log_{10} N_c')).split('${Lg}$').join(i('L_g = 32.5 + 50\\log_{10}(N/1570)'));
fs.writeFileSync(F,s); console.log((s.match(/\$\{L[cg]\}\$/g)||[]).length);
