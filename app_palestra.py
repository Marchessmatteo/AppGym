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
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    label, .stWidget label, div[data-testid="stWidgetLabel"] p {
        color: #FF4B2B !important;
        font-weight: bold !important;
        font-size: 18px !important;
    }
    input {
        color: #000000 !important;
        background-color: #FFFFFF !important;
    }
    .stButton>button {
        background-color: #FF4B2B !important;
        color: white !important;
        font-weight: bold;
    }
    .stProgress > div > div > div > div {
        background-color: #FF4B2B !important;
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

# --- 3. SCHEDA ALLENAMENTO ---
scheda = {
    "⚡ ESPLOSIVITÀ SUPERIORE": [
        "Power Clean 5x5",
        "Military Press 4x6",
        "Rematore Bilanciere 4x8",
        "Push-up Esplosivi 4x8",
        "Plank 3 Appoggi"
    ],
    "💪 FORZA GAMBE": [
        "Squat Bilanciere 4x8",
        "Panca Piana Bilanciere",
        "Trazioni Sbarra 4xmax",
        "Affondi Posteriori Manubri",
        "Copenhagen Plank"
    ],
    "Corsa": ["Corsa"],
    "Giorno Jolly": ["Esercizio Libero"]
}
# --- 4. NOTE ESERCIZI ---
note_esercizi = {
    "Power Clean 5x5": "4 serie × 4 reps | Carico: ~50-55 kg | Focus: massima velocità di spinta | Recupero: 2 min",
    "Military Press 4x6": "4 serie × 6 reps | Carico: ~46-54 kg | Pesante controllato | Recupero: 2 min",
    "Rematore Bilanciere 4x8": "4 serie × 8 reps | Carico: ~70-84 kg | Schiena forte | Recupero: 90 sec",
    "Push-up Esplosivi 4x8": "3 serie × 6 reps | Stacca le mani da terra quando spingi | Recupero: 60 sec",
    "Plank 3 Appoggi": "3 serie × 45 sec | Solleva un piede alla volta alternando | Recupero: 45 sec",
    "Squat Bilanciere 4x8": "4 serie × 5 reps | Carico: ~75-80 kg | Tieni 2 rep di margine | Recupero: 2 min 30 sec",
    "Panca Piana Bilanciere": "4 serie × 8 reps | Polso dritto e in linea col bilanciere | Recupero: 90 sec",
    "Trazioni Sbarra 4xmax": "4 serie × max reps | Fermati 1-2 rep prima di cedere | Recupero: 90 sec",
    "Affondi Posteriori Manubri": "3 serie × 8 reps per gamba | Carico medio-alto | In controllo | Recupero: 90 sec",
    "Copenhagen Plank": "3 serie × 30 sec per lato | Gamba sopra appoggiata su panca | Recupero: 45 sec",
}
# --- 5. OBIETTIVI FISSI PER ESERCIZIO (kg) ---
obiettivi = {
    "Power Clean 5x5":               80.0,
    "Squat Bilanciere":             100.0,
    "Military Press 4x6":            50.0,
    "Rematore Bilanciere 4x8":       80.0,
    "Panca Piana Bilanciere":        80.0,
     "Affondi Posteriori Manubri":   20.0,
    "Trazioni Sbarra":               10.0,
}

# --- 6. TITOLO E LOGIN ---
st.title("🏋️‍♂️ Il mio registro di allenamento")

if 'ruolo' not in st.session_state:
    st.session_state.ruolo = None

if st.session_state.ruolo is None:
    st.write("### Accedi o continua come ospite")
    password = st.text_input("🔒 Password Admin (lascia vuoto per Guest)", type="password")
    col_login1, col_login2 = st.columns(2)
    if col_login1.button("Accedi come Admin"):
        if password == st.secrets["app_password"]:
            st.session_state.ruolo = "admin"
            st.rerun()
        else:
            st.error("Password errata!")
    if col_login2.button("Entra come Guest 👀"):
        st.session_state.ruolo = "guest"
        st.rerun()
    st.stop()

is_admin = st.session_state.ruolo == "admin"

if is_admin:
    st.success("👑 Modalità Admin")
else:
    st.info("👀 Modalità Guest — i dati non vengono salvati nel database")

if 'guest_serie' not in st.session_state:
    st.session_state.guest_serie = []

# --- 7. SELEZIONE GIORNO ---
giorno_sel = st.selectbox("Seleziona Sessione", list(scheda.keys()))
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

        if is_admin:
            if st.button("SALVA SCATTO E AVANZA ➡️"):
                with engine.connect() as conn:
                    conn.execute(sqlalchemy.text("""
                        INSERT INTO sessioni_corsa
                            (data_allenamento, tipo_corsa, serie_n, metri, ritmo, bpm, note)
                        VALUES (:d, :t, :s, :m, :r, :b, :n)
                    """), {"d": data_sel, "t": tipo_corsa, "s": serie, "m": metri, "r": ritmo, "b": bpm if bpm > 0 else None, "n": note})
                    conn.commit()
                st.session_state.n_serie += 1
                st.rerun()
            if st.button("Reset Scatto (Torna a 1)"):
                st.session_state.n_serie = 1
                st.rerun()
        else:
            st.warning("👀 Guest: il salvataggio è disabilitato")

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

        if is_admin:
            if st.button("SALVA CORSA LUNGA"):
                with engine.connect() as conn:
                    conn.execute(sqlalchemy.text("""
                        INSERT INTO sessioni_corsa
                            (data_allenamento, tipo_corsa, serie_n, metri, minuti, ritmo, bpm, note)
                        VALUES (:d, :t, 1, :m, :min, :r, :b, :n)
                    """), {"d": data_sel, "t": tipo_corsa, "m": metri, "min": minuti if minuti > 0 else None, "r": ritmo, "b": bpm if bpm > 0 else None, "n": note})
                    conn.commit()
                st.success("Corsa salvata!")
                st.rerun()
        else:
            st.warning("👀 Guest: il salvataggio è disabilitato")

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

        if is_admin:
            if st.button("SALVA RIPETUTA E AVANZA ➡️"):
                with engine.connect() as conn:
                    conn.execute(sqlalchemy.text("""
                        INSERT INTO sessioni_corsa
                            (data_allenamento, tipo_corsa, serie_n, metri, ritmo, bpm, note)
                        VALUES (:d, :t, :s, :m, :r, :b, :n)
                    """), {"d": data_sel, "t": tipo_corsa, "s": serie, "m": metri, "r": ritmo, "b": bpm if bpm > 0 else None, "n": note})
                    conn.commit()
                st.session_state.n_serie += 1
                st.rerun()
            if st.button("Reset Ripetuta (Torna a 1)"):
                st.session_state.n_serie = 1
                st.rerun()
        else:
            st.warning("👀 Guest: il salvataggio è disabilitato")

    # --- Storico Corsa ---
    st.divider()
    st.subheader("📋 Storico Corsa")
    try:
        with engine.connect() as conn:
            df_corse = pd.read_sql("""
                SELECT id, data_allenamento AS Data, tipo_corsa AS Tipo,
                       serie_n AS Serie, metri AS Metri, minuti AS Minuti,
                       ritmo AS Ritmo, bpm AS BPM, note AS Note
                FROM sessioni_corsa
                ORDER BY data_allenamento DESC, serie_n ASC
                LIMIT 30
            """, conn)

        if not df_corse.empty:
            if is_admin:
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
                                conn.execute(sqlalchemy.text("DELETE FROM sessioni_corsa WHERE id = :id"), {"id": id_del})
                            conn.commit()
                        st.rerun()
            else:
                st.dataframe(df_corse.drop(columns=["id"]), use_container_width=True)
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
                    WHERE esercizio = :ex
                    ORDER BY data_allenamento DESC, id DESC LIMIT 1
                """), {"ex": esercizio_sel}).fetchone()

            if result_last:
                with engine.connect() as conn:
                    ultime_serie = conn.execute(sqlalchemy.text("""
                        SELECT serie_n, ripetizioni, carico_kg
                        FROM sessioni_allenamento
                        WHERE esercizio = :ex
                        AND data_allenamento = (SELECT MAX(data_allenamento) FROM sessioni_allenamento WHERE esercizio = :ex)
                        ORDER BY serie_n ASC
                    """), {"ex": esercizio_sel}).fetchall()
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

        if is_admin:
            if st.button("SALVA SERIE E AVANZA ➡️"):
                with engine.connect() as conn:
                    conn.execute(sqlalchemy.text("""
                        INSERT INTO sessioni_allenamento
                            (data_allenamento, giorno_scheda, esercizio, serie_n, ripetizioni, carico_kg, note)
                        VALUES (:d, :g, :es, :s, :r, :kg, :n)
                    """), {"d": data_sel, "g": giorno_sel, "es": esercizio_sel, "s": serie, "r": reps, "kg": carico, "n": note})
                    conn.commit()
                st.session_state.n_serie += 1
                st.rerun()
            if st.button("Reset Serie (Torna a 1)"):
                st.session_state.n_serie = 1
                st.rerun()
        else:
            if st.button("AGGIUNGI SERIE (sessione temporanea) ➡️"):
                st.session_state.guest_serie.append({"Esercizio": esercizio_sel, "Serie": serie, "Reps": reps, "Kg": carico, "Note": note})
                st.session_state.n_serie += 1
                st.rerun()
            if st.session_state.guest_serie:
                st.dataframe(pd.DataFrame(st.session_state.guest_serie), use_container_width=True)
            st.warning("👀 Guest: i dati spariscono alla chiusura del browser")

# --- 10. SEZIONE PALESTRA ---
else:
    st.divider()
    esercizio_sel = st.selectbox("Esercizio", scheda[giorno_sel])

    # Box note esercizio
    if esercizio_sel in note_esercizi:
        st.info(f"📋 **{esercizio_sel}**\n\n{note_esercizi[esercizio_sel]}")

    try:
        with engine.connect() as conn:
            result_last = conn.execute(sqlalchemy.text("""
                SELECT carico_kg, ripetizioni, data_allenamento
                FROM sessioni_allenamento
                WHERE esercizio = :ex
                ORDER BY data_allenamento DESC, id DESC LIMIT 1
            """), {"ex": esercizio_sel}).fetchone()

        if result_last:
            with engine.connect() as conn:
                ultime_serie = conn.execute(sqlalchemy.text("""
                    SELECT serie_n, ripetizioni, carico_kg
                    FROM sessioni_allenamento
                    WHERE esercizio = :ex
                    AND data_allenamento = (SELECT MAX(data_allenamento) FROM sessioni_allenamento WHERE esercizio = :ex)
                    ORDER BY serie_n ASC
                """), {"ex": esercizio_sel}).fetchall()
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
    if esercizio_sel == "BattleRope":
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

    if is_admin:
        if st.button("SALVA SERIE E AVANZA ➡️"):
            with engine.connect() as conn:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO sessioni_allenamento
                        (data_allenamento, giorno_scheda, esercizio, serie_n, ripetizioni, carico_kg, note)
                    VALUES (:d, :g, :es, :s, :r, :kg, :n)
                """), {"d": data_sel, "g": giorno_sel, "es": esercizio_sel, "s": serie, "r": reps, "kg": carico, "n": note})
                conn.commit()
            st.session_state.n_serie += 1
            st.rerun()
        if st.button("Reset Serie (Torna a 1)"):
            st.session_state.n_serie = 1
            st.rerun()
    else:
        if st.button("AGGIUNGI SERIE (sessione temporanea) ➡️"):
            st.session_state.guest_serie.append({"Esercizio": esercizio_sel, "Serie": serie, "Reps": reps, "Kg": carico, "Note": note})
            st.session_state.n_serie += 1
            st.rerun()
        if st.session_state.guest_serie:
            st.dataframe(pd.DataFrame(st.session_state.guest_serie), use_container_width=True)
        st.warning("👀 Guest: i dati spariscono alla chiusura del browser")

    # --- Grafico progressi ---
    st.divider()
    st.subheader("📈 Analisi Carichi")
    try:
        with engine.connect() as conn:
            df_all = pd.read_sql("SELECT * FROM sessioni_allenamento", conn)
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
            if es_scelto in obiettivi and obiettivi[es_scelto] > 0:
                fig.add_hline(y=obiettivi[es_scelto], line_dash="dash", line_color="#FFD700",
                    annotation_text=f"Obiettivo: {obiettivi[es_scelto]:.0f} kg", annotation_position="top right")
            fig.update_layout(
                plot_bgcolor='#0E1117', paper_bgcolor='#0E1117', font_color='#FFFFFF',
                legend=dict(font=dict(color='#FFFFFF')),
                xaxis=dict(gridcolor='#333333'), yaxis=dict(gridcolor='#333333'),
            )
            st.plotly_chart(fig, use_container_width=True)

            if es_scelto in obiettivi and obiettivi[es_scelto] > 0:
                try:
                    df_filt['data_allenamento'] = pd.to_datetime(df_filt['data_allenamento'])
                    df_filt['settimana'] = df_filt['data_allenamento'].dt.to_period('W')
                    df_sett = df_filt.groupby('settimana')['carico_kg'].max().reset_index().sort_values('settimana').tail(4)
                    if len(df_sett) >= 2:
                        progressione    = df_sett['carico_kg'].diff().dropna().mean()
                        massimo_attuale = df_sett['carico_kg'].iloc[-1]
                        obiettivo_kg    = obiettivi[es_scelto]
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

