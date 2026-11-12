import { beforeEach, describe, expect, it, vi } from 'vitest';

const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

async function loadPage() {
  vi.resetModules();
  document.body.innerHTML = '<div id="app"></div>';
  await import('../src/loginpage.js');
}

function submit(email, password) {
  document.querySelector('#email').value = email;
  document.querySelector('#password').value = password;
  document.querySelector('#login-form').dispatchEvent(new Event('submit', { cancelable: true }));
}

const message = () => document.querySelector('#login-message').textContent;

describe('login page', () => {
  let assign;

  beforeEach(() => {
    assign = vi.fn();
    vi.stubGlobal('location', { assign });
    vi.stubGlobal('fetch', vi.fn());
  });

  it('requires both fields before calling the API', async () => {
    await loadPage();
    submit('', '');
    await flush();
    expect(message()).toBe('Neįvesti prisijungimo duomenys');
    expect(fetch).not.toHaveBeenCalled();
  });

  it('redirects to documents on success', async () => {
    fetch.mockResolvedValue({ ok: true });
    await loadPage();
    submit(' user@example.com ', 'secret');
    await flush();
    expect(fetch).toHaveBeenCalledWith(
      '/api/auth/login/',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'user@example.com', password: 'secret' }),
      }),
    );
    expect(assign).toHaveBeenCalledWith('/documents');
  });

  it('shows the server error message on failure', async () => {
    fetch.mockResolvedValue({
      ok: false,
      json: async () => ({ message: 'Neteisingai suvesti prisijungimo duomenys' }),
    });
    await loadPage();
    submit('user@example.com', 'bad');
    await flush();
    expect(message()).toBe('Neteisingai suvesti prisijungimo duomenys');
    expect(assign).not.toHaveBeenCalled();
    expect(document.querySelector('button[type="submit"]').disabled).toBe(false);
  });

  it('falls back to the default message when the body is not JSON', async () => {
    fetch.mockResolvedValue({
      ok: false,
      json: async () => {
        throw new Error('bad json');
      },
    });
    await loadPage();
    submit('user@example.com', 'bad');
    await flush();
    expect(message()).toBe('Neteisingai suvesti prisijungimo duomenys');
  });

  it('reports network errors', async () => {
    fetch.mockRejectedValue(new Error('offline'));
    await loadPage();
    submit('user@example.com', 'secret');
    await flush();
    expect(message()).toContain('Nepavyko susisiekti su serveriu');
  });
});
