# DocAuditor

Pradinis dokumentų analizės sistemos karkasas:

- `frontend/` — HTML5, Tailwind CSS v4 ir Vite v8.3.0;
- `backend/` — Django v6.1 API, veikianti su Python;
- PostgreSQL v18.6 — paleidžiama per `docker-compose.yml`;
- `backend/api/ai.py` — pasirenkamas Gemini API arba lokalaus Ollama modelio tiekėjas.

## Paleidimas

1. Nukopijuokite `backend/.env.example` į `backend/.env` ir įrašykite Gemini
   API raktą bei savo Ollama modelio pavadinimą. Neįkelkite `.env` į Git.
   Django automatiškai perskaito šį failą; esami aplinkos kintamieji turi
   pirmenybę prieš jame nurodytas reikšmes.
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

## API dokumentacija

Paleidus backend, interaktyvi Swagger UI dokumentacija pasiekiama adresu
`http://localhost:8000/api/docs/`. OpenAPI schemą galima gauti adresu
`http://localhost:8000/api/schema/`. Dokumentacija apima sveikatos patikrą,
registraciją ir dokumentų sąrašo bei įkėlimo API.

Atidarius dokumentą galima pasirinkti dvi to paties dokumento versijas ir jas
palyginti. DI ataskaita parodoma lange, o sėkmingo palyginimo atveju ją galima
atsisiųsti PDF formatu.

## Dokumentų saugojimo API

Dokumentų API naudoja prisijungusio Django naudotojo sesiją. Įkėlimas priima
`multipart/form-data` užklausą su vienu `file` lauku:

```text
POST /api/documents/
```

Priimami PDF, DOC ir DOCX failai iki 15 MiB. Sėkmės atveju API grąžina `201`,
pranešimą „Dokumentas išsaugotas sėkmingai“ ir naujo dokumento metaduomenis.
Neprisijungusiems naudotojams grąžinamas `401`, o netinkamam failui — `400` su
klaidos aprašymu.

Prisijungusio naudotojo dokumentų sąrašas:

```text
GET /api/documents/
```

Sąraše pateikiami tik to naudotojo dokumentai. Failai saugomi
`MEDIA_ROOT/documents/`, o dokumentų metaduomenys — `api_document` lentelėje.

Išsaugotą dokumentą galima ištrinti:

```text
DELETE /api/documents/<document_id>/
```

Trinti gali tik dokumento savininkas. Sėkmės atveju grąžinamas `204`, o kartu
pašalinamas ir saugomas failas bei dokumento analizės duomenys.
Sesija galioja per Django autentifikaciją. Prisijungti galima per
`POST /api/auth/login/` (JSON su `email` ir `password`); sėkmės atveju frontend
nukreipia į `/documents`, o nesėkmės atveju rodo „Neteisingai suvesti prisijungimo
duomenys“. Atsijungti galima per `POST /api/auth/logout/`.

## Registracijos patikrinimas

1. Įsitikinkite, kad PostgreSQL veikia (`docker compose ps db`) ir migracijos
   pritaikytos (`python manage.py migrate` iš `backend/` aplanko).
2. Paleiskite backend su `python manage.py runserver`, o atskirame terminale frontend
   su `npm run dev`.
3. Naršyklėje atidarykite `http://localhost:5173/register` ir užregistruokite
   naudotoją. Sėkmės pranešimas reiškia, kad API sukūrė naudotoją.
4. Norėdami patikrinti įrašą PostgreSQL, atidarykite dar vieną terminalą:

   ```powershell
   cd C:\Users\Adminas\Desktop\DocAuditor\backend
   .\.venv\Scripts\Activate.ps1
   python manage.py shell -c "from django.contrib.auth import get_user_model; print(list(get_user_model().objects.values('username', 'email')))"
   ```

   Užregistruotas vartotojo vardas ir el. paštas bus parodyti iš Django naudotojų
   lentelės. Slaptažodis sąraše nerodomas ir DB saugomas maišos pavidalu.

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

Klausimai apie pasirinktą dokumentą per pokalbio langą visada siunčiami į
Gemini API. Backend aplinkoje turi būti nustatytas `GEMINI_API_KEY`; pasirenkamas
`GEMINI_MODEL` numatytai yra `gemini-2.5-flash`.

