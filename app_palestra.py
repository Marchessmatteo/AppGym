import streamlit as st
import pandas as pd
import sqlalchemy
import plotly.graph_objects as go
import time
from datetime import date

# --- 1. CONFIGURAZIONE PAGINA & STILE ---
st.set_page_config(page_title="Gym Tracker Pro", page_icon="🏋️‍♂️", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0B1120; color: #FFFFFF; }
    label, .stWidget label, div[data-testid="stWidgetLabel"] p {
        color: #3B82F6 !important;
        font-weight: bold !important;
        font-size: 18px !important;
    }
    input {
        color: #000000 !important;
        background-color: #FFFFFF !important;
    }
    .stButton>button {
        background-color: #3B82F6 !important;
        color: white !important;
        font-weight: bold;
        border: 1px solid #60A5FA !important;
    }
    .stProgress > div > div > div > div {
        background-color: #3B82F6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNESSIONE DATABASE ---
@st.cache_resource
def get_engine():
    return sqlalchemy.create_engine(
        f"mysql+pymysql://{st.secrets['user']}:{st.secrets['pw']}@{st.secrets['host']}:{st.secrets['port']}/{st.secrets['db']}",
        pool_size=2,
        max_overflow=0,
        pool_recycle=300,
        pool_pre_ping=True
    )

engine = get_engine()

# --- 6. TITOLO E LOGIN (nome utente + PIN) ---
st.title("🏋️‍♂️ Il mio registro di allenamento")

if 'utente_id' not in st.session_state:
    st.session_state.utente_id = None
    st.session_state.nome_utente = None

if st.session_state.utente_id is None:
    st.write("### Chi sei?")
    nome_inserito = st.text_input("Nome utente")
    pin_inserito = st.text_input("PIN (4 cifre)", type="password", max_chars=4)

    if st.button("Entra"):
        nome_pulito = nome_inserito.strip()
        if nome_pulito == "" or pin_inserito == "":
            st.error("Inserisci nome e PIN!")
        elif not pin_inserito.isdigit() or len(pin_inserito) != 4:
            st.error("Il PIN deve essere di 4 cifre numeriche!")
        else:
            with engine.connect() as conn:
                risultato = conn.execute(sqlalchemy.text(
                    "SELECT id, pin FROM Utenti WHERE nome_utente = :nome"
                ), {"nome": nome_pulito}).fetchone()

                if risultato:
                    utente_id_trovato, pin_salvato = risultato
                    if pin_salvato is None:
                        conn.execute(sqlalchemy.text(
                            "UPDATE Utenti SET pin = :pin WHERE id = :id"
                        ), {"pin": pin_inserito, "id": utente_id_trovato})
                        conn.commit()
                        st.session_state.utente_id = utente_id_trovato
                        st.session_state.nome_utente = nome_pulito
                        st.rerun()
                    elif pin_salvato == pin_inserito:
                        st.session_state.utente_id = utente_id_trovato
                        st.session_state.nome_utente = nome_pulito
                        st.rerun()
                    else:
                        st.error("PIN errato!")
                else:
                    conn.execute(sqlalchemy.text(
                        "INSERT INTO Utenti (nome_utente, pin) VALUES (:nome, :pin)"
                    ), {"nome": nome_pulito, "pin": pin_inserito})
                    conn.commit()
                    nuovo = conn.execute(sqlalchemy.text(
                        "SELECT id FROM Utenti WHERE nome_utente = :nome"
                    ), {"nome": nome_pulito}).fetchone()
                    st.session_state.utente_id = nuovo[0]
                    st.session_state.nome_utente = nome_pulito
                    st.rerun()
    st.stop()

st.success(f"✅ Connesso come {st.session_state.nome_utente}")

# --- 6.5 GESTIONE SCHEDE ---
st.divider()
with st.expander("📋 Le mie Schede"):
    if 'creazione_scheda' not in st.session_state:
        st.session_state.creazione_scheda = False

    if not st.session_state.creazione_scheda:
        # --- Elenco schede esistenti ---
        with engine.connect() as conn:
            schede_utente = conn.execute(sqlalchemy.text("""
                SELECT id, nome_scheda FROM Schede
                WHERE utente_id = :uid
                ORDER BY data_creazione DESC
            """), {"uid": st.session_state.utente_id}).fetchall()

        if schede_utente:
            st.write("#### Schede salvate")
            for scheda_id, nome in schede_utente:
                with engine.connect() as conn:
                    esercizi_scheda = conn.execute(sqlalchemy.text("""
                        SELECT e.nome_esercizio, se.serie_n, se.ripetizioni, se.obiettivo_kg, se.note
                        FROM Scheda_Esercizi se
                        JOIN Esercizi e ON se.esercizio_id = e.id
                        WHERE se.scheda_id = :sid
                        ORDER BY se.ordine ASC
                    """), {"sid": scheda_id}).fetchall()

                col_nome, col_del = st.columns([4, 1])
                col_nome.write(f"**{nome}**")
                if col_del.button("🗑️", key=f"del_scheda_{scheda_id}"):
                    with engine.connect() as conn:
                        conn.execute(sqlalchemy.text(
                            "DELETE FROM Scheda_Esercizi WHERE scheda_id = :sid"
                        ), {"sid": scheda_id})
                        conn.execute(sqlalchemy.text(
                            "DELETE FROM Schede WHERE id = :sid AND utente_id = :uid"
                        ), {"sid": scheda_id, "uid": st.session_state.utente_id})
                        conn.commit()
                    st.rerun()

                for nome_es, serie_n, reps, obj_kg, note_es in esercizi_scheda:
                    riga = f"　{nome_es} — {serie_n}x{reps}"
                    if obj_kg:
                        riga += f" | 🎯 {obj_kg} kg"
                    if note_es:
                        riga += f" | 📝 {note_es}"
                    st.caption(riga)
            st.divider()

        # --- Pulsante crea nuova ---
        if st.button("➕ Crea nuova scheda"):
            st.session_state.creazione_scheda = True
            st.session_state.esercizi_scheda_temp = []
            st.rerun()
    else:
        st.write("### Nuova scheda")
        nome_scheda = st.text_input("Nome scheda", placeholder="Es. Scheda A - Petto/Tricipiti", key="nome_nuova_scheda")

        col_a, col_b = st.columns(2)
        if col_a.button("✅ Continua"):
            if nome_scheda.strip() == "":
                st.error("Inserisci un nome per la scheda!")
            else:
                st.session_state.nome_scheda_temp = nome_scheda.strip()
                st.rerun()
        if col_b.button("❌ Annulla"):
            st.session_state.creazione_scheda = False
            st.rerun()

        if 'nome_scheda_temp' in st.session_state:
            st.success(f"Scheda: **{st.session_state.nome_scheda_temp}**")

            st.write("#### Aggiungi esercizio")
            with engine.connect() as conn:
                lista_esercizi = conn.execute(sqlalchemy.text(
                    "SELECT id, nome_esercizio FROM Esercizi ORDER BY nome_esercizio ASC"
                )).fetchall()

            opzioni_esercizi = {nome: id for id, nome in lista_esercizi}
            esercizio_scelto = st.selectbox("Esercizio", list(opzioni_esercizi.keys()), key="sel_esercizio_scheda")

            col_s, col_r = st.columns(2)
            serie_target = col_s.number_input("Serie", 1, 10, 3, key="serie_target_scheda")
            reps_target = col_r.number_input("Ripetizioni", 1, 50, 8, key="reps_target_scheda")

            obiettivo_kg_input = st.number_input("Obiettivo Kg (opzionale)", 0.0, 300.0, 0.0, key="obiettivo_target_scheda")
            note_input = st.text_input("Note (opzionale)", key="note_target_scheda")

            if st.button("➕ Aggiungi alla scheda"):
                st.session_state.esercizi_scheda_temp.append({
                    "esercizio_id": opzioni_esercizi[esercizio_scelto],
                    "nome": esercizio_scelto,
                    "serie": serie_target,
                    "reps": reps_target,
                    "obiettivo": obiettivo_kg_input if obiettivo_kg_input > 0 else None,
                    "note": note_input if note_input.strip() != "" else None
                })
                st.rerun()

            if st.session_state.esercizi_scheda_temp:
                st.write("#### Esercizi nella scheda")
                for i, es in enumerate(st.session_state.esercizi_scheda_temp):
                    st.write(f"{i+1}. **{es['nome']}** — {es['serie']}x{es['reps']}")

                st.divider()
                if st.button("💾 Salva Scheda Definitiva", type="primary"):
                    with engine.connect() as conn:
                        conn.execute(sqlalchemy.text("""
                            INSERT INTO Schede (utente_id, nome_scheda)
                            VALUES (:uid, :nome)
                        """), {"uid": st.session_state.utente_id, "nome": st.session_state.nome_scheda_temp})
                        conn.commit()

                        nuova_scheda = conn.execute(sqlalchemy.text("""
                            SELECT id FROM Schede
                            WHERE utente_id = :uid AND nome_scheda = :nome
                            ORDER BY id DESC LIMIT 1
                        """), {"uid": st.session_state.utente_id, "nome": st.session_state.nome_scheda_temp}).fetchone()
                        scheda_id = nuova_scheda[0]

                        for ordine, es in enumerate(st.session_state.esercizi_scheda_temp, start=1):
                            conn.execute(sqlalchemy.text("""
                                INSERT INTO Scheda_Esercizi (scheda_id, esercizio_id, serie_n, ripetizioni, ordine, obiettivo_kg, note)
                                VALUES (:sid, :eid, :s, :r, :o, :obj, :n)
                            """), {"sid": scheda_id, "eid": es["esercizio_id"], "s": es["serie"], "r": es["reps"], "o": ordine, "obj": es["obiettivo"], "n": es["note"]})
                        conn.commit()

                    st.success("✅ Scheda salvata con successo!")
                    st.session_state.creazione_scheda = False
                    del st.session_state.nome_scheda_temp
                    del st.session_state.esercizi_scheda_temp
                    st.rerun()

# --- 7. SELEZIONE GIORNO ---
with engine.connect() as conn:
    schede_disponibili = conn.execute(sqlalchemy.text("""
        SELECT id, nome_scheda FROM Schede
        WHERE utente_id = :uid
        ORDER BY data_creazione DESC
    """), {"uid": st.session_state.utente_id}).fetchall()

mappa_schede = {nome: sid for sid, nome in schede_disponibili}
opzioni_sessione = list(mappa_schede.keys()) + ["Corsa", "Giorno Jolly"]

if not schede_disponibili:
    st.info("💡 Non hai ancora creato schede — apri '📋 Le mie Schede' sopra per crearne una, oppure usa 'Giorno Jolly' per allenarti liberamente.")

giorno_sel = st.selectbox("Seleziona Sessione", opzioni_sessione)
data_sel = st.date_input("Data", date.today())

# --- 8. SEZIONE CORSA ---
if giorno_sel == "Corsa":
    st.divider()
    st.subheader("🏃‍♂️ Tipo di Corsa")

    tipo_corsa = st.selectbox("Seleziona tipo", ["Scatti", "Corsa Lunga", "Ripetute 400m"])

    st.divider()

    if tipo_corsa == "Scatti":
        st.write("### ⚡ Scatti")
        if 'n_serie' not in st.session_state:
            st.session_state.n_serie = 1

        col1, col2 = st.columns(2)
        serie = col1.number_input("Numero scatto", 1, 30, step=1, value=st.session_state.n_serie, key="scatto_n")
        metri = col2.number_input("Metri", 0, 500, 0, step=5, key="scatto_m")
        col3, col4 = st.columns(2)
        ritmo = col3.text_input("Ritmo (es. 4:30)", key="scatto_r")
        bpm = col4.number_input("BPM", 0, 220, 0, key="scatto_bpm")
        note = st.text_input("Note", key="scatto_note")

        if True:
            if st.button("SALVA SCATTO E AVANZA ➡️"):
                with engine.connect() as conn:
                    conn.execute(sqlalchemy.text("""
                        INSERT INTO sessioni_corsa
                            (data_allenamento, tipo_corsa, serie_n, metri, ritmo, bpm, note, utente_id)
                        VALUES (:d, :t, :s, :m, :r, :b, :n, :uid)
                    """), {"d": data_sel, "t": tipo_corsa, "s": serie, "m": metri, "r": ritmo, "b": bpm if bpm > 0 else None, "n": note, "uid": st.session_state.utente_id})
                    conn.commit()
                st.session_state.n_serie += 1
                st.rerun()
            if st.button("Reset Scatto (Torna a 1)"):
                st.session_state.n_serie = 1
                st.rerun()

    elif tipo_corsa == "Corsa Lunga":
        st.write("### 🏃 Corsa Lunga")
        col1, col2 = st.columns(2)
        metri = col1.number_input("Distanza (metri)", 0, 50000, 0, step=100, key="lunga_m")
        minuti = col2.number_input("Tempo (minuti)", 0.0, 300.0, 0.0, step=0.5, key="lunga_min")
        col3, col4 = st.columns(2)
        ritmo = col3.text_input("Ritmo medio (es. 5:30)", key="lunga_r")
        bpm = col4.number_input("BPM medio", 0, 220, 0, key="lunga_bpm")
        note = st.text_input("Note", key="lunga_note")

        if metri > 0 and minuti > 0:
            km = metri / 1000
            ritmo_calc = minuti / km
            min_r = int(ritmo_calc)
            sec_r = int((ritmo_calc - min_r) * 60)
            st.metric("🏃 Ritmo calcolato", f"{min_r}:{sec_r:02d} min/km")

        if True:
            if st.button("SALVA CORSA LUNGA"):
                with engine.connect() as conn:
                    conn.execute(sqlalchemy.text("""
                        INSERT INTO sessioni_corsa
                            (data_allenamento, tipo_corsa, serie_n, metri, minuti, ritmo, bpm, note, utente_id)
                        VALUES (:d, :t, 1, :m, :min, :r, :b, :n, :uid)
                    """), {"d": data_sel, "t": tipo_corsa, "m": metri, "min": minuti if minuti > 0 else None, "r": ritmo, "b": bpm if bpm > 0 else None, "n": note, "uid": st.session_state.utente_id})
                    conn.commit()
                st.success("Corsa salvata!")
                st.rerun()

    elif tipo_corsa == "Ripetute 400m":
        st.write("### 🔄 Ripetute")
        if 'n_serie' not in st.session_state:
            st.session_state.n_serie = 1

        col1, col2 = st.columns(2)
        serie = col1.number_input("Numero ripetuta", 1, 30, step=1, value=st.session_state.n_serie, key="rip_n")
        metri = col2.number_input("Metri", 0, 1000, 400, step=50, key="rip_m")
        col3, col4 = st.columns(2)
        ritmo = col3.text_input("Ritmo (es. 4:30)", key="rip_r")
        bpm = col4.number_input("BPM", 0, 220, 0, key="rip_bpm")
        note = st.text_input("Note", key="rip_note")

        if True:
            if st.button("SALVA RIPETUTA E AVANZA ➡️"):
                with engine.connect() as conn:
                    conn.execute(sqlalchemy.text("""
                        INSERT INTO sessioni_corsa
                            (data_allenamento, tipo_corsa, serie_n, metri, ritmo, bpm, note, utente_id)
                        VALUES (:d, :t, :s, :m, :r, :b, :n, :uid)
                    """), {"d": data_sel, "t": tipo_corsa, "s": serie, "m": metri, "r": ritmo, "b": bpm if bpm > 0 else None, "n": note, "uid": st.session_state.utente_id})
                    conn.commit()
                st.session_state.n_serie += 1
                st.rerun()
            if st.button("Reset Ripetuta (Torna a 1)"):
                st.session_state.n_serie = 1
                st.rerun()

    # --- Storico Corsa ---
    st.divider()
    st.subheader("📋 Storico Corsa")
    try:
        with engine.connect() as conn:
            df_corse = pd.read_sql(sqlalchemy.text("""
                SELECT id, data_allenamento AS Data, tipo_corsa AS Tipo,
                       serie_n AS Serie, metri AS Metri, minuti AS Minuti,
                       ritmo AS Ritmo, bpm AS BPM, note AS Note
                FROM sessioni_corsa
                WHERE utente_id = :uid
                ORDER BY data_allenamento DESC, serie_n ASC
                LIMIT 30
            """), conn, params={"uid": st.session_state.utente_id})

        if not df_corse.empty:
            df_corse.insert(0, "Seleziona", False)
            modificato_corse = st.data_editor(
                df_corse, hide_index=True,
                column_config={"id": None, "Seleziona": st.column_config.CheckboxColumn()},
                disabled=["Data", "Tipo", "Serie", "Metri", "Minuti", "Ritmo", "BPM", "Note"],
                use_container_width=True, key="editor_corse"
            )
            ids_da_eliminare = modificato_corse[modificato_corse["Seleziona"] == True]["id"].tolist()
            if ids_da_eliminare:
                if st.button(f"🗑️ ELIMINA {len(ids_da_eliminare)} RIGHE", type="primary", key="elimina_corse"):
                    with engine.connect() as conn:
                        for id_del in ids_da_eliminare:
                            conn.execute(sqlalchemy.text(
                                "DELETE FROM sessioni_corsa WHERE id = :id AND utente_id = :uid"
                            ), {"id": id_del, "uid": st.session_state.utente_id})
                        conn.commit()
                    st.rerun()
        else:
            st.info("Nessuna corsa registrata ancora.")
    except Exception as e:
        st.error(f"Errore: {e}")

# --- 9. SEZIONE GIORNO JOLLY ---
elif giorno_sel == "Giorno Jolly":
    st.divider()
    esercizio_sel = st.text_input("✏️ Nome Esercizio", placeholder="Es. Panca Piana, Leg Press...")

    if esercizio_sel:
        try:
            with engine.connect() as conn:
                result_last = conn.execute(sqlalchemy.text("""
                    SELECT carico_kg, ripetizioni, data_allenamento
                    FROM sessioni_allenamento
                    WHERE esercizio = :ex AND utente_id = :uid
                    ORDER BY data_allenamento DESC, id DESC LIMIT 1
                """), {"ex": esercizio_sel, "uid": st.session_state.utente_id}).fetchone()

            if result_last:
                with engine.connect() as conn:
                    ultime_serie = conn.execute(sqlalchemy.text("""
                        SELECT serie_n, ripetizioni, carico_kg
                        FROM sessioni_allenamento
                        WHERE esercizio = :ex AND utente_id = :uid
                        AND data_allenamento = (SELECT MAX(data_allenamento) FROM sessioni_allenamento WHERE esercizio = :ex AND utente_id = :uid)
                        ORDER BY serie_n ASC
                    """), {"ex": esercizio_sel, "uid": st.session_state.utente_id}).fetchall()
                testo = f"💡 Ultima volta ({result_last[2]}):\n"
                for s in ultime_serie:
                    testo += f"Serie {s[0]}: {s[2]} kg x {s[1]} reps\n"
                st.info(testo)
        except:
            pass

        st.divider()
        if 'n_serie' not in st.session_state:
            st.session_state.n_serie = 1

        col3, col4, col5 = st.columns(3)
        serie  = col3.number_input("Serie", 1, 30, step=1, key="input_serie", value=st.session_state.n_serie)
        reps   = col4.number_input("Reps", 1, 50, 8)
        carico = col5.number_input("Kg", 0.0, 300.0, 0.0)
        note   = st.text_input("Note (es. RPE)")

        if True:
            if st.button("SALVA SERIE E AVANZA ➡️"):
                with engine.connect() as conn:
                    conn.execute(sqlalchemy.text("""
                        INSERT INTO sessioni_allenamento
                            (data_allenamento, giorno_scheda, esercizio, serie_n, ripetizioni, carico_kg, note, utente_id)
                        VALUES (:d, :g, :es, :s, :r, :kg, :n, :uid)
                    """), {"d": data_sel, "g": giorno_sel, "es": esercizio_sel, "s": serie, "r": reps, "kg": carico, "n": note, "uid": st.session_state.utente_id})
                    conn.commit()
                st.session_state.n_serie += 1
                st.rerun()
            if st.button("Reset Serie (Torna a 1)"):
                st.session_state.n_serie = 1
                st.rerun()

# --- 10. SEZIONE PALESTRA (scheda personalizzata) ---
else:
    st.divider()
    scheda_id_sel = mappa_schede[giorno_sel]

    with engine.connect() as conn:
        esercizi_scheda_sel = conn.execute(sqlalchemy.text("""
            SELECT e.id, e.nome_esercizio, se.serie_n, se.ripetizioni, se.obiettivo_kg, se.note
            FROM Scheda_Esercizi se
            JOIN Esercizi e ON se.esercizio_id = e.id
            WHERE se.scheda_id = :sid
            ORDER BY se.ordine ASC
        """), {"sid": scheda_id_sel}).fetchall()

    mappa_esercizi_scheda = {nome: (eid, sn, rp, obj, nt) for eid, nome, sn, rp, obj, nt in esercizi_scheda_sel}
    esercizio_sel = st.selectbox("Esercizio", list(mappa_esercizi_scheda.keys()))

    _, serie_target_sel, reps_target_sel, obiettivo_sel, note_sel = mappa_esercizi_scheda[esercizio_sel]
    info_testo = f"📋 **{esercizio_sel}** — target: {serie_target_sel}x{reps_target_sel}"
    if obiettivo_sel:
        info_testo += f" | 🎯 Obiettivo: {obiettivo_sel} kg"
    if note_sel:
        info_testo += f"\n\n📝 {note_sel}"
    st.info(info_testo)

    try:
        with engine.connect() as conn:
            result_last = conn.execute(sqlalchemy.text("""
                SELECT carico_kg, ripetizioni, data_allenamento
                FROM sessioni_allenamento
                WHERE esercizio = :ex AND utente_id = :uid
                ORDER BY data_allenamento DESC, id DESC LIMIT 1
            """), {"ex": esercizio_sel, "uid": st.session_state.utente_id}).fetchone()

        if result_last:
            with engine.connect() as conn:
                ultime_serie = conn.execute(sqlalchemy.text("""
                    SELECT serie_n, ripetizioni, carico_kg
                    FROM sessioni_allenamento
                    WHERE esercizio = :ex AND utente_id = :uid
                    AND data_allenamento = (SELECT MAX(data_allenamento) FROM sessioni_allenamento WHERE esercizio = :ex AND utente_id = :uid)
                    ORDER BY serie_n ASC
                """), {"ex": esercizio_sel, "uid": st.session_state.utente_id}).fetchall()
            testo = f"💡 Ultima volta ({result_last[2]}):\n"
            for s in ultime_serie:
                testo += f"Serie {s[0]}: {s[2]} kg x {s[1]} reps\n"
            st.info(testo)
    except:
        pass

    # --- Timer di recupero ---
    st.divider()
    st.write("### ⏱️ Recupero")
    col_t1, col_t2, col_t3 = st.columns(3)
    t_60  = col_t1.button("60s")
    t_90  = col_t2.button("90s")
    t_120 = col_t3.button("120s")

    timer_scelto = 0
    if t_60:  timer_scelto = 60
    if t_90:  timer_scelto = 90
    if t_120: timer_scelto = 120

    if timer_scelto > 0:
        placeholder = st.empty()
        for i in range(timer_scelto, -1, -1):
            placeholder.metric("Riposati...", f"{i}s")
            time.sleep(1)
        st.success("👊 TORNA A SPINGERE!")

    # --- Timer BattleRope ---
    if esercizio_sel == "Battle Rope":
        st.divider()
        st.write("### 🕒 Timer BattleRope")
        tempo_rope = st.slider("Seleziona Secondi", 5, 60, 30, key="slider_br")
        if st.button("VIA! 🔥", key="btn_br"):
            barra = st.progress(0)
            for i in range(tempo_rope):
                time.sleep(1)
                barra.progress((i + 1) / tempo_rope)
            st.success("🔥 SESSIONE FINITA!")
            st.balloons()

    # --- Inserimento serie ---
    st.divider()
    if 'n_serie' not in st.session_state:
        st.session_state.n_serie = 1

    col3, col4, col5 = st.columns(3)
    serie  = col3.number_input("Serie", 1, 30, step=1, key="input_serie", value=st.session_state.n_serie)
    reps   = col4.number_input("Reps", 1, 50, 8)
    carico = col5.number_input("Kg", 0.0, 300.0, 0.0)
    note   = st.text_input("Note (es. RPE)")

    if True:
        if st.button("SALVA SERIE E AVANZA ➡️"):
            with engine.connect() as conn:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO sessioni_allenamento
                        (data_allenamento, giorno_scheda, esercizio, serie_n, ripetizioni, carico_kg, note, utente_id)
                    VALUES (:d, :g, :es, :s, :r, :kg, :n, :uid)
                """), {"d": data_sel, "g": giorno_sel, "es": esercizio_sel, "s": serie, "r": reps, "kg": carico, "n": note, "uid": st.session_state.utente_id})
                conn.commit()
            st.session_state.n_serie += 1
            st.rerun()
        if st.button("Reset Serie (Torna a 1)"):
            st.session_state.n_serie = 1
            st.rerun()

    # --- Grafico progressi ---
    st.divider()
    st.subheader("📈 Analisi Carichi")
    try:
        with engine.connect() as conn:
            df_all = pd.read_sql(sqlalchemy.text(
                "SELECT * FROM sessioni_allenamento WHERE utente_id = :uid"
            ), conn, params={"uid": st.session_state.utente_id})
        if not df_all.empty:
            es_scelto = st.selectbox("Scegli esercizio da analizzare:", df_all['esercizio'].unique())
            df_filt = df_all[df_all['esercizio'] == es_scelto].sort_values('data_allenamento')

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_filt['data_allenamento'], y=df_filt['carico_kg'],
                mode='markers', name='Serie',
                marker=dict(color='#FF4B2B', size=8),
                text=df_filt['serie_n'].apply(lambda x: f"Serie {x}"),
                hovertemplate='<b>%{text}</b><br>Kg: %{y}<br>Data: %{x}<extra></extra>'
            ))
            df_max = df_filt.groupby('data_allenamento', as_index=False)['carico_kg'].max()
            fig.add_trace(go.Scatter(
                x=df_max['data_allenamento'], y=df_max['carico_kg'],
                mode='lines+markers', name='Massimo sessione',
                line=dict(color='#00C853', width=2), marker=dict(color='#00C853', size=10)
            ))

            if es_scelto in mappa_esercizi_scheda and mappa_esercizi_scheda[es_scelto][3]:
                obiettivo_grafico = mappa_esercizi_scheda[es_scelto][3]
                fig.add_hline(y=obiettivo_grafico, line_dash="dash", line_color="#FFD700",
                    annotation_text=f"Obiettivo: {obiettivo_grafico:.0f} kg", annotation_position="top right")

            fig.update_layout(
                plot_bgcolor='#0E1117', paper_bgcolor='#0E1117', font_color='#FFFFFF',
                legend=dict(font=dict(color='#FFFFFF')),
                xaxis=dict(gridcolor='#333333'), yaxis=dict(gridcolor='#333333'),
            )
            st.plotly_chart(fig, use_container_width=True)

            if es_scelto in mappa_esercizi_scheda and mappa_esercizi_scheda[es_scelto][3]:
                try:
                    obiettivo_kg = mappa_esercizi_scheda[es_scelto][3]
                    df_filt['data_allenamento'] = pd.to_datetime(df_filt['data_allenamento'])
                    df_filt['settimana'] = df_filt['data_allenamento'].dt.to_period('W')
                    df_sett = df_filt.groupby('settimana')['carico_kg'].max().reset_index().sort_values('settimana').tail(4)
                    if len(df_sett) >= 2:
                        progressione    = df_sett['carico_kg'].diff().dropna().mean()
                        massimo_attuale = df_sett['carico_kg'].iloc[-1]
                        kg_mancanti     = obiettivo_kg - massimo_attuale
                        st.divider()
                        col_a, col_b, col_c = st.columns(3)
                        col_a.metric("🏋️ Massimo attuale", f"{massimo_attuale:.1f} kg")
                        col_b.metric("📈 Progressione/sett", f"+{progressione:.1f} kg")
                        col_c.metric("🎯 Obiettivo", f"{obiettivo_kg:.0f} kg")
                        if kg_mancanti <= 0:
                            st.success("🏆 Obiettivo già raggiunto!")
                        elif progressione <= 0:
                            st.warning("⚠️ Nelle ultime 4 settimane il carico non è aumentato.")
                        else:
                            settimane_mancanti = kg_mancanti / progressione
                            data_arrivo = date.today() + pd.Timedelta(weeks=settimane_mancanti)
                            st.success(f"🗓️ Se continui così raggiungi **{obiettivo_kg:.0f} kg** il **{data_arrivo.strftime('%d %B %Y')}** — tra circa **{settimane_mancanti:.0f} settimane**!")
                    else:
                        st.info("📊 Servono almeno 2 settimane di dati.")
                except Exception as e:
                    st.error(f"Errore stima: {e}")
    except:
        st.info("Aggiungi dati per vedere i grafici.")

# --- 11. GESTIONE CRONOLOGIA ---
if True:
    st.divider()
    st.subheader("🗑️ Gestione Cronologia Selettiva")
    try:
        with engine.connect() as conn:
            df_last = pd.read_sql(sqlalchemy.text("""
                SELECT id, data_allenamento, esercizio, serie_n, ripetizioni, carico_kg, note
                FROM sessioni_allenamento
                WHERE utente_id = :uid
                ORDER BY id DESC LIMIT 20
            """), conn, params={"uid": st.session_state.utente_id})
        if not df_last.empty:
            df_last.insert(0, "Seleziona", False)
            modificato = st.data_editor(
                df_last, hide_index=True,
                column_config={"id": None, "Seleziona": st.column_config.CheckboxColumn()},
                disabled=["data_allenamento", "esercizio", "serie_n", "ripetizioni", "carico_kg", "note"],
                use_container_width=True, key="editor_cronologia"
            )
            ids_da_eliminare = modificato[modificato["Seleziona"] == True]["id"].tolist()
            if ids_da_eliminare:
                if st.button(f"🗑️ ELIMINA {len(ids_da_eliminare)} RIGHE", type="primary", key="elimina_cronologia"):
                    with engine.connect() as conn:
                        for id_del in ids_da_eliminare:
                            conn.execute(sqlalchemy.text(
                                "DELETE FROM sessioni_allenamento WHERE id = :id AND utente_id = :uid"
                            ), {"id": id_del, "uid": st.session_state.utente_id})
                        conn.commit()
                    st.rerun()
        else:
            st.info("Nessun dato registrato.")
    except Exception as e:
        st.error(f"Errore: {e}")

# --- 12. TRACCIAMENTO PESO CORPOREO ---
st.divider()
st.subheader("⚖️ Peso Corporeo")

peso_obiettivo = 78.0

if True:
    col_p1, col_p2 = st.columns(2)
    data_peso = col_p1.date_input("Data misurazione", date.today(), key="data_peso")
    peso_kg = col_p2.number_input("Peso (kg)", min_value=40.0, max_value=200.0, step=0.1, key="peso_kg")
    if st.button("SALVA PESO"):
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text(
                "INSERT INTO peso_corporeo (data_misurazione, peso_kg, utente_id) VALUES (:d, :p, :uid)"
            ), {"d": data_peso, "p": peso_kg, "uid": st.session_state.utente_id})
            conn.commit()
        st.success("Peso salvato!")
        st.rerun()

try:
    with engine.connect() as conn:
        df_peso = pd.read_sql(sqlalchemy.text(
            "SELECT data_misurazione, peso_kg FROM peso_corporeo WHERE utente_id = :uid ORDER BY data_misurazione ASC"
        ), conn, params={"uid": st.session_state.utente_id})
    if not df_peso.empty:
        fig_peso = go.Figure()
        fig_peso.add_trace(go.Scatter(
            x=df_peso['data_misurazione'], y=df_peso['peso_kg'],
            mode='lines+markers', name='Peso',
            line=dict(color='#FF4B2B', width=2), marker=dict(size=8)
        ))
        fig_peso.add_hline(y=peso_obiettivo, line_dash="dash", line_color="#FFD700",
            annotation_text=f"Obiettivo: {peso_obiettivo} kg", annotation_position="top right")
        fig_peso.update_layout(
            plot_bgcolor='#0E1117', paper_bgcolor='#0E1117', font_color='#FFFFFF',
            xaxis=dict(gridcolor='#333333'), yaxis=dict(gridcolor='#333333'),
        )
        st.plotly_chart(fig_peso, use_container_width=True)

        peso_attuale = df_peso['peso_kg'].iloc[-1]
        peso_iniziale = df_peso['peso_kg'].iloc[0]
        kg_persi = peso_iniziale - peso_attuale
        kg_mancanti = peso_attuale - peso_obiettivo

        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("⚖️ Peso attuale", f"{peso_attuale} kg")
        col_s2.metric("📉 Kg persi", f"{kg_persi:.1f} kg")
        col_s3.metric("🎯 Al obiettivo", f"{kg_mancanti:.1f} kg")

        if len(df_peso) >= 2:
            df_peso['data_misurazione'] = pd.to_datetime(df_peso['data_misurazione'])
            df_peso['settimana'] = df_peso['data_misurazione'].dt.to_period('W')
            df_sett_peso = df_peso.groupby('settimana')['peso_kg'].mean().reset_index()
            variazione = df_sett_peso['peso_kg'].diff().dropna().mean()
            if variazione < 0:
                settimane_mancanti = kg_mancanti / abs(variazione)
                data_obiettivo = date.today() + pd.Timedelta(weeks=settimane_mancanti)
                st.success(f"🗓️ Se continui così raggiungi **{peso_obiettivo} kg** il **{data_obiettivo.strftime('%d %B %Y')}** — tra circa **{settimane_mancanti:.0f} settimane**!")
            elif variazione > 0:
                st.warning("⚠️ Il peso sta aumentando nelle ultime settimane!")
            else:
                st.info("📊 Il peso è stabile, continua a spingere!")
    else:
        st.info("Inserisci la prima misurazione!")
except Exception as e:
    st.error(f"Errore: {e}")
