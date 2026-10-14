import './style.css';

document.querySelector('#app').innerHTML = `
  <main class="flex min-h-screen items-center justify-center px-6 py-12">
    <section class="w-full max-w-lg">
      <div class="mb-8 text-center">
        <a href="/" class="text-sm font-semibold uppercase tracking-[0.3em] text-pacific-blue-400">DocAuditor</a>
        <h1 class="mt-3 text-3xl font-bold tracking-tight text-alabaster-grey-50">Registruotis</h1>
        <p class="mt-2 text-sm text-powder-blue-400">Sukurkite paskyrą dokumentų analizės sistemai</p>
      </div>

      <form id="register-form" novalidate class="rounded-2xl border border-charcoal-blue-700/80 bg-charcoal-blue-950/70 p-7 shadow-2xl shadow-black/20 sm:p-8">
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
  </main>
`;

const form = document.querySelector('#register-form');
const message = document.querySelector('#register-message');
const submitButton = form.querySelector('button[type="submit"]');
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
