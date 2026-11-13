import './style.css';
import { initializeThemeToggle } from './theme.js';

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
        <p id="documents-message" class="mb-2 min-h-5 text-sm font-medium" aria-live="polite"></p>
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
          <div class="flex items-center gap-2">
            <button id="preview-delete-button" type="button" class="rounded-xl border border-rose-400/70 px-4 py-2 text-sm font-semibold text-rose-300 transition hover:border-rose-300 focus:outline-none focus:ring-2 focus:ring-rose-300">
              Ištrinti
            </button>
            <button id="analyze-button" type="button" class="rounded-xl bg-pacific-blue-500 px-4 py-2 text-sm font-semibold text-carbon-black-950 disabled:opacity-50">
              Analizuoti
            </button>
            <button id="ask-document-button" type="button" class="rounded-xl bg-pacific-blue-500 px-4 py-2 text-sm font-semibold text-carbon-black-950 transition hover:bg-pacific-blue-400 focus:outline-none focus:ring-2 focus:ring-pacific-blue-300">
              Paklausk apie dokumentą
            </button>
            <button id="compare-documents-button" type="button" class="rounded-xl border border-pacific-blue-400 px-4 py-2 text-sm font-semibold text-pacific-blue-300 transition hover:bg-pacific-blue-400/10">
              Palyginti
            </button>
            <button id="close-preview-button" type="button" class="rounded-xl border border-charcoal-blue-600 px-4 py-2 text-sm font-semibold text-alabaster-grey-50 transition hover:border-pacific-blue-400 focus:outline-none focus:ring-2 focus:ring-pacific-blue-400">
              Uždaryti
            </button>
          </div>
          <div id="chat-dialog" class="fixed inset-0 z-30 hidden items-center justify-center bg-carbon-black-950/80 p-4" role="dialog" aria-modal="true" aria-labelledby="chat-title">
            <section class="flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-charcoal-blue-700/80 bg-charcoal-blue-950 shadow-2xl">
              <header class="flex items-center justify-between gap-4 border-b border-charcoal-blue-700/80 px-5 py-4">
                <div class="min-w-0">
                  <h2 id="chat-title" class="truncate text-lg font-semibold text-alabaster-grey-50">Klausti apie dokumentą</h2>
                  <p id="chat-document-name" class="truncate text-sm text-powder-blue-400"></p>
                </div>
                <button id="close-chat-button" type="button" class="rounded-xl border border-charcoal-blue-600 px-4 py-2 text-sm font-semibold text-alabaster-grey-50 transition hover:border-pacific-blue-400">
                  Uždaryti
                </button>
              </header>
              <div id="chat-messages" class="min-h-48 flex-1 space-y-3 overflow-y-auto p-5" aria-live="polite">
                <p id="chat-empty" class="text-sm text-powder-blue-400">Parašykite klausimą apie pasirinkto dokumento sąlygas.</p>
              </div>
              <form id="chat-form" class="border-t border-charcoal-blue-700/80 p-5">
                <label for="chat-input" class="sr-only">Jūsų klausimas</label>
                <textarea id="chat-input" rows="2" maxlength="2000" placeholder="Įrašykite klausimą ir paspauskite Enter..." class="w-full resize-none rounded-xl border border-charcoal-blue-600 bg-carbon-black-950 px-4 py-3 text-sm text-alabaster-grey-50 outline-none transition placeholder:text-charcoal-blue-400 focus:border-pacific-blue-400 focus:ring-2 focus:ring-pacific-blue-400/20"></textarea>
                <p id="chat-message" class="mt-2 min-h-5 text-sm font-medium" aria-live="polite"></p>
              </form>
            </section>
          </div>
        </header>
        <div class="max-h-52 overflow-y-auto border-b border-charcoal-blue-700/80 px-5 py-3 text-sm text-powder-blue-300">
          <p id="analysis-status" class="mt-2" aria-live="polite"></p>
          <p id="analysis-summary" class="mt-2 whitespace-pre-wrap text-alabaster-grey-50"></p>
          <a id="analysis-download" class="mt-2 hidden font-semibold text-pacific-blue-300" download>Gauti santrauką</a>
        </div>
        <p id="preview-status" class="hidden px-5 py-4 text-sm text-powder-blue-400" aria-live="polite"></p>
        <iframe id="preview-frame" title="Dokumento turinio peržiūra" class="hidden min-h-0 flex-1 bg-white"></iframe>
        <div id="preview-download" class="hidden px-5 pb-5 text-sm text-powder-blue-400">
          <a id="preview-download-link" class="font-semibold text-pacific-blue-300 hover:text-pacific-blue-200" download>Atsisiųsti dokumentą</a>
        </div>
      </section>
    </div>
    <div id="comparison-dialog" class="fixed inset-0 z-30 hidden items-center justify-center bg-carbon-black-950/80 p-4" role="dialog" aria-modal="true" aria-labelledby="comparison-title">
      <section class="w-full max-w-3xl rounded-2xl border border-charcoal-blue-700/80 bg-charcoal-blue-950 p-6 shadow-2xl">
        <header class="flex items-center justify-between gap-4">
          <h2 id="comparison-title" class="text-lg font-semibold text-alabaster-grey-50">Palyginti dokumento versijas</h2>
          <button id="close-comparison-button" type="button" class="rounded-xl border border-charcoal-blue-600 px-4 py-2 text-sm font-semibold text-alabaster-grey-50 transition hover:border-pacific-blue-400">Uždaryti</button>
        </header>
        <div class="mt-5 grid gap-4 sm:grid-cols-2">
          <label class="text-sm text-powder-blue-300">Pirma versija
            <select id="first-version-select" class="mt-2 w-full rounded-xl border border-charcoal-blue-600 bg-carbon-black-950 px-3 py-3 text-sm text-alabaster-grey-50 outline-none focus:border-pacific-blue-400"></select>
          </label>
          <label class="text-sm text-powder-blue-300">Antra versija
            <select id="second-version-select" class="mt-2 w-full rounded-xl border border-charcoal-blue-600 bg-carbon-black-950 px-3 py-3 text-sm text-alabaster-grey-50 outline-none focus:border-pacific-blue-400"></select>
          </label>
        </div>
        <p id="comparison-message" class="mt-4 min-h-5 text-sm font-medium" aria-live="polite"></p>
        <button id="run-comparison-button" type="button" class="mt-2 rounded-xl bg-pacific-blue-500 px-5 py-2 text-sm font-semibold text-carbon-black-950 transition hover:bg-pacific-blue-400 disabled:cursor-not-allowed disabled:opacity-50">Palyginti</button>
        <div id="comparison-report" class="mt-5 hidden max-h-96 overflow-y-auto rounded-xl border border-charcoal-blue-700 bg-charcoal-blue-900/50 p-4 text-sm leading-6 text-powder-blue-200 whitespace-pre-wrap"></div>
        <div id="comparison-download-container" class="mt-4"></div>
      </section>
    </div>
    <div id="delete-dialog" class="fixed inset-0 z-20 hidden items-center justify-center bg-carbon-black-950/80 p-4" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title" aria-describedby="delete-dialog-message">
      <section class="w-full max-w-md rounded-2xl border border-charcoal-blue-700/80 bg-charcoal-blue-950 p-6 shadow-2xl shadow-black/40">
        <div class="flex items-start gap-4">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-rose-400/10 text-rose-300" aria-hidden="true">
            <span class="text-xl">!</span>
          </div>
          <div>
            <h2 id="delete-dialog-title" class="text-lg font-semibold text-alabaster-grey-50">Ištrinti dokumentą?</h2>
            <p id="delete-dialog-message" class="mt-2 text-sm leading-6 text-powder-blue-300">Ar tikrai norite ištrinti?</p>
          </div>
        </div>
        <div class="mt-6 flex justify-end gap-3">
          <button id="cancel-delete-button" type="button" class="rounded-xl border border-charcoal-blue-600 px-4 py-2 text-sm font-semibold text-alabaster-grey-50 transition hover:border-pacific-blue-400 focus:outline-none focus:ring-2 focus:ring-pacific-blue-400">
            Atšaukti
          </button>
          <button id="confirm-delete-button" type="button" class="rounded-xl bg-rose-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-400 focus:outline-none focus:ring-2 focus:ring-rose-300">
            Patvirtinti
          </button>
        </div>
      </section>
    </div>
  </main>
