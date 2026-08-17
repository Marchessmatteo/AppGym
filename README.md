# 🏋️‍♂️ Gym Tracker Pro

App multi-utente di tracciamento allenamenti, costruita con **Streamlit** e **MySQL**, per creare schede personalizzate, registrare serie, carichi, velocità, salti e monitorare i progressi nel tempo con grafici interattivi.

Nata come progetto personale di apprendimento pratico su dati reali (Python, database, data analysis), oggi supporta più utenti con login indipendente, schede su misura e metriche avanzate ispirate al Velocity Based Training.

🔗 **App live:** https://appgym-j7pg2yvwqfna97clbdjkj6.streamlit.app/
---

## ✨ Funzionalità

### Autenticazione
- **Login con nome utente + PIN** a 4 cifre (nessuna email richiesta): al primo accesso il PIN viene impostato automaticamente
- Dati completamente isolati per utente: ogni persona vede solo le proprie schede, allenamenti, corse e pesature

### Schede personalizzate
- Creazione di **schede su misura**: per ogni esercizio si scelgono serie, ripetizioni target, un obiettivo di carico (kg) opzionale e note libere
- Catalogo condiviso di **oltre 90 esercizi**, selezionabili da menu a tendina (anche nella modalità libera "Giorno Jolly", per evitare nomi incoerenti)
- Visualizzazione, modifica al volo (serie/reps) ed eliminazione delle schede salvate
- Pulsante **"▶️ Guarda esecuzione"** per gli esercizi che hanno un video dimostrativo collegato

### Allenamento
- Selezione della sessione tra le proprie schede, **Corsa** o **Giorno Jolly** (allenamento libero)
- Inserimento rapido di serie, ripetizioni, carico (kg), con avanzamento automatico del numero di serie
- **Velocità di esecuzione (m/s)**, con classificazione automatica nella zona di forza corrispondente (Forza Assoluta, Accelerativa, Forza-Velocità, Velocità-Forza, Forza Iniziale)
- **Altezza/distanza (cm)** per gli esercizi di salto (CMJ, Box Jump, Broad Jump, Pogo Jumps), al posto del carico
- Promemoria dell'ultima sessione registrata per l'esercizio selezionato
- Timer di recupero (60s / 90s / 120s) e timer dedicato per il BattleRope

### Corsa
- Tre modalità: Scatti, Corsa Lunga, Ripetute 400m
- Calcolo automatico del ritmo medio (min/km) per la corsa lunga
- Storico corse con eliminazione selettiva

### Monitoraggio
- **Check-in giornaliero sul sonno**: una volta al giorno, richiede le ore dormite e mostra un messaggio di incoraggiamento o cautela in base al riposo
- **Grafici interattivi (Plotly)** per ogni esercizio: andamento dei carichi, massimo per sessione, linea obiettivo dinamica (presa dalla scheda), hover con la velocità registrata
- Stima automatica della data di raggiungimento dell'obiettivo, basata sulla progressione settimanale
- Tracciamento del peso corporeo con grafico e obiettivo target
- Gestione cronologia selettiva: tabella con le ultime sessioni ed eliminazione righe

---

## 🛠️ Stack tecnico

