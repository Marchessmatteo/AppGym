import streamlit as st
import pandas as pd
import sqlalchemy
import plotly.graph_objects as go
import os
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
engine = sqlalchemy.create_engine(
    f"mysql+pymysql://{st.secrets['user']}:{st.secrets['pw']}@{st.secrets['host']}:{st.secrets['port']}/{st.secrets['db']}",
    connect_args={"ssl": {"ca": False}}
)
)
# --- 3. SCHEDA ALLENAMENTO ---
scheda = {
    "Giorno 1": [
        "BattleRope",
        "Power Clean 5x5",
        "Affondi Manubri 3x20",
        "Trazioni Sbarra 4xmax",
        "Scaletta Agilità 5min"
    ],
    "Giorno 2": [
        "Push-up Esplosivi 4x8",
        "Military Press 4x6",
        "Dip Parallele 4x10",
        "Rematore Bilanciere 4x8",
        "BattleRope"
    ],
    "Giorno 3": [
        "Squat Bilanciere 4x8",
        "Burpees 3x12",
        "Trazioni Presa Inversa 3xmax",
        "Affondi saltati 3x20",
        "Scaletta + Scatto",
        "PLUNK1 + legraises15 + russian twist20"
    ],
    "Giorno 4": ["Corsa"],
    "Giorno Jolly": ["Esercizio Libero"]
}

# --- 4. OBIETTIVI FISSI PER ESERCIZIO (kg) ---
obiettivi = {
    "Power Clean 5x5":              100.0,
    "Squat Bilanciere 4x8":         100.0,
    "Military Press 4x6":            80.0,
    "Rematore Bilanciere 4x8":       80.0,
    "Dip Parallele 4x10":            20.0,
    "Trazioni Sbarra 4xmax":         10.0,
    "Trazioni Presa Inversa 3xmax":  10.0,
    "Push-up Esplosivi 4x8":          0.0,
    "Affondi Manubri 3x20":          20.0,
    "Affondi saltati 3x20":          20.0,
    "Burpees 3x12":                  20.0,
}

# --- 5. TITOLO E LOGIN ---
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

# --- 6. SELEZIONE GIORNO ---
giorno_sel = st.selectbox("Seleziona Giorno", list(scheda.keys()))
data_sel = st.date_input("Data", date.today())

