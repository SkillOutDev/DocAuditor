# DocAuditor

Pradinis dokumentų analizės sistemos karkasas:

- `frontend/` — HTML5, Tailwind CSS v4 ir Vite v8.3.0;
- `backend/` — Django v6.1 API, veikianti su Python;
- PostgreSQL v18.6 — paleidžiama per `docker-compose.yml`;
- `backend/api/ai.py` — pasirenkamas Gemini API arba lokalaus Ollama modelio tiekėjas.

## Paleidimas

1. Nukopijuokite `.env.example` į `.env` ir prireikus pakeiskite reikšmes.
2. Paleiskite duomenų bazę:

   ```powershell
   docker compose up -d db
   ```

3. Įdiekite backend priklausomybes ir paleiskite Django:

   ```powershell
   cd backend
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver
   ```

4. Kitame terminale įdiekite frontend priklausomybes ir paleiskite Vite:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

API sveikatos patikra: `http://localhost:8000/api/health/`.

## Duomenų bazės lentelės

Django migracijos sukuria standartines autentifikacijos lenteles (`auth_*`,
`django_*`) ir `api_document` lentelę. `api_document` saugo:

- dokumento savininką;
- failo pavadinimą, tipą ir dydį;
- analizės būseną;
- supaprastintą paaiškinimą ir pagrindines sąlygas;
- sukūrimo ir atnaujinimo laiką.

Pritaikyti migracijas PostgreSQL duomenų bazėje:

```powershell
cd C:\Users\legat\Desktop\Coding\DocAuditor
docker compose up -d db
cd backend
C:\Users\legat\AppData\Local\Python\pythoncore-3.14-64\python.exe manage.py migrate
```

Jei pakeisite modelius, sugeneruokite naują migraciją ir ją pritaikykite:

```powershell
C:\Users\legat\AppData\Local\Python\pythoncore-3.14-64\python.exe manage.py makemigrations
C:\Users\legat\AppData\Local\Python\pythoncore-3.14-64\python.exe manage.py migrate
```

Administratoriaus paskyrai sukurti:

```powershell
C:\Users\legat\AppData\Local\Python\pythoncore-3.14-64\python.exe manage.py createsuperuser
```

Tada administravimo langas pasiekiamas adresu
`http://127.0.0.1:8000/admin/`. Įkelti dokumentai saugomi `backend/media/documents/`
kataloge, o jų metaduomenys — PostgreSQL lentelėje `api_document`.

## DI tiekėjo pasirinkimas

- `AI_PROVIDER=gemini` naudoja `GEMINI_API_KEY` ir `GEMINI_MODEL`;
- `AI_PROVIDER=ollama` naudoja `OLLAMA_BASE_URL` ir `OLLAMA_MODEL`.

Ollama atveju atskirai įdiekite Ollama ir atsisiųskite pasirinktą modelį, pavyzdžiui:

```powershell
ollama pull llama3.2
```
