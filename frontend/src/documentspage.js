import './style.css';

document.querySelector('#app').innerHTML = `
  <main class="min-h-screen px-6 py-12">
    <section class="mx-auto max-w-4xl">
      <header class="mb-8 flex items-center justify-between gap-4">
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.3em] text-pacific-blue-400">DocAuditor</p>
          <h1 class="mt-2 text-3xl font-bold tracking-tight text-alabaster-grey-50">Mano dokumentai</h1>
        </div>
        <button id="logout-button" type="button"
          class="rounded-xl border border-charcoal-blue-600 px-4 py-2 text-sm font-semibold text-alabaster-grey-50 transition hover:border-pacific-blue-400">
          Atsijungti
        </button>
      </header>
      <div class="rounded-2xl border border-charcoal-blue-700/80 bg-charcoal-blue-950/70 p-6 shadow-2xl shadow-black/20">
        <p id="documents-status" class="text-sm text-powder-blue-400" aria-live="polite">Kraunama...</p>
        <ul id="documents-list" class="divide-y divide-charcoal-blue-700/80"></ul>
      </div>
    </section>
  </main>
`;

const status = document.querySelector('#documents-status');
const list = document.querySelector('#documents-list');

function renderDocuments(documents) {
  list.replaceChildren();
  status.textContent = documents.length ? '' : 'Dokumentų dar nėra.';
  for (const document_ of documents) {
    const item = document.createElement('li');
    item.className = 'flex items-center justify-between gap-4 py-3 text-sm';
    const title = document.createElement('span');
    title.className = 'font-medium text-alabaster-grey-50';
    title.textContent = document_.original_filename;
    const date = document.createElement('span');
    date.className = 'text-powder-blue-400';
    date.textContent = new Date(document_.created_at).toLocaleDateString('lt-LT');
    item.append(title, date);
    list.append(item);
  }
}

async function loadDocuments() {
  try {
    const response = await fetch('/api/documents/', { credentials: 'same-origin' });
    if (response.status === 401) {
      window.location.replace('/login');
      return;
    }
    if (!response.ok) throw new Error('Request failed');
    renderDocuments((await response.json()).documents);
  } catch {
    status.textContent = 'Nepavyko įkelti dokumentų sąrašo.';
  }
}

document.querySelector('#logout-button').addEventListener('click', async () => {
  try {
    await fetch('/api/auth/logout/', { method: 'POST', credentials: 'same-origin' });
  } finally {
    window.location.replace('/login');
  }
});

loadDocuments();
