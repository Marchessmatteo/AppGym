import streamlit as st

import pandas as pd

import sqlalchemy

import os

import time

from dotenv import load_dotenv

from datetime import date



# --- 1. CONFIGURAZIONE PAGINA & STILE ---

st.set_page_config(page_title="Gym Tracker Pro", page_icon="🏋️‍♂️", layout="centered")



# CSS per Dark Mode e accenti Arancioni (Stile Palestra)-



# --- 1. CONFIGURAZIONE PAGINA & STILE ---

st.set_page_config(page_title="Gym Tracker Pro", page_icon="🏋️‍♂️", layout="centered")

# CSS aggiornato per etichette Arancioni

# --- 1. CONFIGURAZIONE PAGINA & STILE ---

# --- 1. CONFIGURAZIONE PAGINA & STILE ---

st.set_page_config(page_title="Gym Tracker Pro", page_icon="🏋️‍♂️", layout="centered")



st.markdown("""

    <style>

    /* 1. Sfondo generale scuro */

    .stApp { background-color: #0E1117; color: #FFFFFF; }

    

    /* 2. ETICHETTE (Scegli Giorno, Data, ecc.) - ARANCIONI */

    label, .stWidget label, div[data-testid="stWidgetLabel"] p {

        color: #FF4B2B !important; 

        font-weight: bold !important;

        font-size: 18px !important;

    }



    /* 3. TESTO DENTRO I BOX (Numeri e Date) - NERO SU BIANCO */

    /* Questo risolve il problema delle scritte invisibili */

    input {

        color: #000000 !important; /* Testo nero */

        background-color: #FFFFFF !important; /* Sfondo bianco */

    }



    /* 4. BOTTONI ARANCIONI */

    .stButton>button { 

        background-color: #FF4B2B !important; 

        color: white !important; 

        font-weight: bold;

    }



    /* 5. BARRA PROGRESSO */

    .stProgress > div > div > div > div { 

        background-color: #FF4B2B !important; 

    }

    </style>

    """, unsafe_allow_html=True)

# --- 2. CONNESSIONE DATABASE ---

load_dotenv(dotenv_path="pswgym.env")

engine = sqlalchemy.create_engine(f"mysql+pymysql://{os.getenv('user')}:{os.getenv('pw')}@{os.getenv('host')}/{os.getenv('db')}")



# --- 3. SCHEDA ALLENAMENTO ---

scheda = {

    "Giorno 1": ["BattleRope", "Power Clean 5x5", "Affondi Manubri 3x20", "Trazioni Sbarra 4xmax", "Scaletta Agilità 5min"],

    "Giorno 2": ["Push-up Esplosivi 4x8", "Military Press 4x6", "Dip Parallele 4x10", "Rematore Bilanciere 4x8", "BattleRope"],

    "Giorno 3": ["Squat Bilanciere 4x8", "Burpees 3x12", "Trazioni Presa Inversa 3xmax","Affondi saltati 3x20", "Scaletta + Scatto","PLUNK1 + legraises15 + russian twist20"],

    "Giorno 4": ["Corsa"]

}



st.title("🏋️‍♂️ IL mio registro di allenamento")



# --- 4. SELEZIONE GIORNO ---

giorno_sel = st.selectbox("Seleziona Giorno", list(scheda.keys()))

data_sel = st.date_input("Data", date.today())



# --- 5. LOGICA CONDIZIONALE: CORSA vs PALESTRA ---



