# DocAuditor UML klasių diagramos paaiškinimas

„User“ klasė aprašo sistemos naudotoją, jo registraciją, prisijungimą,
atsijungimą ir jam priklausančius dokumentus bei autentifikavimo sesijas.
„AuthenticationSession“ klasė aprašo naudotojo autentifikavimo sesiją, jos
identifikatorių, sukūrimo ir galiojimo laiką bei būseną. „LoginCredentials“
yra struktūros klasė, sauganti elektroninio pašto adresą ir slaptažodį bei
leidžianti patikrinti jų tinkamumą.

„Document“ klasė aprašo pagrindinį sistemos domeno objektą: dokumento
metaduomenis, failą, sukūrimo ir atnaujinimo laiką, analizės būseną bei
analizės klaidą. Klasė leidžia dokumentą įkelti, išsaugoti, ištrinti ir
peržiūrėti. „DocumentFile“ yra struktūros klasė, apibendrinanti dokumento
failo kelią, formatą ir dydį. „DocumentCollection“ aprašo naudotojo
dokumentų rinkinį ir leidžia dokumentus išvardyti, pridėti, surasti bei
palyginti.

„DocumentAnalysis“ yra struktūros klasė, apibendrinanti sugeneruotą dokumento
santrauką, analizės laiką, galimą klaidą, nustatytas rizikas, privatumo
vertinimą ir pagrindines dokumento sąlygas. Analizė susiejama su dokumentu ir
išsaugoma tik naudotojui pasirinkus analizės išsaugojimo veiksmą. „KeyCondition“
struktūros klasė aprašo analizės metu išskirtą svarbią dokumento sąlygą ir jos
svarbos reikšmę.

„RiskAssessment“ struktūros klasė aprašo vieną nustatytą riziką: jos lygį,
kategoriją, paaiškinimą ir susijusią sutarties sąlygą. „PrivacyAssessment“
struktūros klasė aprašo renkamus asmens duomenis, jų naudojimo tikslus,
saugojimo terminą, perdavimą trečiosioms šalims, perdavimą už Europos
Sąjungos arba Europos ekonominės erdvės ribų, rinkodarą be sutikimo ir
privatumo santrauką.

„AIProvider“ yra sąsaja, apibrėžianti bendras analizės teksto generavimo ir
teikėjo pasiekiamumo operacijas. „GeminiProvider“ yra pagrindinis dirbtinio
intelekto teikėjas, o „OllamaProvider“ – atsarginis teikėjas. Abi klasės
įgyvendina „AIProvider“ sąsają, gali būti inicializuojamos, generuoti atsakymą
ir patikrinti savo pasiekiamumą.

Diagramoje pateiktos keturios sąrašo klasės. „AnalysisStatus“ apibrėžia
dokumento analizės būsenas: laukiama, analizuojama, baigta arba nepavykusi.
„DocumentFormat“ apibrėžia palaikomus PDF, DOC ir DOCX formatus.
„AuthenticationStatus“ apibrėžia aktyvią, pasibaigusią arba nutrauktą
autentifikavimo sesiją. „RiskLevel“ apibrėžia didelės, vidutinės ir mažos
rizikos lygius.

Klasių ryšiai parodo, kad naudotojas gali turėti daug dokumentų ir
autentifikavimo sesijų, dokumentas turi failą ir gali turėti išsaugotą
analizę, o analizė gali identifikuoti kelias rizikas, privatumo vertinimą ir
pagrindines sąlygas. Dokumentų analizė kreipiasi į „AIProvider“ sąsają, kurią
įgyvendina „GeminiProvider“ ir „OllamaProvider“. Diagrama apima daugiau nei
dešimt klasių, keturias sąrašo klases ir kelias struktūros klases, todėl
atitinka UML klasių diagramos reikalavimus.
