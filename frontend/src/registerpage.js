import './style.css';
import { initializeThemeToggle } from './theme.js';

document.querySelector('#app').innerHTML = `
  <main class="flex min-h-screen items-center justify-center px-6 py-12">
    <section class="w-full max-w-lg">
      <div class="mb-8 text-center">
        <a href="/" class="text-sm font-semibold uppercase tracking-[0.3em] text-pacific-blue-400">DocAuditor</a>
        <h1 class="mt-3 text-3xl font-bold tracking-tight text-alabaster-grey-50">Registruotis</h1>
        <p class="mt-2 text-sm text-powder-blue-400">Sukurkite paskyrą dokumentų analizės sistemai</p>
      </div>

      <form id="register-form" novalidate class="rounded-2xl border border-charcoal-blue-700/80 bg-charcoal-blue-950/70 p-7 shadow-2xl shadow-black/20 sm:p-8">
        <section id="privacy-notice" class="mb-6 rounded-xl border border-pacific-blue-400/40 bg-pacific-blue-950/40 p-4 text-sm leading-6 text-powder-blue-200" aria-labelledby="privacy-notice-title">
          <h2 id="privacy-notice-title" class="font-semibold text-alabaster-grey-50">Privatumo informacija</h2>
          <p class="mt-2">Prieš registruodamiesi peržiūrėkite, kaip tvarkomi jūsų duomenys.</p>
          <button id="privacy-open-button" type="button" class="mt-2 font-semibold text-pacific-blue-300 underline decoration-pacific-blue-300/60 underline-offset-4 hover:text-pacific-blue-200 focus:outline-none focus:ring-2 focus:ring-pacific-blue-300">
            Terms and conditions
          </button>
        </section>
        <div class="space-y-5">
          <div>
            <label for="username" class="mb-2 block text-sm font-medium text-powder-blue-200">Vartotojo vardas</label>
            <input id="username" name="username" type="text" autocomplete="username" maxlength="150" required
              class="register-input w-full rounded-xl border border-charcoal-blue-600 bg-carbon-black-950 px-4 py-3 text-sm text-alabaster-grey-50 outline-none transition placeholder:text-charcoal-blue-400 focus:border-pacific-blue-400 focus:ring-2 focus:ring-pacific-blue-400/20" />
            <p id="username-error" class="mt-1 hidden text-xs text-rose-300" aria-live="polite"></p>
          </div>
          <div>
            <label for="email" class="mb-2 block text-sm font-medium text-powder-blue-200">El. paštas</label>
            <input id="email" name="email" type="email" autocomplete="email" placeholder="vardas@pastas.lt" required
              class="register-input w-full rounded-xl border border-charcoal-blue-600 bg-carbon-black-950 px-4 py-3 text-sm text-alabaster-grey-50 outline-none transition placeholder:text-charcoal-blue-400 focus:border-pacific-blue-400 focus:ring-2 focus:ring-pacific-blue-400/20" />
            <p id="email-error" class="mt-1 hidden text-xs text-rose-300" aria-live="polite"></p>
          </div>
          <div>
            <label for="password" class="mb-2 block text-sm font-medium text-powder-blue-200">Slaptažodis</label>
            <input id="password" name="password" type="password" autocomplete="new-password" minlength="8" maxlength="128" required
              class="register-input w-full rounded-xl border border-charcoal-blue-600 bg-carbon-black-950 px-4 py-3 text-sm text-alabaster-grey-50 outline-none transition placeholder:text-charcoal-blue-400 focus:border-pacific-blue-400 focus:ring-2 focus:ring-pacific-blue-400/20" />
            <p class="mt-1 text-xs text-powder-blue-500">Nuo 8 iki 128 simbolių.</p>
            <p id="password-error" class="mt-1 hidden text-xs text-rose-300" aria-live="polite"></p>
          </div>
        </div>

        <p id="register-message" class="mt-5 min-h-5 text-center text-sm font-medium" aria-live="polite"></p>
        <button type="submit"
          class="mt-4 w-full rounded-xl bg-pacific-blue-500 px-4 py-3 text-sm font-semibold text-carbon-black-950 transition hover:bg-pacific-blue-400 focus:outline-none focus:ring-2 focus:ring-pacific-blue-300 focus:ring-offset-2 focus:ring-offset-charcoal-blue-950">
          Sukurti paskyrą
        </button>
        <p class="mt-5 text-center text-sm text-powder-blue-400">
          Jau turite paskyrą? <a href="/login" class="font-semibold text-pacific-blue-300 hover:text-pacific-blue-200">Prisijungti</a>
        </p>
      </form>
    </section>
    <div id="privacy-dialog" class="fixed inset-0 z-30 hidden items-center justify-center bg-carbon-black-950/80 p-4" role="dialog" aria-modal="true" aria-labelledby="privacy-dialog-title">
      <section class="max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-charcoal-blue-700/80 bg-charcoal-blue-950 p-6 shadow-2xl">
        <header class="flex items-center justify-between gap-4">
          <h2 id="privacy-dialog-title" class="text-lg font-semibold text-alabaster-grey-50">Terms and conditions</h2>
          <button id="privacy-close-button" type="button" class="rounded-xl border border-charcoal-blue-600 px-4 py-2 text-sm font-semibold text-alabaster-grey-50 transition hover:border-pacific-blue-400">
            Uždaryti
          </button>
        </header>
        <div class="mt-5 space-y-4 text-sm leading-6 text-powder-blue-200">
          <p>Prieš pateikdami registracijos duomenis susipažinkite su tuo, kaip sistema juos tvarko.</p>
          <div>
            <h3 class="font-semibold text-alabaster-grey-100">Kokius duomenis renkame?</h3>
            <p>Renkame vartotojo vardą, el. pašto adresą ir paskyros slaptažodį. Slaptažodis saugomas tik užšifruotu (maišos) pavidalu.</p>
          </div>
          <div>
            <h3 class="font-semibold text-alabaster-grey-100">Kaip naudojame duomenis?</h3>
            <p>Duomenys naudojami paskyrai sukurti, prisijungimui, dokumentų analizei ir sistemos veikimui užtikrinti.</p>
          </div>
          <div>
            <h3 class="font-semibold text-alabaster-grey-100">Kiek laiko saugome duomenis?</h3>
            <p>Paskyros duomenys saugomi, kol paskyra ištrinama arba kol jų saugojimas reikalingas sistemos veikimui ir saugumui.</p>
          </div>
          <div>
            <h3 class="font-semibold text-alabaster-grey-100">Kas gali pasiekti duomenis?</h3>
            <p>Duomenis gali pasiekti tik sistemos administratoriai ir paslaugų teikėjai, būtini sistemos veikimui. Jie gali būti perduodami DI paslaugos teikėjui tik dokumentų analizės ir klausimų atsakymo funkcijoms vykdyti.</p>
          </div>
        </div>
      </section>
    </div>
  </main>
`;

