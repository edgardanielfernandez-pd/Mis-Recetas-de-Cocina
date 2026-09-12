import streamlit as st
import sqlite3
import pandas as pd
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Mi Recetario", page_icon="🍳", layout="wide")

CARPETA_VIDEOS = "VIDEOS"
os.makedirs(CARPETA_VIDEOS, exist_ok=True)

# --- BASE DE DATOS ---
conn = sqlite3.connect("recetario.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS recetas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    tipo_sabor TEXT NOT NULL,
    es_airfryer INTEGER DEFAULT 0,
    ingredientes TEXT NOT NULL,
    pasos TEXT,
    tipo_video TEXT,
    origen_video TEXT,
    probada INTEGER DEFAULT 0
)
""")
conn.commit()

st.title("🍳 Mi Recetario Inteligente")

tab_ver, tab_agregar, tab_despensa = st.tabs([
    "📖 Ver y Editar Recetas", 
    "➕ Cargar Nueva Receta", 
    "🔍 ¿Qué cocino con lo que tengo?"
])

# ========================================================
# TAB 1: VER, EDITAR, ELIMINAR Y MARCAR PROBADAS (ORDEN ALFABÉTICO)
# ========================================================
with tab_ver:
    col_f1, col_f2, col_f3 = st.columns([1.5, 1.5, 1.5])
    with col_f1:
        filtro_estado = st.selectbox("Estado:", ["Todas", "Para Repetir (Probadas)", "Por Probar (Pendientes)"])
    with col_f2:
        filtro_sabor = st.multiselect("Sabor:", ["Dulce", "Salada"], default=["Dulce", "Salada"])
    with col_f3:
        filtro_metodo = st.selectbox("Método de cocción:", ["Todos", "Solo Freidora de aire", "Solo Tradicional (Sin freidora)"])

    # Consulta base con filtros
    query = "SELECT * FROM recetas WHERE 1=1"
    params = []

    if filtro_estado == "Para Repetir (Probadas)":
        query += " AND probada = 1"
    elif filtro_estado == "Por Probar (Pendientes)":
        query += " AND probada = 0"

    if filtro_sabor:
        placeholders = ",".join("?" for _ in filtro_sabor)
        query += f" AND tipo_sabor IN ({placeholders})"
        params.extend(filtro_sabor)

    if filtro_metodo == "Solo Freidora de aire":
        query += " AND es_airfryer = 1"
    elif filtro_metodo == "Solo Tradicional (Sin freidora)":
        query += " AND es_airfryer = 0"

    # ORDENAMIENTO ALFABÉTICO (A - Z)
    query += " ORDER BY nombre COLLATE NOCASE ASC"

    df = pd.read_sql(query, conn, params=params)

    if df.empty:
        st.info("No hay recetas registradas con estos filtros.")
    else:
        for _, row in df.iterrows():
            tag_sabor = "🍰 Dulce" if row['tipo_sabor'] == "Dulce" else "🧂 Salada"
            tag_airfryer = "🌪️ Freidora de aire" if row['es_airfryer'] == 1 else "🍳 Tradicional"
            tag_estado = "⭐ Para Repetir" if row['probada'] == 1 else "⏳ Por Probar"
            
            with st.expander(f"{row['nombre']} — [{tag_sabor} | {tag_airfryer}] — {tag_estado}"):
                sub_ver, sub_editar = st.tabs(["👁️ Ver Receta", "✏️ Modificar / Eliminar"])
                
                # --- VISTA NORMAL ---
                with sub_ver:
                    col_info, col_media = st.columns([1, 1])
                    with col_info:
                        st.markdown("#### 🛒 Ingredientes")
                        for ing in [i.strip() for i in row['ingredientes'].split(",") if i.strip()]:
                            st.markdown(f"- {ing}")
                        st.markdown("#### 📝 Preparación")
                        st.write(row['pasos'] if row['pasos'] else "Sin pasos detallados.")
                        
                        marcado = st.checkbox("¿Receta probada / Para repetir?", value=bool(row['probada']), key=f"probada_{row['id']}")
                        if marcado != bool(row['probada']):
                            c.execute("UPDATE recetas SET probada = ? WHERE id = ?", (1 if marcado else 0, row['id']))
                            conn.commit()
                            st.rerun()

                    with col_media:
                        st.markdown("#### 🎥 Video")
                        if row['origen_video']:
                            if row['tipo_video'] == 'local' and os.path.exists(row['origen_video']):
                                st.video(row['origen_video'])
                            elif row['tipo_video'] == 'enlace':
                                st.video(row['origen_video'])
                            else:
                                st.warning("Video local no encontrado.")
                        else:
                            st.info("Sin video asignado.")

                # --- MODO EDICIÓN ---
                with sub_editar:
                    with st.form(f"form_editar_{row['id']}"):
                        edit_nombre = st.text_input("Nombre", value=row['nombre'])
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            edit_sabor = st.radio("Sabor", ["Salada", "Dulce"], index=0 if row['tipo_sabor'] == "Salada" else 1, horizontal=True)
                        with col_e2:
                            edit_airfryer = st.checkbox("¿Freidora de aire?", value=bool(row['es_airfryer']))
                        
                        edit_ingredientes = st.text_area("Ingredientes (separados por coma)", value=row['ingredientes'])
                        edit_pasos = st.text_area("Instrucciones", value=row['pasos'] if row['pasos'] else "")
                        
                        edit_video_url = st.text_input("Enlace web de video (dejar vacío si no aplica)", value=row['origen_video'] if row['tipo_video'] == 'enlace' else "")
                        
                        col_btn1, col_btn2 = st.columns([1, 1])
                        with col_btn1:
                            guardar_cambios = st.form_submit_button("💾 Guardar Cambios")
                        with col_btn2:
                            borrar_receta = st.form_submit_button("🗑️ Eliminar Receta")

                        if guardar_cambios:
                            nuevo_tipo_video = row['tipo_video']
                            nuevo_origen_video = row['origen_video']
                            if edit_video_url.strip():
                                nuevo_tipo_video = "enlace"
                                nuevo_origen_video = edit_video_url.strip()

                            c.execute("""
                                UPDATE recetas 
                                SET nombre = ?, tipo_sabor = ?, es_airfryer = ?, ingredientes = ?, pasos = ?, tipo_video = ?, origen_video = ?
                                WHERE id = ?
                            """, (edit_nombre.strip(), edit_sabor, 1 if edit_airfryer else 0, edit_ingredientes.strip().lower(), edit_pasos.strip(), nuevo_tipo_video, nuevo_origen_video, row['id']))
                            conn.commit()
                            st.success("¡Receta actualizada!")
                            st.rerun()

                        if borrar_receta:
                            c.execute("DELETE FROM recetas WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.warning(f"Receta '{row['nombre']}' eliminada.")
                            st.rerun()

# ========================================================
# TAB 2: AGREGAR NUEVA RECETA
# ========================================================
with tab_agregar:
    st.subheader("Cargar una nueva receta")
    
    nombre = st.text_input("Nombre de la receta *", key="new_nombre")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        tipo_sabor = st.radio("Sabor *", ["Salada", "Dulce"], horizontal=True, key="new_sabor")
    with col_c2:
        es_airfryer = st.checkbox("¿Es para Freidora de aire (Airfryer)?", value=False, key="new_airfryer")
        
    ingredientes = st.text_area("Ingredientes (separados por coma, ej: 2 papas, 1 cdita sal, 1 cda aceite) *", key="new_ing")
    pasos = st.text_area("Instrucciones / Paso a paso", key="new_pasos")
    
    st.markdown("#### Opciones de Video")
    tipo_video_opcion = st.radio(
        "¿Cómo vas a ingresar el video?",
        ["Pegar enlace web (YouTube, TikTok, Instagram)", "Subir archivo (.mp4, .mov)", "Sin video"],
        horizontal=True,
        key="new_tipo_video"
    )
    
    video_subido = None
    video_url = ""
    
    if tipo_video_opcion == "Pegar enlace web (YouTube, TikTok, Instagram)":
        video_url = st.text_input("Pega aquí la URL del video (ej: https://www.youtube.com/watch?v=...)", key="new_url")
    elif tipo_video_opcion == "Subir archivo (.mp4, .mov)":
        video_subido = st.file_uploader("Selecciona el archivo de video", type=["mp4", "mov", "avi", "mkv"], key="new_file")
        
    probada_inicial = st.checkbox("¿Ya la probaste y es para repetir?", key="new_probada")
    
    if st.button("💾 Guardar Receta", type="primary"):
        if not nombre.strip() or not ingredientes.strip():
            st.error("Por favor completa al menos el nombre y los ingredientes.")
        else:
            tipo_final = "ninguno"
            origen_final = ""
            
            if tipo_video_opcion.startswith("Subir") and video_subido is not None:
                nombre_archivo_seguro = f"{nombre.strip().replace(' ', '_').lower()}_{video_subido.name}"
                ruta_guardado = os.path.join(CARPETA_VIDEOS, nombre_archivo_seguro)
                with open(ruta_guardado, "wb") as f:
                    f.write(video_subido.getbuffer())
                tipo_final = "local"
                origen_final = ruta_guardado
            elif tipo_video_opcion.startswith("Pegar") and video_url.strip():
                tipo_final = "enlace"
                origen_final = video_url.strip()
            
            c.execute("""
                INSERT INTO recetas (nombre, tipo_sabor, es_airfryer, ingredientes, pasos, tipo_video, origen_video, probada)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nombre.strip(), tipo_sabor, 1 if es_airfryer else 0, ingredientes.strip().lower(), pasos.strip(), tipo_final, origen_final, 1 if probada_inicial else 0))
            conn.commit()
            
            st.success(f"¡Receta '{nombre}' guardada con éxito!")
            st.rerun()

