/* service-worker.js */
const queue = [];
let busy = false;

self.addEventListener('message', (evt) => {
  const job = evt.data;            // {url, btnId}
  queue.push(job);
  runQueue();
});

async function runQueue() {
  if (busy || queue.length === 0) return;
  busy = true;
  const { url, btnId } = queue.shift();

  try {
    const res  = await fetch(`/download?url=${encodeURIComponent(url)}`);
    if (!res.ok) throw new Error('DL failed');

    const blob = await res.blob();
    const cd   = res.headers.get('Content-Disposition') || '';
    const name = /filename="(.+?)"/i.exec(cd)?.[1] || 'download.mp3';

    // 👉 pipe blob back to page so button state can flip
    self.clients.matchAll().then(clients =>
      clients.forEach(c =>
        c.postMessage({ btnId, status: 'done', blob, name })
      )
    );
  } catch (e) {
    self.clients.matchAll().then(clients =>
      clients.forEach(c =>
        c.postMessage({ btnId, status: 'error', error: e.message })
      )
    );
  } finally {
    busy = false;
    runQueue();
  }
}
