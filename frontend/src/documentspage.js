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
      <div class="mb-6 rounded-2xl border border-charcoal-blue-700/80 bg-charcoal-blue-950/70 p-6 shadow-2xl shadow-black/20">
        <h2 class="text-lg font-semibold text-alabaster-grey-50">Įkelti dokumentą</h2>
        <form id="upload-form" novalidate class="mt-4">
          <input id="file-input" name="file" type="file" accept=".pdf,.doc,.docx" class="hidden" />
          <div class="flex flex-wrap items-center gap-3">
            <button id="choose-button" type="button"
              class="rounded-xl border border-charcoal-blue-600 px-4 py-2 text-sm font-semibold text-alabaster-grey-50 transition hover:border-pacific-blue-400">
              Įkelti dokumentą
            </button>
            <span id="file-name" class="text-sm text-powder-blue-400">Failas nepasirinktas</span>
          </div>
          <p class="mt-2 text-xs text-powder-blue-500">Leidžiami PDF, DOC ir DOCX failai iki 15 MB.</p>
          <p id="upload-message" class="mt-3 min-h-5 text-sm font-medium" aria-live="polite"></p>
          <button id="save-button" type="submit"
            class="mt-2 rounded-xl bg-pacific-blue-500 px-5 py-2 text-sm font-semibold text-carbon-black-950 transition hover:bg-pacific-blue-400 disabled:cursor-not-allowed disabled:opacity-50">
            Išsaugoti
          </button>
        </form>
      </div>
      <div class="rounded-2xl border border-charcoal-blue-700/80 bg-charcoal-blue-950/70 p-6 shadow-2xl shadow-black/20">
        <p id="documents-status" class="text-sm text-powder-blue-400" aria-live="polite">Kraunama...</p>
        <ul id="documents-list" class="divide-y divide-charcoal-blue-700/80"></ul>
      </div>
    </section>
    <div id="preview-dialog" class="fixed inset-0 z-10 hidden bg-carbon-black-950/80 p-4 sm:p-8" role="dialog" aria-modal="true" aria-labelledby="preview-title">
      <section class="mx-auto flex h-full max-w-5xl flex-col overflow-hidden rounded-2xl border border-charcoal-blue-700/80 bg-charcoal-blue-950 shadow-2xl">
        <header class="flex items-center justify-between gap-4 border-b border-charcoal-blue-700/80 px-5 py-4">
          <div class="flex min-w-0 items-baseline gap-2">
            <h2 id="preview-title" class="truncate text-lg font-semibold text-alabaster-grey-50">Dokumento peržiūra</h2>
            <span id="preview-date" class="shrink-0 text-sm text-powder-blue-400"></span>
          </div>
          <button id="close-preview-button" type="button" class="rounded-xl border border-charcoal-blue-600 px-4 py-2 text-sm font-semibold text-alabaster-grey-50 transition hover:border-pacific-blue-400 focus:outline-none focus:ring-2 focus:ring-pacific-blue-400">
            Uždaryti
          </button>
        </header>
        <p id="preview-status" class="hidden px-5 py-4 text-sm text-powder-blue-400" aria-live="polite"></p>
        <iframe id="preview-frame" title="Dokumento turinio peržiūra" class="hidden min-h-0 flex-1 bg-white"></iframe>
        <div id="preview-download" class="hidden px-5 pb-5 text-sm text-powder-blue-400">
          <a id="preview-download-link" class="font-semibold text-pacific-blue-300 hover:text-pacific-blue-200" download>Atsisiųsti dokumentą</a>
        </div>
      </section>
    </div>
  </main>