# --- 7. SEZIONE CORSA (Giorno 4) ---
if giorno_sel == "Giorno 4":
    st.divider()
    st.subheader("🏃‍♂️ Obiettivo Settimanale: 10 KM")

    try:
        df_corsa_db = pd.read_sql(
            "SELECT carico_kg FROM sessioni_allenamento WHERE esercizio = 'Corsa'", engine
        )
        km_totali = df_corsa_db['carico_kg'].sum()
    except:
        km_totali = 0.0

    obiettivo_km = 10.0
    percentuale = min(km_totali / obiettivo_km, 1.0)

    st.progress(percentuale)
    st.write(f"Hai percorso **{km_totali:.1f} km** su {obiettivo_km} km previsti!")

    st.divider()
    st.write("⌚ **Sincronizzazione Smartwatch**")

    distanza = 0.0
    minuti = 0
    note_corsa = "Sessione Corsa"

    if st.button("Sincronizza dati da Smartwatch"):
        with st.spinner("Connessione al server dell'orologio..."):
            time.sleep(2)
            distanza = 4.5
            minuti = 25
            note_corsa = "Sincronizzato da Smartwatch"
            st.success(f"✅ Trovata ultima corsa: {distanza} km!")
    else:
        c1, c2 = st.columns(2)
        distanza = c1.number_input("Distanza (km)", min_value=0.0, step=0.1, key="dist_man")
        minuti = c2.number_input("Tempo (min)", min_value=0, step=1, key="time_man")
        note_corsa = st.text_input("Note corsa", key="note_man")

    if distanza > 0 and minuti > 0:
        ritmo_decimale = minuti / distanza
        minuti_ritmo = int(ritmo_decimale)
        secondi_ritmo = int((ritmo_decimale - minuti_ritmo) * 60)
        ritmo_str = f"{minuti_ritmo}:{secondi_ritmo:02d} min/km"
        st.metric("🏃 Ritmo medio", ritmo_str)
        note_corsa_finale = f"{note_corsa} | Ritmo: {ritmo_str}".strip(" |")
    else:
        note_corsa_finale = note_corsa

    if is_admin:
        if st.button("SALVA SESSIONE CORSA"):
            with engine.connect() as conn:
                query = sqlalchemy.text("""
                    INSERT INTO sessioni_allenamento
                        (data_allenamento, giorno_scheda, esercizio, serie_n, ripetizioni, carico_kg, note)
                    VALUES
                        (:d, :g, 'Corsa', 1, :r, :c, :n)
                """)
                conn.execute(query, {"d": data_sel, "g": giorno_sel, "r": minuti, "c": distanza, "n": note_corsa_finale})
                conn.commit()
            st.rerun()
    else:
        st.warning("👀 Guest: il salvataggio è disabilitato")

    st.divider()
    st.subheader("📋 Storico Corse")
    try:
        df_corse = pd.read_sql("""
            SELECT
                id,
                data_allenamento AS Data,
                carico_kg        AS Km,
                ripetizioni      AS Minuti,
                note             AS Note
            FROM sessioni_allenamento
            WHERE esercizio = 'Corsa'
            ORDER BY data_allenamento DESC
        """, engine)

        if not df_corse.empty:
            df_corse['Ritmo'] = df_corse.apply(
                lambda r: f"{int(r['Minuti']/r['Km'])}:{int(((r['Minuti']/r['Km']) % 1) * 60):02d} min/km"
                if r['Km'] > 0 else "-", axis=1
            )

            if is_admin:
                df_corse.insert(0, "Seleziona", False)
                modificato_corse = st.data_editor(
                    df_corse,
                    hide_index=True,
                    column_config={
                        "id":        None,
                        "Seleziona": st.column_config.CheckboxColumn(help="Spunta per eliminare"),
                        "Data":      "Data",
                        "Km":        "Km",
                        "Minuti":    "Minuti",
                        "Ritmo":     "Ritmo",
                        "Note":      "Note"
                    },
                    disabled=["Data", "Km", "Minuti", "Ritmo", "Note"],
                    use_container_width=True,
                    key="editor_corse"
                )
                ids_da_eliminare = modificato_corse[modificato_corse["Seleziona"] == True]["id"].tolist()
                if ids_da_eliminare:
                    if st.button(
                        f"🗑️ ELIMINA {len(ids_da_eliminare)} RIGHE SELEZIONATE",
                        type="primary",
                        use_container_width=True,
                        key="elimina_corse"
                    ):
                        with engine.connect() as conn:
                            for id_del in ids_da_eliminare:
                                conn.execute(sqlalchemy.text(
                                    "DELETE FROM sessioni_allenamento WHERE id = :id"
                                ), {"id": id_del})
                            conn.commit()
                        st.success("Righe eliminate con successo!")
                        st.rerun()
            else:
                st.dataframe(df_corse.drop(columns=["id"]), use_container_width=True)
        else:
            st.info("Nessuna corsa registrata ancora.")
    except Exception as e:
        st.error(f"Errore: {e}")