# --- 11. GESTIONE CRONOLOGIA (solo Admin) ---
if is_admin:
    st.divider()
    st.subheader("🗑️ Gestione Cronologia Selettiva")
    try:
        with engine.connect() as conn:
            df_last = pd.read_sql("""
                SELECT id, data_allenamento, esercizio, serie_n, ripetizioni, carico_kg, note
                FROM sessioni_allenamento ORDER BY id DESC LIMIT 20
            """, conn)
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
                            conn.execute(sqlalchemy.text("DELETE FROM sessioni_allenamento WHERE id = :id"), {"id": id_del})
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

if is_admin:
    col_p1, col_p2 = st.columns(2)
    data_peso = col_p1.date_input("Data misurazione", date.today(), key="data_peso")
    peso_kg = col_p2.number_input("Peso (kg)", min_value=40.0, max_value=200.0, step=0.1, key="peso_kg")
    if st.button("SALVA PESO"):
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("INSERT INTO peso_corporeo (data_misurazione, peso_kg) VALUES (:d, :p)"), {"d": data_peso, "p": peso_kg})
            conn.commit()
        st.success("Peso salvato!")
        st.rerun()

try:
    with engine.connect() as conn:
        df_peso = pd.read_sql("SELECT data_misurazione, peso_kg FROM peso_corporeo ORDER BY data_misurazione ASC", conn)
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
