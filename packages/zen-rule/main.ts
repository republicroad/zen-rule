import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { ZenRule, registerUdf, udfManager } from './src/index.js';
import data  from './custom.json' with { type: "json" }
import data2  from './custom_fullnode.json' with { type: "json" }
// console.log('data:', data);

// Register a UDF similar to the `foo` in main.py
registerUdf('foo', undefined, {
  parameters: {
    a: { type: 'string', description: '参数 a' },
    b: { type: 'string', description: '参数 b' },
    c: { type: 'string', description: '参数 c' },
  },
  returns: { type: 'string', description: 'foo 函数返回' },
})(function foo(kwargs: Record<string, unknown>) {
  console.log('function: foo args:', JSON.stringify(Object.keys(kwargs)));
  console.log('function: foo kwargs:', kwargs);
  return 'foo value';
});

async function testZenruleFoo() {
  const zr = new ZenRule({});
  if (import.meta.url.startsWith('file:///$bunfs/root')) {
    const executionDirectory = process.execPath.split('/').slice(0, -1).join('/'); 
    // const __dirname = dirname(fileURLToPath(import.meta.url));
    // const __dirname = process.cwd();
    // const filename = resolve(__dirname, '../../graph/custom_fullnode.json');
    // const filename = resolve(__dirname, 'custom_fullnode.json');
    var filename = resolve(executionDirectory, 'custom_fullnode.json');
  }
  else{
    const executionDirectory = import.meta.dir;
    // const __dirname = dirname(fileURLToPath(import.meta.url));
    // const __dirname = process.cwd();
    // console.log('__dirname:', __dirname);
    // const filename = resolve(__dirname, '../../graph/custom.json');
    var filename = resolve(executionDirectory, 'custom_fullnode.json');
    // const filename = resolve(__dirname, 'custom.json');
  }
  const key = filename;
  if (!zr.getDecisionCache(key)) {
    const content = readFileSync(filename, 'utf-8');
    zr.createDecisionWithCacheKey(key, content);
  }
  for (let i = 0; i < 1; i++) {
    const result = await zr.evaluateAsync(key, { input: 7, myvar: 15 });
    console.log('zen rule custom result:', JSON.stringify(result, null, 2));
    const resultValue = (result as any)?.result?.result;
    if (resultValue !== 'foo value') {
      throw new Error(`custom rule execution failed, got: ${resultValue}`);
    }
    console.log(`------------------${i}------------------------`);
  }
}

async function testZenrule() {
  const zr = new ZenRule({});
  // Returns the full absolute path of the binary (e.g., /usr/local/bin/myapp)
  const executablePath = process.execPath; 
  // Returns the true physical directory containing the binary
  const executionDirectory = process.execPath.split('/').slice(0, -1).join('/'); 
  console.log('executionDirectory:', executionDirectory);
  console.log('executablePath:', executablePath);
  console.log('import.meta.url:', import.meta.url);
  console.log('import.meta.path:', import.meta.path);
  console.log('import.meta.dir:', import.meta.dir);
  console.log('process.cwd():', process.cwd());
  if (import.meta.url.startsWith('file:///$bunfs/root')) {
    const executionDirectory = process.execPath.split('/').slice(0, -1).join('/'); 
    // const __dirname = dirname(fileURLToPath(import.meta.url));
    // const __dirname = process.cwd();
    // const filename = resolve(__dirname, '../../graph/custom_fullnode.json');
    // const filename = resolve(__dirname, 'custom_fullnode.json');
    var filename = resolve(executionDirectory, 'custom.json');
  }
  else{
    const executionDirectory = import.meta.dir;
    // const __dirname = dirname(fileURLToPath(import.meta.url));
    // const __dirname = process.cwd();
    // console.log('__dirname:', __dirname);
    // const filename = resolve(__dirname, '../../graph/custom.json');
    var filename = resolve(executionDirectory, 'custom.json');
    // const filename = resolve(__dirname, 'custom.json');
  }
  const key = filename;
  if (!zr.getDecisionCache(key)) {
    const content = readFileSync(filename, 'utf-8');
    zr.createDecisionWithCacheKey(key, content);
  }
  for (let i = 0; i < 1; i++) {
    const result = await zr.evaluateAsync(key, { input: 7, myvar: 15 });
    console.log('zen rule custom result:', JSON.stringify(result, null, 2));
    console.log(`------------------${i}------------------------`);
  }
}

async function main() {
  console.log('\n=== test_zenrule ===');
  await testZenrule();
  console.log('=== test_zenrule_foo ===');
  await testZenruleFoo();
}

main().catch(console.error);

// import.meta.url 在 bun compile 中是 file:///$bunfs/root/xxx.exe 路径.