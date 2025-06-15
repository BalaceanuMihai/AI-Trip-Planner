# AI-Trip-Planner
Trip  planner that uses AI to find specific trips based on user preferences

## User Stories

- Ca utilizator, vreau sa pot introduce datele calatoriei într-un chat, astfel încât AI-ul sa-mi inteleaga preferintele.

- Ca utilizator, vreau aă pot alege o destinatie dintr-o lista generata de AI, astfel incat sa personalizez vacanaa.

- Ca utilizator, vreau ca planul de calatorie sa includa zboruri dus-intors, astfel incat sa imi organizez transportul complet.

- Ca utilizator, vreau să văd 3 cele mai bune opțiuni de hoteluri, astfel incat sa aleg cea mai potrivita cazare.

- Ca utilizator, vreau sa primesc sugestii de activitati, astfel încât să imi planific timpul liber.

- Ca utilizator, vreau ca datele mele sa fie salvate in fisiere JSON, astfel incat aplicatia sa imi poata genera rapid un plan.

- Ca utilizator, vreau sa pot accesa planul meu de vacanta dintr-un link, astfel incat sa il consult usor.

- Ca utilizator, vreau ca orele zborurilor ss fie afisate clar, astfel incat sa stiu exact cand plec si cand ajung.

- Ca utilizator, vreau sa pot incheia conversatia si sa primesc sumarul preferintelor mele, astfel incat sa fiu sigur ca totul a fost salvat corect.

- Ca utilizator, vreau ca linkurile din rezultate sa fie interactive, astfel incat sa pot face direct rezervarile.

## Diagrama UML

Este atasata in repository ul proiectului (Diagrama UML.png)

## Git Source Control

- 'main' - Ramura principala, cod stabil
- 'feature/trip-model' - Structura de baza a proiectului
- 'feature/telegramBotConfiguration' - Am incercat sa utilizam un template de tip Telegram pentru chatbot, dar ulterior am optat pentru o interfata facuta manual.
- 'feature/AI-User-Interface' - Am dezvoltat interfata manual de tip chatbot care interactioneaza cu utilizatorul pentru a colecta detalii despre vacanta (ex: destinatie, date, preferinte de activitati).
                              - Am aplicat prompt engineering pentru a ghida conversatia si a genera intrebari relevante.
                              - Raspunsurile oferite de utilizator sunt extrase si salvate automat intr-un fisier JSON, care este ulterior folosit pentru a face cereri catre API-urile de zboruri, cazari si activitati.
- 'feature/FlightsAPI' - In core/planner am creat in flights.py functia care face un request prin API catre KIWi.com si ne returneaza o lista de zboruri catre destinatia aleasa anterior.
- 'feature/hotelAPIpartial' - Am inceput crearea fisierului hotels.py
- 'feature/HotelAPI' - In core/planner am creat in hotels.py functia care face un request prin API catre Booking.com si ne returneaza o lista de cazari in destinatia aleasa anterior.
- 'feature/ActivitiesAPI' - In core/planner am creat in activities.py functia care face un request prin API catre TripAdvisor.com si ne returneaza o lista de posibile activitati in destinatia aleasa anterior.
- 'feature/build-vacation-plan' - In core/planner in fisierul vacation_planner.py am centralizat zborurile, cazarile si activitatile obtinute.
- 'feature/results-template' - Am creat pagina de afisare a planurilor de vacanta, intr-un format user-friendly.


## Rezolvare bug cu Pull Request

Am identificat o eroare în fișierul flights.py, unde datele de plecare și întoarcere nu erau preluate corect, ceea ce ducea la afișarea unor zboruri cu ore și zile aleatorii.
Pentru a remedia problema, am creat branch-ul feature/build-vacation-plan în care:
- am corectat parametrii transmiși în request-ul către API-ul kiwi-cheap-flights;
- am verificat că zborurile returnate corespund exact perioadei selectate de utilizator.

Rezolvarea a fost integrată în main printr-un pull request dedicat.

## Design Patterns

- Aplicat Separation of Concerns: planner ≠ UI ≠ data
- Folosit un pattern simplu de tip Service Layer pentru generate_vacation_plans() → agregare zboruri, hoteluri și activități într-o singură functie.
- Chatul rulează într-un controller Django, iar datele sunt procesate în backend independent.

## Prompt Engineering & Toolori AI

Pe parcursul dezvoltării proiectului am utilizat intensiv tooluri AI precum ChatGPT și GitHub Copilot în două moduri:

1. În procesul de dezvoltare:
- pentru generarea și optimizarea codului HTML/CSS al interfeței chatbotului;
- pentru scrierea funcțiilor backend (salvare date JSON, apeluri API pentru zboruri, hoteluri și activități);
- pentru debugging și explicarea erorilor;

2. În aplicația finală:
- am implementat prompt engineering direct în chatbotul aplicației, care pune întrebări relevante despre preferințele de vacanță (ex: „Care este perioada dorită?”, „Ce tip de activități preferi?”);
- AI-ul folosește aceste răspunsuri pentru a genera automat o listă personalizată de planuri de vacanță;
- planul ales de utilizator este salvat și folosit pentru a interoga API-urile externe.

Astfel, AI-ul a fost integrat atât ca asistent de dezvoltare, cât și ca componentă centrală în experiența utilizatorului.