`;

initializeThemeToggle();

const status = document.querySelector('#documents-status');
const documentsMessage = document.querySelector('#documents-message');
const list = document.querySelector('#documents-list');
const previewDialog = document.querySelector('#preview-dialog');
const previewTitle = document.querySelector('#preview-title');
const previewDate = document.querySelector('#preview-date');
const previewStatus = document.querySelector('#preview-status');
const previewFrame = document.querySelector('#preview-frame');
const previewDownload = document.querySelector('#preview-download');
const previewDownloadLink = document.querySelector('#preview-download-link');
const previewDeleteButton = document.querySelector('#preview-delete-button');
const analyzeButton = document.querySelector('#analyze-button');
const analysisStatus = document.querySelector('#analysis-status');
const analysisSummary = document.querySelector('#analysis-summary');
const analysisDownload = document.querySelector('#analysis-download');
const analyzingDocuments = new Set();
const askDocumentButton = document.querySelector('#ask-document-button');
const compareDocumentsButton = document.querySelector('#compare-documents-button');
const chatDialog = document.querySelector('#chat-dialog');
const closeChatButton = document.querySelector('#close-chat-button');
const chatDocumentName = document.querySelector('#chat-document-name');
const chatMessages = document.querySelector('#chat-messages');
const chatEmpty = document.querySelector('#chat-empty');
const chatForm = document.querySelector('#chat-form');
const chatInput = document.querySelector('#chat-input');
const chatMessage = document.querySelector('#chat-message');
const comparisonDialog = document.querySelector('#comparison-dialog');
const closeComparisonButton = document.querySelector('#close-comparison-button');
const firstVersionSelect = document.querySelector('#first-version-select');
const secondVersionSelect = document.querySelector('#second-version-select');
const comparisonMessage = document.querySelector('#comparison-message');
const runComparisonButton = document.querySelector('#run-comparison-button');
const comparisonReport = document.querySelector('#comparison-report');
const comparisonDownloadContainer = document.querySelector('#comparison-download-container');
const deleteDialog = document.querySelector('#delete-dialog');
const cancelDeleteButton = document.querySelector('#cancel-delete-button');
const confirmDeleteButton = document.querySelector('#confirm-delete-button');
let previewObjectUrl = '';
let previewDocument = null;
let pendingDeleteDocument = null;
let chatDocument = null;
let comparisonObjectUrl = '';
const DELETE_SUCCESS = 'Dokumentas sėkmingai ištrintas';
const DELETE_FAILED = 'Klaida: nepavyko ištrinti dokumento';

function showDocumentsMessage(text, colorClass) {
  documentsMessage.textContent = text;
  documentsMessage.className = `mb-2 min-h-5 text-sm font-medium ${colorClass}`;
}

function closePreview() {
  previewDialog.classList.add('hidden');
  previewFrame.src = '';
  if (previewObjectUrl) {
    URL.revokeObjectURL(previewObjectUrl);
    previewObjectUrl = '';
  }
  previewDocument = null;
}

function openChat() {
  if (!previewDocument) return;
  chatDocument = previewDocument;
  chatDocumentName.textContent = previewDocument.original_filename;
  chatDialog.classList.remove('hidden');
  chatDialog.classList.add('flex');
  chatInput.focus();
}

function closeChat() {
  chatDialog.classList.add('hidden');
  chatDialog.classList.remove('flex');
  chatDocument = null;
}

function addChatMessage(text, sender) {
  chatEmpty.classList.add('hidden');
  const message = document.createElement('p');
  message.className = sender === 'user'
    ? 'ml-auto max-w-[85%] rounded-xl bg-pacific-blue-500 px-4 py-3 text-sm text-carbon-black-950'
    : 'max-w-[85%] rounded-xl bg-charcoal-blue-800 px-4 py-3 text-sm text-alabaster-grey-50';
  message.textContent = text;
  chatMessages.append(message);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function openComparison() {
  if (!previewDocument) return;
  const versions = currentDocuments.filter(({ title }) => title === previewDocument.title);
  firstVersionSelect.replaceChildren();
  secondVersionSelect.replaceChildren();
  for (const version of versions) {
    const label = `${version.original_filename} · ${new Date(version.created_at).toLocaleString('lt-LT')}`;
    firstVersionSelect.add(new Option(label, version.id));
    secondVersionSelect.add(new Option(label, version.id));
  }
  comparisonMessage.textContent = versions.length < 2 ? 'Nepasirinkti dokumentai palyginimui' : '';
  comparisonMessage.className = 'mt-4 min-h-5 text-sm font-medium text-rose-300';
  comparisonReport.classList.add('hidden');
  comparisonDownloadContainer.replaceChildren();
  if (comparisonObjectUrl) {
    URL.revokeObjectURL(comparisonObjectUrl);
    comparisonObjectUrl = '';
  }
  comparisonDialog.classList.remove('hidden');
  comparisonDialog.classList.add('flex');
}

function closeComparison() {
  comparisonDialog.classList.add('hidden');
  comparisonDialog.classList.remove('flex');
  if (comparisonObjectUrl) {
    URL.revokeObjectURL(comparisonObjectUrl);
    comparisonObjectUrl = '';
  }
}

async function openDocumentPreview(document_) {
  previewDocument = document_;
  renderAnalysis(document_);
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

function renderAnalysis(document_) {
  const analyzing = analyzingDocuments.has(document_.id);
  analyzeButton.disabled = analyzing;
  analysisStatus.textContent = analyzing ? 'Dokumentas analizuojamas...' : '';
  analysisSummary.textContent = document_.simplified_explanation || '';
  analysisDownload.classList.toggle('hidden', !document_.simplified_explanation);
  analysisDownload.href = `/api/documents/${document_.id}/summary.pdf`;
}

analyzeButton.addEventListener('click', async () => {
  const document_ = previewDocument;
  if (!document_ || analyzingDocuments.has(document_.id)) return;
  analyzingDocuments.add(document_.id);
  renderAnalysis(document_);
  try {
    const response = await fetch(`/api/documents/${document_.id}/analysis/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': await getCsrfToken() },
      credentials: 'same-origin',
    });
    if (response.status === 401) {
      window.location.replace('/login');
      return;
    }
    if (!response.ok) throw new Error('Analysis request failed');
    const result = await response.json();
    document_.simplified_explanation = result.summary;
    if (previewDocument?.id === document_.id) analysisSummary.textContent = result.summary;
  } catch {
    if (previewDocument?.id === document_.id) analysisStatus.textContent = 'Analizė nepavyko, bandykite dar kartą';
  } finally {
    analyzingDocuments.delete(document_.id);
    if (previewDocument?.id === document_.id) {
      analyzeButton.disabled = false;
      if (analysisStatus.textContent === 'Dokumentas analizuojamas...') analysisStatus.textContent = '';
      analysisDownload.classList.toggle('hidden', !document_.simplified_explanation);
    }
  }
});