initializeThemeToggle();

const form = document.querySelector('#register-form');
const message = document.querySelector('#register-message');
const submitButton = form.querySelector('button[type="submit"]');
const privacyDialog = document.querySelector('#privacy-dialog');
const privacyOpenButton = document.querySelector('#privacy-open-button');
const privacyCloseButton = document.querySelector('#privacy-close-button');
const fieldNames = ['username', 'email', 'password'];

function clearFieldError(name) {
  const input = form.elements.namedItem(name);
  const error = document.querySelector(`#${name}-error`);
  input.classList.remove('border-rose-400');
  input.removeAttribute('aria-invalid');
  error.textContent = '';
  error.classList.add('hidden');
}

function showFieldError(name, text) {
  const input = form.elements.namedItem(name);
  const error = document.querySelector(`#${name}-error`);
  input.classList.add('border-rose-400');
  input.setAttribute('aria-invalid', 'true');
  error.textContent = text;
  error.classList.remove('hidden');
}

function openPrivacyDialog() {
  privacyDialog.classList.remove('hidden');
  privacyDialog.classList.add('flex');
  privacyCloseButton.focus();
}

function closePrivacyDialog() {
  privacyDialog.classList.add('hidden');
  privacyDialog.classList.remove('flex');
  privacyOpenButton.focus();
}

privacyOpenButton.addEventListener('click', openPrivacyDialog);
privacyCloseButton.addEventListener('click', closePrivacyDialog);
privacyDialog.addEventListener('click', (event) => {
  if (event.target === privacyDialog) closePrivacyDialog();
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && !privacyDialog.classList.contains('hidden')) closePrivacyDialog();
});

for (const name of fieldNames) {
  form.elements.namedItem(name).addEventListener('input', () => clearFieldError(name));
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  for (const name of fieldNames) clearFieldError(name);
  message.textContent = '';
  message.className = 'mt-5 min-h-5 text-center text-sm font-medium';

  const formData = new FormData(form);
  const values = Object.fromEntries(formData.entries());
  const errors = {};

  values.username = String(values.username).trim();
  values.email = String(values.email).trim();
  if (!values.username) errors.username = 'Įveskite vartotojo vardą.';
  else if (values.username.length > 150) errors.username = 'Vartotojo vardas negali viršyti 150 simbolių.';
  if (!String(values.email).trim()) {
    errors.email = 'Įveskite el. pašto adresą.';
  } else if (!form.elements.namedItem('email').validity.valid) {
    errors.email = 'Įveskite galiojantį el. pašto adresą.';
  }
  if (String(values.password).length < 8 || String(values.password).length > 128) {
    errors.password = 'Slaptažodį turi sudaryti 8–128 simboliai.';
  }

  for (const [name, text] of Object.entries(errors)) showFieldError(name, text);
  if (Object.keys(errors).length > 0) return;

  submitButton.disabled = true;
  submitButton.textContent = 'Registruojama...';
  try {
    const response = await fetch('/api/auth/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(values),
    });
    const result = await response.json();

    if (!response.ok) {
      for (const [name, text] of Object.entries(result.errors ?? {})) {
        if (fieldNames.includes(name)) showFieldError(name, text);
        else {
          message.textContent = text;
          message.className = 'mt-5 min-h-5 text-center text-sm font-medium text-rose-300';
        }
      }
      return;
    }

    message.textContent = result.message;
    message.className = 'mt-5 min-h-5 text-center text-sm font-medium text-emerald-300';
    form.reset();
  } catch {
    message.textContent = 'Nepavyko susisiekti su serveriu. Patikrinkite, ar veikia Django API.';
    message.className = 'mt-5 min-h-5 text-center text-sm font-medium text-rose-300';
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = 'Sukurti paskyrą';
  }
});