| Componente         | Tecnologia                          |
|---------------------|--------------------------------------|
| Frontend / App       | [Streamlit](https://streamlit.io)   |
| Database             | MySQL (hosting: [Railway](https://railway.app)) |
| ORM / Connessione DB | SQLAlchemy + PyMySQL                |
| Grafici              | Plotly                              |
| Analisi dati          | Python (pandas) in JupyterLab       |
| Dashboard analitica   | Power BI                            |
| Gestione variabili   | python-dotenv (per il notebook)     |
| Hosting app          | Streamlit Community Cloud           |
| Versionamento        | GitHub                              |

---

## 📁 Struttura del progetto

```
AppGym/
├── app_palestra.py        # App principale Streamlit
├── pulizia_dati.ipynb     # Notebook di pulizia/analisi dati per Power BI
├── pswgym.env              # Credenziali DB per il notebook (locale, non versionato)
├── requirements.txt        # Dipendenze Python
├── .streamlit/
│   └── secrets.toml        # Credenziali DB per l'app (locale, non versionato)
└── README.md
```

---

## ⚙️ Setup locale

### 1. Clona il repository

```bash
git clone https://github.com/<tuo-username>/gym-tracker.git
cd gym-tracker
```

### 2. Installa le dipendenze

```bash
pip install -r requirements.txt
```

`requirements.txt` include:
```
streamlit
pandas
sqlalchemy
pymysql
python-dotenv
plotly
```

### 3. Configura le credenziali del database

Crea un file `.streamlit/secrets.toml` (locale, **non caricarlo su GitHub**) con questa struttura:

```toml
user = "root"
pw = "la-tua-password"
host = "tramway.proxy.rlwy.net"
port = "la-tua-porta"
db = "railway"
```

> ⚠️ Il database usa MySQL su Railway. In alternativa puoi puntare a un database MySQL locale ricreando lo stesso schema (vedi sotto).

### 4. Avvia l'app

```bash
streamlit run app_palestra.py
```

---

## 🗄️ Schema del database

Il database è organizzato attorno a un sistema multi-utente con catalogo esercizi condiviso e schede personalizzate.

**`Utenti`** — anagrafica utenti

| Colonna | Tipo | Descrizione |
|---|---|---|
| `id` | INT (PK, AI) | Identificativo utente |
| `nome_utente` | VARCHAR (UNIQUE) | Nome scelto in fase di login |
| `pin` | VARCHAR(4) | PIN a 4 cifre |
| `data_creazione` | TIMESTAMP | Data di primo accesso |

**`Esercizi`** — catalogo condiviso

| Colonna | Tipo | Descrizione |
|---|---|---|
| `id` | INT (PK, AI) | Identificativo esercizio |
| `nome_esercizio` | VARCHAR (UNIQUE) | Nome dell'esercizio |
| `categoria` | VARCHAR | Categoria muscolare (opzionale) |
| `link_video` | VARCHAR | Link al video dimostrativo (opzionale) |

**`Schede`** e **`Scheda_Esercizi`** — piani personalizzati

| Tabella | Colonne principali |
|---|---|
| `Schede` | `id`, `utente_id`, `nome_scheda`, `data_creazione` |
| `Scheda_Esercizi` | `id`, `scheda_id`, `esercizio_id`, `serie_n`, `ripetizioni`, `ordine`, `obiettivo_kg`, `note` |

**`sessioni_allenamento`** — log storico degli allenamenti

| Colonna | Tipo | Descrizione |
|---|---|---|
| `id` | INT (PK, AI) | Identificativo riga |
| `data_allenamento` | DATE | Data della sessione |
| `giorno_scheda` | VARCHAR | Nome della scheda usata |
| `esercizio` | VARCHAR | Nome dell'esercizio |
| `serie_n` | INT | Numero di serie |
| `ripetizioni` | INT | Ripetizioni |
| `carico_kg` | DECIMAL | Carico in kg |
| `velocita_ms` | DECIMAL | Velocità di esecuzione in m/s (opzionale) |
| `altezza_cm` | DECIMAL | Altezza/distanza del salto in cm (opzionale) |
| `note` | TEXT | Note libere |
| `utente_id` | INT (FK) | Utente proprietario della riga |

**`sessioni_corsa`** — log delle sessioni di corsa (scatti, corsa lunga, ripetute)

**`peso_corporeo`** — misurazioni periodiche del peso

**`Sonno`** — check-in giornaliero sulle ore di sonno

---

## 🚀 Deploy su Streamlit Cloud

1. Pusha il codice su un repository GitHub
2. Vai su [share.streamlit.io](https://share.streamlit.io) e collega il repository
3. Imposta il file principale su `app_palestra.py`
4. Aggiungi le credenziali del database nelle **Secrets** dell'app (stesso formato del `secrets.toml` locale)
5. Deploy 🎉

---

## 📊 Analisi dati e dashboard

Il notebook `pulizia_dati.ipynb` si collega al database Railway ed esegue:
- Estrazione e pulizia dei dati grezzi
- Calcolo del volume di lavoro (serie × reps × kg), con stima basata sul peso corporeo per gli esercizi a corpo libero
- Classificazione automatica della velocità nelle zone di forza
- Suddivisione in fasi di programmazione (es. Costruzione / Espressione)
- Esportazione in CSV, pronti per l'importazione in Power BI

La dashboard Power BI (in costruzione) è pensata per offrire un'analisi professionale delle performance, oltre la semplice visualizzazione dei dati grezzi.

---

## 📝 Note

Progetto personale nato a scopo di apprendimento (sviluppo app, data analysis, gestione database), evoluto in un'applicazione multi-utente. L'app è pensata per restare gratuita; l'analisi approfondita delle performance è pensata come possibile servizio a valore aggiunto in futuro.
