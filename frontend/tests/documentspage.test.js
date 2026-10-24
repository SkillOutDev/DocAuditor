import { beforeEach, describe, expect, it, vi } from 'vitest';

const flush = async () => {
  for (let i = 0; i < 5; i += 1) await new Promise((resolve) => setTimeout(resolve, 0));
};

const doc = { id: 1, original_filename: 'sutartis.pdf', created_at: '2026-01-02T10:00:00Z' };
const $ = (selector) => document.querySelector(selector);
const json = (body, status = 200) => ({ ok: status < 400, status, json: async () => body });

let location;
let calls;

function route(handlers) {
  fetch.mockImplementation(async (url, options = {}) => {
    const key = `${options.method ?? 'GET'} ${url}`;
    calls.push(key);
    const handler = handlers[key];
    if (!handler) throw new Error(`Unexpected request: ${key}`);
    return handler(options);
  });
}

const baseRoutes = (documents = [doc]) => ({
  'GET /api/documents/': () => json({ documents }),
  'GET /api/auth/csrf/': () => json({}),
});

async function loadPage(handlers = baseRoutes()) {
  vi.resetModules();
  document.body.innerHTML = '<div id="app"></div>';
  route(handlers);
  await import('../src/documentspage.js');
  await flush();
}

function chooseFile(file) {
  const input = $('#file-input');
  Object.defineProperty(input, 'files', { value: file ? [file] : [], configurable: true });
  input.dispatchEvent(new Event('change'));
}

const submitForm = () => $('#upload-form').dispatchEvent(new Event('submit', { cancelable: true }));
const pdf = (name = 'a.pdf', size = 10) => new File([new Uint8Array(size)], name, { type: 'application/pdf' });

