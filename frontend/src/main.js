import './style.css';

document.querySelector('#app').innerHTML = `
  <main class="min-h-screen px-6 py-16">
    <section class="mx-auto max-w-5xl">
      <p class="mb-4 text-sm font-semibold uppercase tracking-[0.3em] text-pacific-blue-400">DocAuditor</p>
      <h1 class="max-w-3xl text-4xl font-bold tracking-tight text-alabaster-grey-50 sm:text-6xl">
        Dokumentų analizės sistemos pradinis karkasas
      </h1>
      <p class="mt-6 max-w-2xl text-lg leading-8 text-powder-blue-400">
        Vite, Tailwind CSS, Django, PostgreSQL ir pasirenkamas Gemini arba Ollama DI tiekėjas.
      </p>
      <div class="mt-10 flex flex-wrap gap-3">
        ${['HTML5', 'Tailwind CSS v4', 'Vite', 'Django', 'PostgreSQL', 'Gemini / Ollama']
          .map((technology) => `<span class="rounded-full border border-charcoal-blue-700 bg-charcoal-blue-900 px-4 py-2 text-sm text-powder-blue-200">${technology}</span>`)
          .join('')}
      </div>
      <div class="mt-10 flex flex-wrap gap-3">
        <a href="/login" class="inline-flex rounded-xl border border-charcoal-blue-600 px-5 py-3 text-sm font-semibold text-alabaster-grey-50 transition hover:border-pacific-blue-400">
          Prisijungti
        </a>
        <a href="/register" class="inline-flex rounded-xl bg-pacific-blue-500 px-5 py-3 text-sm font-semibold text-carbon-black-950 transition hover:bg-pacific-blue-400">
          Registruotis
        </a>
      </div>
    </section>
  </main>
`;
