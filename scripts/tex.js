// Render TeX strings (JSON array on stdin) to KaTeX HTML (JSON array on stdout). Display mode when the string starts with "$$".
const katex = require('katex'); let inp = ''; process.stdin.on('data', d => inp += d).on('end', () => {
  const a = JSON.parse(inp); console.log(JSON.stringify(a.map(t => t.startsWith('$$') ? katex.renderToString(t.slice(2), {displayMode: true, output: 'htmlAndMathml', strict: false}) : katex.renderToString(t, {output: 'htmlAndMathml', strict: false}))));
});