function renderDocuments(documents) {
  currentDocuments = documents;
  list.replaceChildren();
  status.textContent = documents.length ? '' : 'Nėra įkeltų dokumentų.';
  for (const document_ of documents) {
    const item = document.createElement('li');
    item.className = 'border-b border-charcoal-blue-700/80 last:border-b-0';
    const contentButton = document.createElement('button');
    contentButton.type = 'button';
    contentButton.dataset.documentId = document_.id;
    contentButton.className = 'min-w-0 flex-1 rounded-xl px-3 py-3 text-left text-sm transition hover:bg-charcoal-blue-800/60 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-pacific-blue-400 flex flex-col gap-1';
    const title = document.createElement('span');
    title.className = 'font-medium text-alabaster-grey-50';
    title.textContent = document_.original_filename;
    const date = document.createElement('span');
    date.className = 'text-powder-blue-400';
    date.textContent = new Date(document_.created_at).toLocaleDateString('lt-LT');
    contentButton.append(title, date);
    const deleteButton = document.createElement('button');
    deleteButton.type = 'button';
    deleteButton.dataset.deleteDocumentId = document_.id;
    deleteButton.className = 'shrink-0 rounded-xl border border-rose-400/70 px-3 py-2 text-xs font-semibold text-rose-300 transition hover:border-rose-300 focus:outline-none focus:ring-2 focus:ring-rose-300';
    deleteButton.textContent = 'Ištrinti';
    const row = document.createElement('div');
    row.className = 'flex items-center gap-2';
    row.append(contentButton, deleteButton);
    item.append(row);
    list.append(item);
  }
}