# ========================================================
# TAB 3: BUSCADOR POR DESPENSA (ORDEN ALFABÉTICO)
# ========================================================
with tab_despensa:
    st.subheader("¿Qué tienes en casa?")
    ingredientes_disponibles = st.text_input("Ingresa ingredientes que tienes (ej: huevo, queso, harina)")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        solo_probadas = st.checkbox("Mostrar únicamente recetas probadas", value=False)
    with col_d2:
        solo_airfryer_despensa = st.checkbox("Filtrar solo recetas de Freidora de aire", value=False)
    
    if ingredientes_disponibles:
        set_casa = {item.strip().lower() for item in ingredientes_disponibles.split(",") if item.strip()}
        
        query_todas = "SELECT * FROM recetas WHERE 1=1"
        if solo_probadas:
            query_todas += " AND probada = 1"
        if solo_airfryer_despensa:
            query_todas += " AND es_airfryer = 1"
        query_todas += " ORDER BY nombre COLLATE NOCASE ASC"
            
        todas_df = pd.read_sql(query_todas, conn)
        
        completas = []
        parciales = []
        
        for _, fila in todas_df.iterrows():
            items_receta = [i.strip().lower() for i in fila['ingredientes'].split(",") if i.strip()]
            ingredientes_presentes = 0
            faltantes = []
            
            for ing_receta in items_receta:
                if any(ing_casa in ing_receta for ing_casa in set_casa):
                    ingredientes_presentes += 1
                else:
                    faltantes.append(ing_receta)
            
            total_ing = len(items_receta)
            if total_ing > 0:
                porcentaje = (ingredientes_presentes / total_ing) * 100
                if porcentaje == 100:
                    completas.append((fila, faltantes))
                elif ingredientes_presentes > 0:
                    parciales.append((fila, faltantes, porcentaje))
        
        if completas:
            st.success(f"🎉 **¡Recetas listas para cocinar ({len(completas)})!**")
            for r, _ in completas:
                tipo_txt = f"{r['tipo_sabor']} | {'Freidora de aire' if r['es_airfryer'] == 1 else 'Tradicional'}"
                with st.expander(f"🟢 {r['nombre']} ({tipo_txt})"):
                    st.write(f"**Ingredientes:** {r['ingredientes']}")
                    st.write(f"**Pasos:** {r['pasos']}")
                    if r['origen_video']:
                        st.video(r['origen_video'])
                        
        if parciales:
            st.markdown("### 🟡 Recetas a las que les falta poco:")
            parciales.sort(key=lambda x: x[2], reverse=True)
            for r, faltantes, pct in parciales:
                tipo_txt = f"{r['tipo_sabor']} | {'Freidora de aire' if r['es_airfryer'] == 1 else 'Tradicional'}"
                with st.expander(f"🟡 {r['nombre']} ({tipo_txt}) — Coincidencia: {pct:.0f}%"):
                    st.write(f"**Te falta:** {', '.join(faltantes)}")
                    st.write(f"**Ingredientes:** {r['ingredientes']}")
                    if r['origen_video']:
                        st.video(r['origen_video'])
