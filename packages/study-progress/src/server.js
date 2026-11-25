import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { summarizeProgress } from './index.js';

const { version } = JSON.parse(readFileSync(new URL('../package.json', import.meta.url)));

export function createApp() {
  return createServer((req, res) => {
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    try {
      const url = new URL(req.url, 'http://localhost');
      if (req.method !== 'GET') {
        res.writeHead(405, { Allow: 'GET' });
        return res.end(JSON.stringify({ error: 'Method not allowed' }));
      }
      if (url.pathname === '/health') {
        return res.end(JSON.stringify({ status: 'ok', version }));
      }
      if (url.pathname === '/progress') {
        const completed = url.searchParams.get('completed');
        const total = url.searchParams.get('total');
        if (completed === null || total === null ||
            !/^\d+$/.test(completed) || !/^\d+$/.test(total)) {
          throw new RangeError('completed and total must be nonnegative integers.');
        }
        return res.end(JSON.stringify(summarizeProgress(Number(completed), Number(total))));
      }
      res.writeHead(404);
      res.end(JSON.stringify({ error: 'Not found' }));
    } catch (error) {
      res.writeHead(400);
      res.end(JSON.stringify({ error: error.message }));
    }
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const port = Number(process.env.PORT || 3000);
  const server = createApp();
  server.listen(port, '0.0.0.0', () => console.log(`Study progress ${version} listening on ${port}`));
  process.on('SIGTERM', () => server.close());
  process.on('SIGINT', () => server.close());
}