`;

const status = document.querySelector('#documents-status');
const list = document.querySelector('#documents-list');
const previewDialog = document.querySelector('#preview-dialog');
const previewTitle = document.querySelector('#preview-title');
const previewDate = document.querySelector('#preview-date');
const previewStatus = document.querySelector('#preview-status');
const previewFrame = document.querySelector('#preview-frame');
const previewDownload = document.querySelector('#preview-download');
const previewDownloadLink = document.querySelector('#preview-download-link');
let previewObjectUrl = '';

function closePreview() {
  previewDialog.classList.add('hidden');
  previewFrame.src = '';
  if (previewObjectUrl) {
    URL.revokeObjectURL(previewObjectUrl);
    previewObjectUrl = '';
  }
}

async function openDocumentPreview(document_) {
  previewDialog.classList.remove('hidden');
  previewTitle.textContent = document_.original_filename;
  previewDate.textContent = `· Įkelta ${new Date(document_.created_at).toLocaleDateString('lt-LT')}`;
  previewStatus.textContent = 'Kraunama dokumento peržiūra...';
  previewStatus.classList.remove('hidden');
  previewFrame.classList.add('hidden');
  previewDownload.classList.add('hidden');
  if (previewObjectUrl) URL.revokeObjectURL(previewObjectUrl);

  try {
    const response = await fetch(`/api/documents/${document_.id}/preview/`, {
      credentials: 'same-origin',
    });
    if (response.status === 401) {
      window.location.replace('/login');
      return;
    }
    if (!response.ok) throw new Error('Preview request failed');

    const blob = await response.blob();
    previewObjectUrl = URL.createObjectURL(blob);
    previewStatus.textContent = '';
    if (blob.type === 'application/pdf') {
      previewStatus.classList.add('hidden');
      previewFrame.src = previewObjectUrl;
      previewFrame.classList.remove('hidden');
    } else {
      previewStatus.textContent = 'Šio formato peržiūra naršyklėje nepalaikoma.';
      previewDownloadLink.href = previewObjectUrl;
      previewDownloadLink.textContent = `Atsisiųsti ${document_.original_filename}`;
      previewDownload.classList.remove('hidden');
    }
  } catch {
    previewStatus.textContent = 'Įvyko klaida. Dokumento peržiūrėti nepavyko.';
    previewStatus.classList.remove('hidden');
  }
}

function renderDocuments(documents) {
  currentDocuments = documents;
  list.replaceChildren();
  status.textContent = documents.length ? '' : 'Nėra įkeltų dokumentų.';
  for (const document_ of documents) {
    const item = document.createElement('li');
    item.className = 'border-b border-charcoal-blue-700/80 last:border-b-0';
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.documentId = document_.id;
    button.className = 'flex w-full items-center justify-between gap-4 rounded-xl px-3 py-3 text-left text-sm transition hover:bg-charcoal-blue-800/60 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-pacific-blue-400';
    const title = document.createElement('span');
    title.className = 'font-medium text-alabaster-grey-50';
    title.textContent = document_.original_filename;
    const date = document.createElement('span');
    date.className = 'text-powder-blue-400';
    date.textContent = new Date(document_.created_at).toLocaleDateString('lt-LT');
    button.append(title, date);
    item.append(button);
    list.append(item);
  }
}

list.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-document-id]');
  if (!button) return;
  const document_ = currentDocuments.find(({ id }) => String(id) === button.dataset.documentId);
  if (document_) openDocumentPreview(document_);
});

document.querySelector('#close-preview-button').addEventListener('click', closePreview);
previewDialog.addEventListener('click', (event) => {
  if (event.target === previewDialog) closePreview();
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && !previewDialog.classList.contains('hidden')) closePreview();
});

let currentDocuments = [];

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

const uploadForm = document.querySelector('#upload-form');
const fileInput = document.querySelector('#file-input');
const fileName = document.querySelector('#file-name');
const uploadMessage = document.querySelector('#upload-message');
const saveButton = document.querySelector('#save-button');
const ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx'];
const MAX_FILE_SIZE = 15 * 1024 * 1024;
const UPLOAD_FAILED = 'Nepavyko įkelti dokumento';

function showUploadMessage(text, colorClass) {
  uploadMessage.textContent = text;
  uploadMessage.className = `mt-3 min-h-5 text-sm font-medium ${colorClass}`;
}

function validateFile(file) {
  const name = file.name.toLowerCase();
  if (!ALLOWED_EXTENSIONS.some((extension) => name.endsWith(extension))) {
    return 'Leidžiami tik PDF, DOC ir DOCX failai.';
  }
  if (file.size > MAX_FILE_SIZE) return 'Dokumento dydis negali viršyti 15 MB.';
  return null;
}

function getCookie(name) {
  const match = document.cookie.split('; ').find((cookie) => cookie.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.slice(name.length + 1)) : '';
}

async function getCsrfToken() {
  await fetch('/api/auth/csrf/', { credentials: 'same-origin' });
  return getCookie('csrftoken');
}

document.querySelector('#choose-button').addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', () => {
  const file = fileInput.files[0];
  uploadMessage.textContent = '';
  if (!file) {
    fileName.textContent = 'Failas nepasirinktas';
    return;
  }
  fileName.textContent = file.name;
  const problem = validateFile(file);
  if (problem) {
    fileInput.value = '';
    fileName.textContent = 'Failas nepasirinktas';
    showUploadMessage(problem, 'text-rose-300');
  }
});

uploadForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const file = fileInput.files[0];
  if (!file) {
    showUploadMessage('Pirmiausia pasirinkite dokumentą.', 'text-amber-300');
    return;
  }
  const problem = validateFile(file);
  if (problem) {
    showUploadMessage(problem, 'text-rose-300');
    return;
  }

  saveButton.disabled = true;
  saveButton.textContent = 'Saugoma...';
  try {
    const body = new FormData();
    body.append('file', file);
    const response = await fetch('/api/documents/', {
      method: 'POST',
      headers: { 'X-CSRFToken': await getCsrfToken() },
      credentials: 'same-origin',
      body,
    });
    if (response.status === 401) {
      window.location.replace('/login');
      return;
    }
    if (!response.ok) {
      showUploadMessage(UPLOAD_FAILED, 'text-rose-300');
      return;
    }
    showUploadMessage('Dokumentas išsaugotas sėkmingai', 'text-emerald-300');
    uploadForm.reset();
    fileName.textContent = 'Failas nepasirinktas';
    await loadDocuments();
  } catch {
    showUploadMessage(UPLOAD_FAILED, 'text-rose-300');
  } finally {
    saveButton.disabled = false;
    saveButton.textContent = 'Išsaugoti';
  }
});

document.querySelector('#logout-button').addEventListener('click', async () => {
  try {
    await fetch('/api/auth/logout/', {
      method: 'POST',
      headers: { 'X-CSRFToken': await getCsrfToken() },
      credentials: 'same-origin',
    });
  } finally {
    window.location.replace('/login');
  }
});

loadDocuments();