# --- 8. SEZIONE GIORNO JOLLY ---
elif giorno_sel == "Giorno Jolly":
    st.divider()
    esercizio_sel = st.text_input("✏️ Nome Esercizio", placeholder="Es. Panca Piana, Leg Press...")

    if esercizio_sel:
        try:
            query_last = sqlalchemy.text("""
                SELECT carico_kg, ripetizioni, data_allenamento
                FROM sessioni_allenamento
                WHERE esercizio = :ex
                ORDER BY data_allenamento DESC, id DESC
                LIMIT 1
            """)
            with engine.connect() as conn:
                result_last = conn.execute(query_last, {"ex": esercizio_sel}).fetchone()

            if result_last:
                query_ultime = sqlalchemy.text("""
                    SELECT serie_n, ripetizioni, carico_kg
                    FROM sessioni_allenamento
                    WHERE esercizio = :ex
                    AND data_allenamento = (
                        SELECT MAX(data_allenamento)
                        FROM sessioni_allenamento
                        WHERE esercizio = :ex
                    )
                    ORDER BY serie_n ASC
                """)
                with engine.connect() as conn:
                    ultime_serie = conn.execute(query_ultime, {"ex": esercizio_sel}).fetchall()

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
                    query = sqlalchemy.text("""
                        INSERT INTO sessioni_allenamento
                            (data_allenamento, giorno_scheda, esercizio, serie_n, ripetizioni, carico_kg, note)
                        VALUES
                            (:d, :g, :es, :s, :r, :kg, :n)
                    """)
                    conn.execute(query, {
                        "d": data_sel, "g": giorno_sel, "es": esercizio_sel,
                        "s": serie, "r": reps, "kg": carico, "n": note
                    })
                    conn.commit()
                st.session_state.n_serie += 1
                st.rerun()
            if st.button("Reset Serie (Torna a 1)"):
                st.session_state.n_serie = 1
                st.rerun()
        else:
            if st.button("AGGIUNGI SERIE (sessione temporanea) ➡️"):
                st.session_state.guest_serie.append({
                    "Esercizio": esercizio_sel,
                    "Serie": serie,
                    "Reps": reps,
                    "Kg": carico,
                    "Note": note
                })
                st.session_state.n_serie += 1
                st.rerun()
            if st.session_state.guest_serie:
                st.write("📋 Serie di questa sessione:")
                st.dataframe(pd.DataFrame(st.session_state.guest_serie), use_container_width=True)
            st.warning("👀 Guest: i dati spariscono alla chiusura del browser")