list.addEventListener('click', (event) => {
  const deleteButton = event.target.closest('button[data-delete-document-id]');
  if (deleteButton) {
    const document_ = currentDocuments.find(({ id }) => String(id) === deleteButton.dataset.deleteDocumentId);
    if (document_) deleteDocument(document_);
    return;
  }
  const button = event.target.closest('button[data-document-id]');
  if (!button) return;
  const document_ = currentDocuments.find(({ id }) => String(id) === button.dataset.documentId);
  if (document_) openDocumentPreview(document_);
});

async function deleteDocument(document_) {
  pendingDeleteDocument = document_;
  deleteDialog.classList.remove('hidden');
  deleteDialog.classList.add('flex');
  cancelDeleteButton.focus();
}

function closeDeleteDialog() {
  deleteDialog.classList.add('hidden');
  deleteDialog.classList.remove('flex');
  pendingDeleteDocument = null;
}

async function confirmDelete() {
  const document_ = pendingDeleteDocument;
  if (!document_) return;
  closeDeleteDialog();

  try {
    const response = await fetch(`/api/documents/${document_.id}/`, {
      method: 'DELETE',
      headers: { 'X-CSRFToken': await getCsrfToken() },
      credentials: 'same-origin',
    });
    if (response.status === 401) {
      window.location.replace('/login');
      return;
    }
    if (!response.ok) throw new Error('Delete request failed');
    if (previewDocument?.id === document_.id) closePreview();
    showDocumentsMessage(DELETE_SUCCESS, 'text-emerald-300');
    await loadDocuments();
  } catch {
    showDocumentsMessage(DELETE_FAILED, 'text-rose-300');
  }
}

