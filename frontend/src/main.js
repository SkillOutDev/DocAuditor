import './style.css';
import { initializeThemeToggle } from './theme.js';

document.querySelector('#app').innerHTML = `
  <main class="landing-page min-h-screen overflow-hidden px-6 pb-16">
    <nav class="relative z-10 mx-auto flex max-w-6xl items-center justify-between py-6" aria-label="Pagrindinė navigacija">
      <a href="/" class="flex items-center gap-3 text-alabaster-grey-50" aria-label="DocAuditor pradinis puslapis">
        <span class="brand-mark flex h-10 w-10 items-center justify-center rounded-xl bg-pacific-blue-500 text-carbon-black-950 shadow-lg shadow-pacific-blue-500/20">
          <svg aria-hidden="true" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 3.75h7.25L19 8.5v11.75H7A2.25 2.25 0 0 1 4.75 18V6A2.25 2.25 0 0 1 7 3.75Z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 4v5h5M8.5 13h6M8.5 16h4" />
          </svg>
        </span>
        <span class="text-lg font-bold tracking-tight">Doc<span class="text-pacific-blue-400">Auditor</span></span>
      </a>
      <a href="/login" class="hidden text-sm font-semibold text-powder-blue-300 transition hover:text-pacific-blue-300 sm:inline-flex">
        Jau turite paskyrą? <span class="ml-1 text-pacific-blue-300">Prisijungti</span>
      </a>
    </nav>

    <section class="relative z-10 mx-auto grid max-w-6xl items-center gap-14 pb-20 pt-14 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16 lg:pb-28 lg:pt-20">
      <div>
        <div class="mb-6 inline-flex items-center gap-2 rounded-full border border-pacific-blue-400/25 bg-pacific-blue-500/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] text-pacific-blue-300">
        <span class="h-1.5 w-1.5 rounded-full bg-pacific-blue-400 shadow-[0_0_10px_currentColor]"></span>
          Išmanesni dokumentai
        </div>
        <h1 class="max-w-2xl text-5xl font-bold leading-[1.06] tracking-[-0.04em] text-alabaster-grey-50 sm:text-6xl lg:text-7xl">
          Aiškumas kiekviename <span class="hero-gradient">dokumente.</span>
        </h1>
        <p class="mt-7 max-w-xl text-lg leading-8 text-powder-blue-300">
          DocAuditor padeda greitai suprasti, įvertinti ir valdyti dokumentų rizikas. Mažiau spėliojimo, daugiau užtikrintumo.
        </p>
        <div class="mt-9 flex flex-wrap items-center gap-3">
          <a href="/register" class="inline-flex items-center gap-2 rounded-xl bg-pacific-blue-500 px-5 py-3.5 text-sm font-semibold text-carbon-black-950 shadow-lg shadow-pacific-blue-500/15 transition hover:-translate-y-0.5 hover:bg-pacific-blue-400">
            Pradėti nemokamai
            <svg aria-hidden="true" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14m-6-6 6 6-6 6" /></svg>
          </a>
          <a href="/login" class="inline-flex rounded-xl border border-charcoal-blue-600 bg-charcoal-blue-950/40 px-5 py-3.5 text-sm font-semibold text-alabaster-grey-50 transition hover:border-pacific-blue-400 hover:bg-charcoal-blue-900">
            Prisijungti
          </a>
        </div>
        <p class="mt-5 text-xs text-powder-blue-500">Įkelkite savo dokumentą ir gaukite aiškias, suprantamas įžvalgas.</p>
      </div>

      <div class="landing-preview relative mx-auto w-full max-w-lg">
        <div class="preview-glow"></div>
        <div class="relative rounded-3xl border border-charcoal-blue-700/80 bg-charcoal-blue-950/90 p-3 shadow-2xl shadow-black/40 backdrop-blur-xl">
          <div class="rounded-2xl border border-charcoal-blue-800 bg-carbon-black-950/80 p-5 sm:p-6">
            <div class="mb-7 flex items-center justify-between">
              <div>
                <p class="text-xs font-medium text-powder-blue-500">Dokumento analizė</p>
                <p class="mt-1 text-sm font-semibold text-alabaster-grey-100">Paslaugų sutartis.pdf</p>
              </div>
              <span class="rounded-lg bg-emerald-400/10 px-2.5 py-1 text-xs font-semibold text-emerald-600">Analizė paruošta</span>
            </div>
            <div class="mb-6 flex items-center gap-4 rounded-xl border border-pacific-blue-500/20 bg-pacific-blue-500/5 p-4">
              <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-pacific-blue-500/15 text-xl text-pacific-blue-300">✦</span>
              <div>
                <p class="text-sm font-semibold text-alabaster-grey-100">Pagrindinės įžvalgos paruoštos</p>
                <p class="mt-1 text-xs text-powder-blue-400">Peržiūrėkite svarbiausias dokumento sąlygas</p>
              </div>
            </div>
            <div class="space-y-3">
              <div class="flex items-center gap-3 rounded-xl border border-charcoal-blue-800 bg-charcoal-blue-900/50 px-3 py-3">
                <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-400/10 text-emerald-300">✓</span>
                <span class="flex-1 text-xs font-medium text-powder-blue-200">Svarbiausios sąlygos</span>
                <span class="text-xs font-semibold text-emerald-300">Rastos</span>
              </div>
              <div class="flex items-center gap-3 rounded-xl border border-charcoal-blue-800 bg-charcoal-blue-900/50 px-3 py-3">
                <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-400/10 text-amber-300">!</span>
                <span class="flex-1 text-xs font-medium text-powder-blue-200">Atkreiptinas dėmesys</span>
                <span class="text-xs font-semibold text-yellow-500">2 vietos</span>
              </div>
              <div class="flex items-center gap-3 rounded-xl border border-charcoal-blue-800 bg-charcoal-blue-900/50 px-3 py-3">
                <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-pacific-blue-500/10 text-pacific-blue-300">↗</span>
                <span class="flex-1 text-xs font-medium text-powder-blue-200">Privatumo sąlygos</span>
                <span class="text-xs font-semibold text-pacific-blue-300">Peržiūrėti</span>
              </div>
            </div>
          </div>
        </div>
        <div class="absolute -bottom-5 -left-5 hidden items-center gap-3 rounded-2xl border border-charcoal-blue-700 bg-charcoal-blue-950/95 px-4 py-3 shadow-xl sm:flex">
          <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-pacific-blue-500/15 text-pacific-blue-300">✦</span>
          <div><p class="text-xs font-semibold text-alabaster-grey-100">DI įžvalgos</p><p class="text-[11px] text-powder-blue-500">Paruošta per kelias sekundes</p></div>
        </div>
      </div>
    </section>

    <section class="relative z-10 mx-auto max-w-6xl border-t border-charcoal-blue-800/70 pt-10">
      <p class="text-center text-xs font-semibold uppercase tracking-[0.2em] text-powder-blue-500">Viskas, ko reikia dokumentų kontrolei</p>
      <div class="mt-7 grid gap-4 md:grid-cols-3">
        <article class="feature-card rounded-2xl border border-charcoal-blue-800 bg-charcoal-blue-950/45 p-5">
          <span class="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-pacific-blue-500/10 text-lg text-pacific-blue-300">⌁</span>
          <h2 class="font-semibold text-alabaster-grey-100">Greita analizė</h2>
          <p class="mt-2 text-sm leading-6 text-powder-blue-400">Gaukite svarbiausias dokumento įžvalgas vienoje vietoje.</p>
        </article>
        <article class="feature-card rounded-2xl border border-charcoal-blue-800 bg-charcoal-blue-950/45 p-5">
          <span class="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-pacific-blue-500/10 text-lg text-pacific-blue-300">◈</span>
          <h2 class="font-semibold text-alabaster-grey-100">Rizikos kontrolė</h2>
          <p class="mt-2 text-sm leading-6 text-powder-blue-400">Pastebėkite neaiškias ir rizikingas sąlygas anksčiau.</p>
        </article>
        <article class="feature-card rounded-2xl border border-charcoal-blue-800 bg-charcoal-blue-950/45 p-5">
          <span class="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-pacific-blue-500/10 text-lg text-pacific-blue-300">⌘</span>
          <h2 class="font-semibold text-alabaster-grey-100">Saugus procesas</h2>
          <p class="mt-2 text-sm leading-6 text-powder-blue-400">Tvarkykite dokumentus ramiai, skaidriai ir patikimai.</p>
        </article>
      </div>
    </section>
  </main>
`;

initializeThemeToggle();