Gemini ryšiui ir prieinamiems modeliams patikrinti paleiskite backend aplanke:

```powershell
python manage.py check_gemini
```

Komanda naudoja `backend/.env`, rodo sukonfigūruotą modelį ir pateikia modelių
sąrašą. Modelių sąrašas nepatvirtina, kad sukonfigūruotas modelis gali generuoti
atsakymus. Norėdami patikrinti ir generavimą, vykdykite
`python manage.py check_gemini --generate`: Gemini bus nusiųsta trumpa
bandomoji užklausa, bet ne dokumento turinys. Galioja įprasti API naudojimo
apribojimai ir galimi mokesčiai.

Ollama atveju atskirai įdiekite Ollama ir atsisiųskite pasirinktą modelį, pavyzdžiui:

```powershell
ollama pull llama3.2
```

## Bendroji dokumento analizė (US-9)

Prisijungę atidarykite savo dokumentą ir pasirinkite „Analizuoti“. Dokumento
tekstas pirmiausia siunčiamas į „Gemini“ (Google); jei užklausa nepavyksta arba
grąžina tuščią ar ilgesnę nei 700 simbolių santrauką, naudojamas vietinis
„Ollama“. Santrauka išsaugoma kartu su dokumento metaduomenimis. Mygtukas
„Gauti santrauką“ atsisiunčia ją PDF formatu.

„Ollama“ santraukos riba yra 2000 simbolių, todėl jos gali viršyti pradiniame
US-9 reikalavime numatytą 700 simbolių ribą. „Gemini“ riba išlieka 700.
Jeigu „Ollama“ atsakymas viršija 2000 simbolių, vieną kartą pakartotinai
paprašoma dar trumpesnės santraukos. Jei ir ji per ilga, analizė atmetama,
o ne nukerpama sakinio viduryje.

`backend/.env` nustatykite `GEMINI_API_KEY`, o `OLLAMA_MODEL` turi atitikti
`ollama list` rodomą įdiegtą modelį. Pakeitę failą, paleiskite Django iš naujo.
Jei tas pats kintamasis jau nustatytas terminale, naudojama terminalo reikšmė.
Atsarginiam variantui „Ollama“ turi veikti ir turėti atsisiųstą modelį.
Gemini užklausos timeout yra 60 s, Ollama — 120 s.

Analizės klaidos diagnostika rodoma backend terminale: nurodomas tiekėjas,
HTTP būsenos kodas arba tai, kad santrauka tuščia ar viršija tiekėjo ribą.
Dokumento tekstas, API raktas ir teikėjų klaidų turinys į šiuos pranešimus
neįtraukiami. Jei abu tiekėjai nepavyksta, API grąžina 502.

Docker Compose automatiškai neskaito `backend/.env`. Keičiant `POSTGRES_*`
reikšmes Django aplinkoje, būtina atitinkamai sukonfigūruoti ir Compose bei
esamą PostgreSQL duomenų bazę.

PDF ir DOCX tekstas išskiriamas Python bibliotekomis. Senų DOC failų tekstui
reikia įdiegti LibreOffice ir įtraukti `soffice` į PATH arba nurodyti jo kelią
backend aplinkoje, pavyzdžiui:

```powershell
$env:LIBREOFFICE_PATH = "C:\Program Files\LibreOffice\program\soffice.exe"
```

Skaitmeninto vaizdo PDF be teksto, užšifruoti, sugadinti, tušti ir ilgesnį nei
100 000 simbolių tekstą turintys dokumentai neanalizuojami; OCR nevykdomas.
PDF santraukai naudojamas sistemos Unicode šriftas (Windows Arial arba Linux
DejaVu Sans); jei jo nėra, nustatykite `SUMMARY_PDF_FONT` į TTF failo kelią.
Analizė yra DI sugeneruota ir nėra garantuotai teisingas teisinis vertinimas.

API: `POST /api/documents/<id>/analysis/` grąžina `{"summary": "..."}`, o
`GET /api/documents/<id>/summary.pdf` grąžina PDF. Abu prieinami tik dokumento
savininkui; POST užklausai būtina sesija ir CSRF žetonas.