document.querySelector('#close-preview-button').addEventListener('click', closePreview);
previewDeleteButton.addEventListener('click', () => {
  if (previewDocument) deleteDocument(previewDocument);
});
askDocumentButton.addEventListener('click', openChat);
compareDocumentsButton.addEventListener('click', openComparison);
closeComparisonButton.addEventListener('click', closeComparison);
comparisonDialog.addEventListener('click', (event) => {
  if (event.target === comparisonDialog) closeComparison();
});
closeChatButton.addEventListener('click', closeChat);
chatDialog.addEventListener('click', (event) => {
  if (event.target === chatDialog) closeChat();
});
cancelDeleteButton.addEventListener('click', closeDeleteDialog);
confirmDeleteButton.addEventListener('click', confirmDelete);
previewDialog.addEventListener('click', (event) => {
  if (event.target === previewDialog) closePreview();
});
deleteDialog.addEventListener('click', (event) => {
  if (event.target === deleteDialog) closeDeleteDialog();
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && !previewDialog.classList.contains('hidden')) closePreview();
  if (event.key === 'Escape' && !deleteDialog.classList.contains('hidden')) closeDeleteDialog();
  if (event.key === 'Escape' && !chatDialog.classList.contains('hidden')) closeChat();
  if (event.key === 'Escape' && !comparisonDialog.classList.contains('hidden')) closeComparison();
});