describe('documents page', () => {
  beforeEach(() => {
    calls = [];
    location = { replace: vi.fn(), assign: vi.fn() };
    vi.stubGlobal('location', location);
    vi.stubGlobal('fetch', vi.fn());
    document.cookie = 'csrftoken=token123';
  });

  describe('document list', () => {
    it('renders documents', async () => {
      await loadPage();
      expect($('#documents-list').textContent).toContain('sutartis.pdf');
      expect($('#documents-status').textContent).toBe('');
    });

    it('shows an empty state', async () => {
      await loadPage(baseRoutes([]));
      expect($('#documents-status').textContent).toBe('Nėra įkeltų dokumentų.');
    });

    it('redirects to login on 401', async () => {
      await loadPage({ 'GET /api/documents/': () => json({}, 401) });
      expect(location.replace).toHaveBeenCalledWith('/login');
    });

    it('shows an error when loading fails', async () => {
      await loadPage({ 'GET /api/documents/': () => json({}, 500) });
      expect($('#documents-status').textContent).toBe('Nepavyko įkelti dokumentų sąrašo.');
    });
  });

  describe('upload', () => {
    it('opens the file picker from the button', async () => {
      await loadPage();
      const click = vi.spyOn($('#file-input'), 'click');
      $('#choose-button').click();
      expect(click).toHaveBeenCalled();
    });

    it('asks for a file when none is chosen', async () => {
      await loadPage();
      submitForm();
      await flush();
      expect($('#upload-message').textContent).toBe('Pirmiausia pasirinkite dokumentą.');
    });

    it('shows the selected file name and resets when cleared', async () => {
      await loadPage();
      chooseFile(pdf('a.pdf'));
      expect($('#file-name').textContent).toBe('a.pdf');
      chooseFile(null);
      expect($('#file-name').textContent).toBe('Failas nepasirinktas');
    });

    it('rejects unsupported extensions', async () => {
      await loadPage();
      chooseFile(new File(['x'], 'a.txt'));
      expect($('#upload-message').textContent).toBe('Leidžiami tik PDF, DOC ir DOCX failai.');
      expect($('#file-name').textContent).toBe('Failas nepasirinktas');
    });

    it('rejects files over 15 MB', async () => {
      await loadPage();
      chooseFile(pdf('big.pdf', 15 * 1024 * 1024 + 1));
      expect($('#upload-message').textContent).toBe('Dokumento dydis negali viršyti 15 MB.');
    });

    it('re-validates on submit', async () => {
      await loadPage();
      const input = $('#file-input');
      Object.defineProperty(input, 'files', { value: [new File(['x'], 'a.exe')], configurable: true });
      submitForm();
      await flush();
      expect($('#upload-message').textContent).toBe('Leidžiami tik PDF, DOC ir DOCX failai.');
    });

    it('uploads with the CSRF header and refreshes the list', async () => {
      let uploadOptions;
      await loadPage({
        ...baseRoutes(),
        'POST /api/documents/': (options) => {
          uploadOptions = options;
          return json({}, 201);
        },
      });
      chooseFile(pdf());
      submitForm();
      await flush();
      expect(uploadOptions.headers['X-CSRFToken']).toBe('token123');
      expect(uploadOptions.body.get('file').name).toBe('a.pdf');
      expect(calls.indexOf('GET /api/auth/csrf/')).toBeLessThan(calls.indexOf('POST /api/documents/'));
      expect($('#upload-message').textContent).toBe('Dokumentas išsaugotas sėkmingai');
      expect($('#save-button').disabled).toBe(false);
      expect(calls.filter((call) => call === 'GET /api/documents/')).toHaveLength(2);
    });

    it('shows a failure message when the server rejects the upload', async () => {
      await loadPage({ ...baseRoutes(), 'POST /api/documents/': () => json({}, 403) });
      chooseFile(pdf());
      submitForm();
      await flush();
      expect($('#upload-message').textContent).toBe('Nepavyko įkelti dokumento');
    });

    it('shows a failure message on network errors', async () => {
      await loadPage({
        ...baseRoutes(),
        'POST /api/documents/': () => {
          throw new Error('offline');
        },
      });
      chooseFile(pdf());
      submitForm();
      await flush();
      expect($('#upload-message').textContent).toBe('Nepavyko įkelti dokumento');
    });

    it('redirects to login when the session expired', async () => {
      await loadPage({ ...baseRoutes(), 'POST /api/documents/': () => json({}, 401) });
      chooseFile(pdf());
      submitForm();
      await flush();
      expect(location.replace).toHaveBeenCalledWith('/login');
    });
  });

  describe('preview', () => {
    beforeEach(() => {
      URL.createObjectURL = vi.fn(() => 'blob:preview');
      URL.revokeObjectURL = vi.fn();
    });

    const previewRoute = (blob, status = 200) => ({
      ...baseRoutes(),
      'GET /api/documents/1/preview/': () => ({ ok: status < 400, status, blob: async () => blob }),
    });

    it('shows PDFs in the frame', async () => {
      await loadPage(previewRoute(new Blob(['x'], { type: 'application/pdf' })));
      $('[data-document-id="1"]').click();
      await flush();
      expect($('#preview-title').textContent).toBe('sutartis.pdf');
      expect($('#preview-frame').classList.contains('hidden')).toBe(false);
    });

    it('offers a download for other formats', async () => {
      await loadPage(previewRoute(new Blob(['x'], { type: 'application/msword' })));
      $('[data-document-id="1"]').click();
      await flush();
      expect($('#preview-status').textContent).toBe('Šio formato peržiūra naršyklėje nepalaikoma.');
      expect($('#preview-download').classList.contains('hidden')).toBe(false);
    });

    it('reports preview errors', async () => {
      await loadPage(previewRoute(null, 500));
      $('[data-document-id="1"]').click();
      await flush();
      expect($('#preview-status').textContent).toBe('Įvyko klaida. Dokumento peržiūrėti nepavyko.');
    });

    it('redirects to login on 401', async () => {
      await loadPage(previewRoute(null, 401));
      $('[data-document-id="1"]').click();
      await flush();
      expect(location.replace).toHaveBeenCalledWith('/login');
    });

    it('closes via button, backdrop and Escape', async () => {
      await loadPage(previewRoute(new Blob(['x'], { type: 'application/pdf' })));
      const open = async () => {
        $('[data-document-id="1"]').click();
        await flush();
      };
      const hidden = () => $('#preview-dialog').classList.contains('hidden');

      await open();
      $('#close-preview-button').click();
      expect(hidden()).toBe(true);
      expect(URL.revokeObjectURL).toHaveBeenCalled();

      await open();
      $('#preview-dialog').click();
      expect(hidden()).toBe(true);

      await open();
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
      expect(hidden()).toBe(true);
    });
  });

  describe('delete', () => {
    const deleteRoutes = (status) => ({
      ...baseRoutes(),
      'DELETE /api/documents/1/': () => json({}, status),
    });
    const dialogHidden = () => $('#delete-dialog').classList.contains('hidden');

    it('confirms and deletes a document', async () => {
      await loadPage(deleteRoutes(204));
      $('[data-delete-document-id="1"]').click();
      expect(dialogHidden()).toBe(false);
      $('#confirm-delete-button').click();
      await flush();
      expect(calls).toContain('DELETE /api/documents/1/');
      expect($('#documents-message').textContent).toBe('Dokumentas sėkmingai ištrintas');
    });

    it('can be cancelled', async () => {
      await loadPage(deleteRoutes(204));
      $('[data-delete-document-id="1"]').click();
      $('#cancel-delete-button').click();
      expect(dialogHidden()).toBe(true);
      expect(calls).not.toContain('DELETE /api/documents/1/');
    });

    it('closes the dialog on backdrop click and Escape', async () => {
      await loadPage(deleteRoutes(204));
      $('[data-delete-document-id="1"]').click();
      $('#delete-dialog').click();
      expect(dialogHidden()).toBe(true);
      $('[data-delete-document-id="1"]').click();
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
      expect(dialogHidden()).toBe(true);
    });

    it('shows an error when deletion fails', async () => {
      await loadPage(deleteRoutes(500));
      $('[data-delete-document-id="1"]').click();
      $('#confirm-delete-button').click();
      await flush();
      expect($('#documents-message').textContent).toBe('Klaida: nepavyko ištrinti dokumento');
    });

    it('redirects to login on 401', async () => {
      await loadPage(deleteRoutes(401));
      $('[data-delete-document-id="1"]').click();
      $('#confirm-delete-button').click();
      await flush();
      expect(location.replace).toHaveBeenCalledWith('/login');
    });
  });

  describe('logout', () => {
    it('posts with the CSRF header and redirects to login', async () => {
      let options;
      await loadPage({
        ...baseRoutes(),
        'POST /api/auth/logout/': (opts) => {
          options = opts;
          return json({});
        },
      });
      $('#logout-button').click();
      await flush();
      expect(options.headers['X-CSRFToken']).toBe('token123');
      expect(location.replace).toHaveBeenCalledWith('/login');
    });
  });
});
