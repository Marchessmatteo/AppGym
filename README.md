# 🏋️‍♂️ Gym Tracker Pro

App personale di tracciamento allenamenti, costruita con **Streamlit** e **MySQL**, per registrare serie, carichi, corse e monitorare i progressi nel tempo con grafici interattivi.

Nata come progetto di apprendimento pratico su dati reali, per allenarmi con Python, database e data analysis.

🔗 **App live:** _[inserisci qui il link Streamlit Cloud]_

---

## ✨ Funzionalità

- **Scheda di allenamento strutturata** su 4 giorni (Giorno 1-3 in palestra, Giorno 4 corsa), con esercizi predefiniti
- **Giorno Jolly**: giornata di allenamento libera con esercizi personalizzati inseriti a mano
- **Modalità Admin / Guest**: gli ospiti possono inserire dati di prova senza che vengano salvati nel database
- **Tracciamento corse**: distanza, tempo, calcolo automatico del ritmo medio (min/km), obiettivo settimanale di 10 km
- **Timer di recupero** (60s / 90s / 120s) e timer dedicato per il BattleRope
- **Inserimento serie rapido**: serie, ripetizioni, carico (kg) e note (es. RPE), con avanzamento automatico della serie
- **Promemoria ultimo carico**: mostra l'ultima sessione registrata per l'esercizio selezionato
- **Grafici interattivi (Plotly)**:
  - andamento dei carichi per ogni serie
  - linea del massimo per sessione
  - linea obiettivo personalizzata per esercizio
  - stima automatica della data di raggiungimento dell'obiettivo, basata sulla progressione settimanale
- **Tracciamento del peso corporeo**: grafico dei progressi con obiettivo target
- **Gestione cronologia selettiva**: tabella con le ultime sessioni, con possibilità di selezionare ed eliminare righe

---

## 🛠️ Stack tecnico

| Componente         | Tecnologia                          |
|---------------------|--------------------------------------|
| Frontend / App       | [Streamlit](https://streamlit.io)   |
| Database             | MySQL (hosting: [Railway](https://railway.app)) |
| ORM / Connessione DB | SQLAlchemy + PyMySQL                |
| Grafici              | Plotly                              |
| Gestione variabili   | python-dotenv                       |
| Hosting app          | Streamlit Community Cloud           |
| Versionamento        | GitHub                              |

---

## 📁 Struttura del progetto

```
gym-tracker/
├── app_palestra.py       # App principale Streamlit
├── requirements.txt      # Dipendenze Python
├── .streamlit/
│   └── secrets.toml      # Credenziali DB (locale, non versionato)
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
db = "railway"
```

> ⚠️ Il database usa MySQL su Railway (piano a pagamento). In alternativa puoi puntare a un database MySQL locale creando lo stesso schema (vedi sotto).

### 4. Avvia l'app

```bash
streamlit run app_palestra.py
```

---

## 🗄️ Schema del database

La tabella principale è `sessioni_allenamento`:

| Colonna            | Tipo          | Descrizione                          |
|---------------------|---------------|----------------------------------------|
| `id`                | INT (PK, AI)  | Identificativo riga                    |
| `data_allenamento`  | DATE          | Data della sessione                    |
| `giorno_scheda`     | VARCHAR       | Giorno della scheda (es. "Giorno 1")   |
| `esercizio`         | VARCHAR       | Nome dell'esercizio                    |
| `serie_n`           | INT           | Numero di serie                        |
| `ripetizioni`       | INT           | Ripetizioni (o minuti, per la corsa)  |
| `carico_kg`         | FLOAT         | Carico in kg (o km, per la corsa)     |
| `note`              | TEXT          | Note libere (es. RPE, ritmo corsa)    |

---

## 🚀 Deploy su Streamlit Cloud

1. Pusha il codice su un repository GitHub pubblico
2. Vai su [share.streamlit.io](https://share.streamlit.io) e collega il repository
3. Imposta il file principale su `app_palestra.py`
4. Aggiungi le credenziali del database nelle **Secrets** dell'app (stesso formato del `secrets.toml` locale)
5. Deploy 🎉

---

## 📊 Prossimi sviluppi

- [ ] Notebook Jupyter di analisi dati: progressione, costanza e volume di allenamento a partire dal database Railway
- [ ] Ulteriori metriche di data analysis (es. distribuzione del volume settimanale, confronto tra esercizi)

---

## 📝 Note

Progetto personale a scopo di apprendimento (data analysis, Python, database, deploy di app). Non pensato per un uso multi-utente su larga scala.