# --- 9. SEZIONE PALESTRA (Giorno 1, 2, 3) ---
else:
    st.divider()
    esercizio_sel = st.selectbox("Esercizio", scheda[giorno_sel])

    try:
        query_last = sqlalchemy.text("""
            SELECT carico_kg, ripetizioni, data_allenamento
            FROM sessioni_allenamento
            WHERE esercizio = :ex
            ORDER BY data_allenamento DESC, id DESC
            LIMIT 1
        """)
        with engine.connect() as conn:
            result_last = conn.execute(query_last, {"ex": esercizio_sel}).fetchone()

        if result_last:
            query_ultime = sqlalchemy.text("""
                SELECT serie_n, ripetizioni, carico_kg
                FROM sessioni_allenamento
                WHERE esercizio = :ex
                AND data_allenamento = (
                    SELECT MAX(data_allenamento)
                    FROM sessioni_allenamento
                    WHERE esercizio = :ex
                )
                ORDER BY serie_n ASC
            """)
            with engine.connect() as conn:
                ultime_serie = conn.execute(query_ultime, {"ex": esercizio_sel}).fetchall()

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
                query = sqlalchemy.text("""
                    INSERT INTO sessioni_allenamento
                        (data_allenamento, giorno_scheda, esercizio, serie_n, ripetizioni, carico_kg, note)
                    VALUES
                        (:d, :g, :es, :s, :r, :kg, :n)
                """)
                conn.execute(query, {
                    "d": data_sel, "g": giorno_sel, "es": esercizio_sel,
                    "s": serie, "r": reps, "kg": carico, "n": note
                })
                conn.commit()
            st.session_state.n_serie += 1
            st.rerun()

        if st.button("Reset Serie (Torna a 1)"):
            st.session_state.n_serie = 1
            st.rerun()
    else:
        if st.button("AGGIUNGI SERIE (sessione temporanea) ➡️"):
            st.session_state.guest_serie.append({
                "Esercizio": esercizio_sel,
                "Serie": serie,
                "Reps": reps,
                "Kg": carico,
                "Note": note
            })
            st.session_state.n_serie += 1
            st.rerun()

        if st.session_state.guest_serie:
            st.write("📋 Serie di questa sessione:")
            st.dataframe(pd.DataFrame(st.session_state.guest_serie), use_container_width=True)

        st.warning("👀 Guest: i dati spariscono alla chiusura del browser")

    # --- Grafico progressi con Plotly ---
    st.divider()
    st.subheader("📈 Analisi Carichi")
    try:
        df_all = pd.read_sql("SELECT * FROM sessioni_allenamento", engine)
        if not df_all.empty:
            es_scelto = st.selectbox("Scegli esercizio da analizzare:", df_all['esercizio'].unique())
            df_filt = df_all[df_all['esercizio'] == es_scelto].sort_values('data_allenamento')

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df_filt['data_allenamento'],
                y=df_filt['carico_kg'],
                mode='markers',
                name='Serie',
                marker=dict(color='#FF4B2B', size=8),
                text=df_filt['serie_n'].apply(lambda x: f"Serie {x}"),
                hovertemplate='<b>%{text}</b><br>Kg: %{y}<br>Data: %{x}<extra></extra>'
            ))

            df_max = df_filt.groupby('data_allenamento', as_index=False)['carico_kg'].max()
            fig.add_trace(go.Scatter(
                x=df_max['data_allenamento'],
                y=df_max['carico_kg'],
                mode='lines+markers',
                name='Massimo sessione',
                line=dict(color='#00C853', width=2),
                marker=dict(color='#00C853', size=10)
            ))

            if es_scelto in obiettivi and obiettivi[es_scelto] > 0:
                fig.add_hline(
                    y=obiettivi[es_scelto],
                    line_dash="dash",
                    line_color="#FFD700",
                    annotation_text=f"Obiettivo: {obiettivi[es_scelto]:.0f} kg",
                    annotation_position="top right"
                )

            fig.update_layout(
                plot_bgcolor='#0E1117',
                paper_bgcolor='#0E1117',
                font_color='#FFFFFF',
                legend=dict(font=dict(color='#FFFFFF')),
                xaxis=dict(gridcolor='#333333'),
                yaxis=dict(gridcolor='#333333'),
            )

            st.plotly_chart(fig, use_container_width=True)

            if es_scelto in obiettivi and obiettivi[es_scelto] > 0:
                try:
                    df_filt['data_allenamento'] = pd.to_datetime(df_filt['data_allenamento'])
                    df_filt['settimana'] = df_filt['data_allenamento'].dt.to_period('W')
                    df_sett = df_filt.groupby('settimana')['carico_kg'].max().reset_index()
                    df_sett = df_sett.sort_values('settimana').tail(4)

                    if len(df_sett) >= 2:
                        progressione    = df_sett['carico_kg'].diff().dropna().mean()
                        massimo_attuale = df_sett['carico_kg'].iloc[-1]
                        obiettivo_kg    = obiettivi[es_scelto]
                        kg_mancanti     = obiettivo_kg - massimo_attuale

                        st.divider()
                        col_a, col_b, col_c = st.columns(3)
                        col_a.metric("🏋️ Massimo attuale",   f"{massimo_attuale:.1f} kg")
                        col_b.metric("📈 Progressione/sett", f"+{progressione:.1f} kg")
                        col_c.metric("🎯 Obiettivo",          f"{obiettivo_kg:.0f} kg")

                        if kg_mancanti <= 0:
                            st.success("🏆 Obiettivo già raggiunto! Pensa a impostarne uno nuovo.")
                        elif progressione <= 0:
                            st.warning("⚠️ Nelle ultime 4 settimane il carico non è aumentato. Continua a spingere!")
                        else:
                            settimane_mancanti = kg_mancanti / progressione
                            data_arrivo = date.today() + pd.Timedelta(weeks=settimane_mancanti)
                            st.success(f"🗓️ Se continui così raggiungi **{obiettivo_kg:.0f} kg** il **{data_arrivo.strftime('%d %B %Y')}** — tra circa **{settimane_mancanti:.0f} settimane**!")
                    else:
                        st.info("📊 Servono almeno 2 settimane di dati per stimare la progressione.")
                except Exception as e:
                    st.error(f"Errore stima: {e}")

    except:
        st.info("Aggiungi dati per vedere i grafici.")

