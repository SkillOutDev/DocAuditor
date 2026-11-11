const THEME_STORAGE_KEY = 'docauditor-theme';

function getStoredTheme() {
  return localStorage.getItem(THEME_STORAGE_KEY) === 'light' ? 'light' : 'dark';
}

function updateThemeButton(button, theme) {
  const isLight = theme === 'light';
  button.textContent = isLight ? '☀' : '☾';
  button.setAttribute('aria-label', isLight ? 'Įjungti tamsią temą' : 'Įjungti šviesią temą');
  button.title = isLight ? 'Tamsi tema' : 'Šviesi tema';
}

export function initializeThemeToggle() {
  const theme = getStoredTheme();
  document.documentElement.classList.toggle('light-theme', theme === 'light');

  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'theme-toggle';
  button.addEventListener('click', () => {
    const nextTheme = document.documentElement.classList.contains('light-theme') ? 'dark' : 'light';
    document.documentElement.classList.toggle('light-theme', nextTheme === 'light');
    localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
    updateThemeButton(button, nextTheme);
  });
  updateThemeButton(button, theme);
  document.body.append(button);
}
