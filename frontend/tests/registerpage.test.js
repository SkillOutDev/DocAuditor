import { beforeEach, describe, expect, it, vi } from 'vitest';

const flush = () => new Promise((resolve) => setTimeout(resolve, 0));
const $ = (selector) => document.querySelector(selector);
const json = (body, status = 200) => ({ ok: status < 400, status, json: async () => body });

async function loadPage() {
  vi.resetModules();
  document.body.innerHTML = '<div id="app"></div>';
  await import('../src/registerpage.js');
}

function fill({ username = 'jonas', email = 'jonas@example.com', password = 'longenough1' } = {}) {
  $('#username').value = username;
  $('#email').value = email;
  $('#password').value = password;
}

async function submit() {
  $('#register-form').dispatchEvent(new Event('submit', { cancelable: true }));
  await flush();
}

const error = (name) => $(`#${name}-error`);

describe('register page', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  it('shows required-field errors without calling the API', async () => {
    await loadPage();
    fill({ username: ' ', email: '', password: '' });
    await submit();
    expect(error('username').textContent).toBe('Įveskite vartotojo vardą.');
    expect(error('email').textContent).toBe('Įveskite el. pašto adresą.');
    expect(error('password').textContent).toBe('Slaptažodį turi sudaryti 8–128 simboliai.');
    expect($('#username').getAttribute('aria-invalid')).toBe('true');
    expect(fetch).not.toHaveBeenCalled();
  });

  it('validates username length, email format and password length', async () => {
    await loadPage();
    fill({ username: 'x'.repeat(151), email: 'not-an-email', password: 'p'.repeat(129) });
    await submit();
    expect(error('username').textContent).toBe('Vartotojo vardas negali viršyti 150 simbolių.');
    expect(error('email').textContent).toBe('Įveskite galiojantį el. pašto adresą.');
    expect(error('password').classList.contains('hidden')).toBe(false);
    expect(fetch).not.toHaveBeenCalled();
  });

  it('clears a field error when the user types', async () => {
    await loadPage();
    fill({ username: '' });
    await submit();
    $('#username').dispatchEvent(new Event('input'));
    expect(error('username').classList.contains('hidden')).toBe(true);
    expect($('#username').hasAttribute('aria-invalid')).toBe(false);
  });

  it('registers and resets the form on success', async () => {
    fetch.mockResolvedValue(json({ message: 'Registracija sėkminga. Galite prisijungti.' }, 201));
    await loadPage();
    fill();
    await submit();
    expect(fetch).toHaveBeenCalledWith(
      '/api/auth/register/',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ username: 'jonas', email: 'jonas@example.com', password: 'longenough1' }),
      }),
    );
    expect($('#register-message').textContent).toBe('Registracija sėkminga. Galite prisijungti.');
    expect($('#username').value).toBe('');
    expect($('button[type="submit"]').disabled).toBe(false);
  });

  it('maps server field errors and general errors', async () => {
    fetch.mockResolvedValue(
      json({ errors: { username: 'Šis vartotojo vardas jau naudojamas.', form: 'Bendra klaida' } }, 409),
    );
    await loadPage();
    fill();
    await submit();
    expect(error('username').textContent).toBe('Šis vartotojo vardas jau naudojamas.');
    expect($('#register-message').textContent).toBe('Bendra klaida');
  });

  it('reports network errors', async () => {
    fetch.mockRejectedValue(new Error('offline'));
    await loadPage();
    fill();
    await submit();
    expect($('#register-message').textContent).toContain('Nepavyko susisiekti su serveriu');
    expect($('button[type="submit"]').textContent.trim()).toBe('Sukurti paskyrą');
  });
});