# --- 10. GESTIONE CRONOLOGIA (solo Admin) ---
if is_admin:
    st.divider()
    st.subheader("🗑️ Gestione Cronologia Selettiva")

    try:
        query_cronologia = """
            SELECT id, data_allenamento, esercizio, serie_n, ripetizioni, carico_kg, note
            FROM sessioni_allenamento
            ORDER BY id DESC
            LIMIT 20
        """
        df_last = pd.read_sql(query_cronologia, engine)

        if not df_last.empty:
            df_last.insert(0, "Seleziona", False)

            modificato = st.data_editor(
                df_last,
                hide_index=True,
                column_config={
                    "id": None,
                    "Seleziona": st.column_config.CheckboxColumn(help="Spunta per eliminare"),
                    "data_allenamento": "Data",
                    "esercizio": "Esercizio",
                    "ripetizioni": "Ripetizioni",
                    "carico_kg": "Kg"
                },
                disabled=["data_allenamento", "esercizio", "serie_n", "ripetizioni", "carico_kg", "note"],
                use_container_width=True,
                key="editor_cronologia"
            )

            ids_da_eliminare = modificato[modificato["Seleziona"] == True]["id"].tolist()

            if ids_da_eliminare:
                if st.button(
                    f"🗑️ ELIMINA {len(ids_da_eliminare)} RIGHE SELEZIONATE",
                    type="primary",
                    use_container_width=True,
                    key="elimina_cronologia"
                ):
                    with engine.connect() as conn:
                        for id_del in ids_da_eliminare:
                            conn.execute(sqlalchemy.text(
                                "DELETE FROM sessioni_allenamento WHERE id = :id"
                            ), {"id": id_del})
                        conn.commit()
                    st.success("Righe eliminate con successo!")
                    st.rerun()
        else:
            st.info("Nessun dato registrato.")

    except Exception as e:
        st.error(f"Errore: {e}")

# --- 11. TRACCIAMENTO PESO CORPOREO ---
st.divider()
st.subheader("⚖️ Peso Corporeo")

peso_obiettivo = 78.0

if is_admin:
    col_p1, col_p2 = st.columns(2)
    data_peso = col_p1.date_input("Data misurazione", date.today(), key="data_peso")
    peso_kg = col_p2.number_input("Peso (kg)", min_value=40.0, max_value=200.0, step=0.1, key="peso_kg")

    if st.button("SALVA PESO"):
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("""
                INSERT INTO peso_corporeo (data_misurazione, peso_kg)
                VALUES (:d, :p)
            """), {"d": data_peso, "p": peso_kg})
            conn.commit()
        st.success("Peso salvato!")
        st.rerun()

try:
    df_peso = pd.read_sql("""
        SELECT data_misurazione, peso_kg
        FROM peso_corporeo
        ORDER BY data_misurazione ASC
    """, engine)

    if not df_peso.empty:
        fig_peso = go.Figure()
        fig_peso.add_trace(go.Scatter(
            x=df_peso['data_misurazione'],
            y=df_peso['peso_kg'],
            mode='lines+markers',
            name='Peso',
            line=dict(color='#FF4B2B', width=2),
            marker=dict(size=8)
        ))
        fig_peso.add_hline(
            y=peso_obiettivo,
            line_dash="dash",
            line_color="#FFD700",
            annotation_text=f"Obiettivo: {peso_obiettivo} kg",
            annotation_position="top right"
        )
        fig_peso.update_layout(
            plot_bgcolor='#0E1117',
            paper_bgcolor='#0E1117',
            font_color='#FFFFFF',
            xaxis=dict(gridcolor='#333333'),
            yaxis=dict(gridcolor='#333333'),
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
