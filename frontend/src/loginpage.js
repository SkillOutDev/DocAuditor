import './style.css';

const DEMO_EMAIL = 'admin@gmail.com';
const DEMO_PASSWORD = 'admin123';

document.querySelector('#app').innerHTML = `
  <main class="flex min-h-screen items-center justify-center px-6 py-12">
    <section class="w-full max-w-md">
      <div class="mb-8 text-center">
        <div class="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-pacific-blue-500/15 text-pacific-blue-300 ring-1 ring-pacific-blue-400/30">
          <svg aria-hidden="true" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M4 7.5 12 13l8-5.5M5.5 19h13A1.5 1.5 0 0 0 20 17.5v-11A1.5 1.5 0 0 0 18.5 5h-13A1.5 1.5 0 0 0 4 6.5v11A1.5 1.5 0 0 0 5.5 19Z" />
          </svg>
        </div>
        <p class="text-sm font-semibold uppercase tracking-[0.3em] text-pacific-blue-400">DocAuditor</p>
        <h1 class="mt-3 text-3xl font-bold tracking-tight text-alabaster-grey-50">Prisijungti</h1>
        <p class="mt-2 text-sm text-powder-blue-400">Prisijunkite prie dokumentų analizės sistemos</p>
      </div>

      <form id="login-form" novalidate class="rounded-2xl border border-charcoal-blue-700/80 bg-charcoal-blue-950/70 p-7 shadow-2xl shadow-black/20 sm:p-8">
        <div class="space-y-5">
          <div>
            <label for="email" class="mb-2 block text-sm font-medium text-powder-blue-200">Gmail el. paštas</label>
            <input id="email" name="email" type="email" autocomplete="email" placeholder="vardas@gmail.com" required
              class="w-full rounded-xl border border-charcoal-blue-600 bg-carbon-black-950 px-4 py-3 text-sm text-alabaster-grey-50 outline-none transition placeholder:text-charcoal-blue-400 focus:border-pacific-blue-400 focus:ring-2 focus:ring-pacific-blue-400/20" />
          </div>
          <div>
            <label for="password" class="mb-2 block text-sm font-medium text-powder-blue-200">Slaptažodis</label>
            <input id="password" name="password" type="password" autocomplete="current-password" placeholder="Įveskite slaptažodį" required
              class="w-full rounded-xl border border-charcoal-blue-600 bg-carbon-black-950 px-4 py-3 text-sm text-alabaster-grey-50 outline-none transition placeholder:text-charcoal-blue-400 focus:border-pacific-blue-400 focus:ring-2 focus:ring-pacific-blue-400/20" />
          </div>
        </div>

        <p id="login-message" class="mt-5 min-h-5 text-center text-sm font-medium" aria-live="polite"></p>
        <button type="submit"
          class="mt-4 w-full rounded-xl bg-pacific-blue-500 px-4 py-3 text-sm font-semibold text-carbon-black-950 transition hover:bg-pacific-blue-400 focus:outline-none focus:ring-2 focus:ring-pacific-blue-300 focus:ring-offset-2 focus:ring-offset-charcoal-blue-950">
          Prisijungti
        </button>
        <p class="mt-5 text-center text-sm text-powder-blue-400">
          Neturite paskyros? <a href="/register" class="font-semibold text-pacific-blue-300 hover:text-pacific-blue-200">Registruotis</a>
        </p>
      </form>
    </section>
  </main>
`;

const form = document.querySelector('#login-form');
const message = document.querySelector('#login-message');

form.addEventListener('submit', (event) => {
  event.preventDefault();

  const formData = new FormData(form);
  const email = formData.get('email').trim();
  const password = formData.get('password');

  if (!email || !password) {
    message.textContent = 'Neįvesti prisijungimo duomenys';
    message.className = 'mt-5 min-h-5 text-center text-sm font-medium text-amber-300';
    return;
  }

  if (email !== DEMO_EMAIL || password !== DEMO_PASSWORD) {
    message.textContent = 'Prisijungimo el. paštas arba slaptažodis neteisingas';
    message.className = 'mt-5 min-h-5 text-center text-sm font-medium text-rose-300';
    return;
  }

  message.textContent = 'Prisijungta sėkmingai';
  message.className = 'mt-5 min-h-5 text-center text-sm font-medium text-emerald-300';
});
