import { mkdir, readFile, writeFile } from 'node:fs/promises';
const html = await readFile(new URL('../dist/client/index.html', import.meta.url), 'utf8');
for (const route of ['policy', 'consent']) {
 const folder = new URL(`../dist/client/${route}/`, import.meta.url);
 await mkdir(folder, { recursive: true });
 await writeFile(new URL('index.html', folder), html);
}
console.log('Prepared static /policy/ and /consent/ routes');