if giorno_sel == "Giorno 4":

    # --- SEZIONE CORSA ---

    st.divider()

    st.subheader("🏃‍♂️ Obiettivo Settimanale: 10 KM")

    

    # Calcolo progresso reale dal DB (sommiamo i km salvati come 'carico_kg')

    try:

        df_corsa_db = pd.read_sql("SELECT carico_kg FROM sessioni_allenamento WHERE esercizio = 'Corsa'", engine)

        km_totali = df_corsa_db['carico_kg'].sum()

    except:

        km_totali = 0.0

        

    obiettivo = 10.0

    percentuale = min(km_totali / obiettivo, 1.0)

    

    st.progress(percentuale)

    st.write(f"Hai percorso **{km_totali:.1f} km** su {obiettivo} km previsti!")



    st.divider()

    st.write("⌚ **Sincronizzazione Smartwatch**")

    

    # Inizializziamo variabili di default

    distanza = 0.0

    minuti = 0

    note_corsa = "Sessione Corsa"



    if st.button("Sincronizza dati da Smartwatch"):

        with st.spinner('Connessione al server dell\'orologio...'):

            time.sleep(2) 

            distanza = 4.5  # Dato simulato

            minuti = 25

            note_corsa = "Sincronizzato da Smartwatch"

            st.success(f"✅ Trovata ultima corsa: {distanza} km!")

    else:

        c1, c2 = st.columns(2)

        distanza = c1.number_input("Distanza (km)", min_value=0.0, step=0.1, key="dist_man")

        minuti = c2.number_input("Tempo (min)", min_value=0, step=1, key="time_man")

        note_corsa = st.text_input("Note corsa", key="note_man")



    if st.button("SALVA SESSIONE CORSA"):

        with engine.connect() as conn:

            query = sqlalchemy.text("""

                INSERT INTO sessioni_allenamento (data_allenamento, giorno_scheda, esercizio, serie_n, ripetizioni, carico_kg, note)

                VALUES (:d, :g, 'Corsa', 1, :r, :c, :n)

            """)

            conn.execute(query, {"d": data_sel, "g": giorno_sel, "r": minuti, "c": distanza, "n": note_corsa})

            conn.commit()

        st.rerun()



else:

    # --- SEZIONE PALESTRA (Giorno 1, 2, 3) ---

    st.divider()

    esercizio_sel = st.selectbox("Esercizio", scheda[giorno_sel])

    try:

        query_last = sqlalchemy.text("""

            SELECT carico_kg, ripetizioni, data_allenamento 

            FROM sessioni_allenamento 

            WHERE esercizio = :ex 

            ORDER BY data_allenamento DESC, id DESC LIMIT 1

        """)

        with engine.connect() as conn:

            result_last = conn.execute(query_last, {"ex": esercizio_sel}).fetchone()

        

        if result_last:

            st.info(f"💡 Ultima volta ({result_last[2]}): {result_last[0]} kg x {result_last[1]} reps")

    except:

        pass # Se il database è vuoto, non mostrare errori

    # --- Fine Promemoria ---



    st.divider()

    # 1. TIMER DI RECUPERO (Semplice e veloce)

    st.write("### ⏱️ Recupero")

    col_t1, col_t2, col_t3 = st.columns(3)

    t_60 = col_t1.button("60s")

    t_90 = col_t2.button("90s")

    t_120 = col_t3.button("120s")



    timer_scelto = 0

    if t_60: timer_scelto = 60

    if t_90: timer_scelto = 90

    if t_120: timer_scelto = 120



    if timer_scelto > 0:

        placeholder = st.empty()

        for i in range(timer_scelto, -1, -1):

            placeholder.metric("Riposati...", f"{i}s")

            time.sleep(1)

        st.success("👊 TORNA A SPINGERE!")



    st.divider()



    # 2. AUTO-INCREMENTO SERIE

    # Usiamo la "session_state" di Streamlit per ricordare a che serie sei

    if 'n_serie' not in st.session_state:

        st.session_state.n_serie = 1



    col3, col4, col5 = st.columns(3)

    # Il valore della serie ora è collegato a session_state

    serie = col3.number_input("Serie", 1, 10, step=1, key="input_serie", value=st.session_state.n_serie)

    reps = col4.number_input("Reps", 1, 50, 8)

    carico = col5.number_input("Kg", 0.0, 300.0, 0.0)

    note = st.text_input("Note (es. RPE)")

 # --- TIMER SPECIFICO PER BattleRope ---

    if esercizio_sel == "BattleRope":

        st.divider()

        st.write("### 🕒 Timer BattleRope")

        tempo_rope = st.slider("Seleziona Secondi", 5, 60, 30, key="slider_br")

        

        if st.button("VIA! 🔥", key="btn_br"):

            import time

            barra = st.progress(0)

            for i in range(tempo_rope):

                time.sleep(1)

                progresso = (i + 1) / tempo_rope

                barra.progress(progresso)

            

            st.success("🔥 SESSIONE FINITA!")

            st.balloons()

    # ---------------------------------------



   

            

    if st.button("SALVA SERIE E AVANZA ➡️"):

        with engine.connect() as conn:

            query = sqlalchemy.text("""

                INSERT INTO sessioni_allenamento (data_allenamento, giorno_scheda, esercizio, serie_n, ripetizioni, carico_kg, note)

                VALUES (:d, :g, :es, :s, :r, :kg, :n)

            """)

            conn.execute(query, {"d": data_sel, "g": giorno_sel, "es": esercizio_sel, "s": serie, "r": reps, "kg": carico, "n": note})

            conn.commit()

        

        # QUI SUCCEDE LA MAGIA: aumenta il numero della serie per la prossima volta

        st.session_state.n_serie += 1

        st.rerun()



    # Tasto per resettare la serie se cambi esercizio

    if st.button("Reset Serie (Torna a 1)"):

        st.session_state.n_serie = 1

        st.rerun()