runComparisonButton.addEventListener('click', async () => {
  if (!firstVersionSelect.value || !secondVersionSelect.value || firstVersionSelect.value === secondVersionSelect.value) {
    comparisonMessage.textContent = 'Nepasirinkti dokumentai palyginimui';
    comparisonMessage.className = 'mt-4 min-h-5 text-sm font-medium text-rose-300';
    return;
  }
  runComparisonButton.disabled = true;
  comparisonMessage.textContent = 'Lyginama';
  comparisonMessage.className = 'mt-4 min-h-5 text-sm font-medium text-powder-blue-400';
  comparisonReport.classList.add('hidden');
  comparisonDownloadContainer.replaceChildren();
  try {
    const response = await fetch('/api/documents/compare/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': await getCsrfToken(),
      },
      credentials: 'same-origin',
      body: JSON.stringify({
        first_document_id: Number(firstVersionSelect.value),
        second_document_id: Number(secondVersionSelect.value),
      }),
    });
    if (response.status === 401) {
      window.location.replace('/login');
      return;
    }
    if (!response.ok) throw new Error('Comparison request failed');
    const result = await response.json();
    comparisonReport.textContent = result.report;
    comparisonReport.classList.remove('hidden');
    const pdfBytes = Uint8Array.from(atob(result.pdf_base64), (character) => character.charCodeAt(0));
    comparisonObjectUrl = URL.createObjectURL(new Blob([pdfBytes], { type: 'application/pdf' }));
    const comparisonDownloadLink = document.createElement('a');
    comparisonDownloadLink.id = 'comparison-download-link';
    comparisonDownloadLink.className = 'inline-block rounded-xl border border-pacific-blue-400 px-4 py-2 text-sm font-semibold text-pacific-blue-300 hover:bg-pacific-blue-400/10';
    comparisonDownloadLink.textContent = 'Atsisiųsti ataskaitą';
    comparisonDownloadLink.href = comparisonObjectUrl;
    comparisonDownloadLink.download = result.pdf_filename;
    comparisonDownloadContainer.append(comparisonDownloadLink);
    comparisonMessage.textContent = '';
  } catch {
    comparisonMessage.textContent = 'Dokumentų palyginti nepavyko';
    comparisonMessage.className = 'mt-4 min-h-5 text-sm font-medium text-rose-300';
  } finally {
    runComparisonButton.disabled = false;
  }
});

chatForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const question = chatInput.value.trim();
  if (!question || !chatDocument) return;
  addChatMessage(question, 'user');
  chatInput.value = '';
  chatInput.disabled = true;
  chatMessage.textContent = 'Ruošiamas atsakymas...';
  chatMessage.className = 'mt-2 min-h-5 text-sm font-medium text-powder-blue-400';
  try {
    const response = await fetch(`/api/documents/${chatDocument.id}/chat/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': await getCsrfToken(),
      },
      credentials: 'same-origin',
      body: JSON.stringify({ question }),
    });
    if (response.status === 401) {
      window.location.replace('/login');
      return;
    }
    if (!response.ok) throw new Error('Chat request failed');
    addChatMessage((await response.json()).answer, 'assistant');
    chatMessage.textContent = '';
  } catch {
    chatMessage.textContent = 'Nepavyko sukurti pokalbio.';
    chatMessage.className = 'mt-2 min-h-5 text-sm font-medium text-rose-300';
  } finally {
    chatInput.disabled = false;
    chatInput.focus();
  }
});

chatInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
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