# --- 6. ANALISI PROGRESSI (GRAFICO) ---

st.divider()

st.subheader("📈 Analisi Carichi")

try:

    df_all = pd.read_sql("SELECT * FROM sessioni_allenamento", engine)

    if not df_all.empty:

        es_scelto = st.selectbox("Scegli esercizio da analizzare:", df_all['esercizio'].unique())

        df_filt = df_all[df_all['esercizio'] == es_scelto].sort_values('data_allenamento')

        st.line_chart(data=df_filt, x='data_allenamento', y='carico_kg')

except:

    st.info("Aggiungi dati per vedere i grafici.")



# --- 7. VISUALIZZAZIONE & CANCELLAZIONE ---

st.divider()

st.subheader("🗑️ Gestione Cronologia Selettiva")



try:

    # Carichiamo gli ultimi 10 inserimenti

    query = "SELECT id, data_allenamento, esercizio, ripetizioni, serie_n, carico_kg, note FROM sessioni_allenamento ORDER BY id DESC LIMIT 10"

    df_last = pd.read_sql(query, engine)



    if not df_last.empty:

        # Aggiungiamo una colonna "Elimina" con checkbox (False di default)

        df_last.insert(0, "Seleziona", False)



        # Usiamo data_editor che permette di cliccare sulle checkbox

        modificato = st.data_editor(

            df_last,

            hide_index=True,

            column_config={

                "id": None, # Nascondiamo l'ID

                "Seleziona": st.column_config.CheckboxColumn(help="Spunta per eliminare"),

                "data_allenamento": "Data",

                "esercizio": "Esercizio",

                "ripetizioni": "ripetizioni",

                "carico_kg": "Kg"

            },

            disabled=["data_allenamento", "esercizio","ripetizioni", "serie_n", "carico_kg", "note"], # Impedisce di scrivere nelle celle

            use_container_width=True,

            key="editor_cronologia"

        )



        # Troviamo gli ID delle righe che l'utente ha spuntato

        ids_da_eliminare = modificato[modificato["Seleziona"] == True]["id"].tolist()



        if ids_da_eliminare:

            # Se ci sono righe selezionate, appare il tastone rosso

            if st.button(f"🗑️ ELIMINA {len(ids_da_eliminare)} RIGHE SELEZIONATE", type="primary", use_container_width=True):

                with engine.connect() as conn:

                    for id_del in ids_da_eliminare:

                        conn.execute(sqlalchemy.text(f"DELETE FROM sessioni_allenamento WHERE id = {id_del}"))

                    conn.commit()

                st.success("Righe eliminate con successo!")

                st.rerun()

    else:

        st.info("Nessun dato registrato.")

except Exception as e: