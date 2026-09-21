import streamlit as st
import pandas as pd
import os
from supabase import create_client, Client

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Mi Recetario", page_icon="🍳", layout="wide")

CARPETA_VIDEOS = "VIDEOS"
os.makedirs(CARPETA_VIDEOS, exist_ok=True)

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- SEGURIDAD: MODO ADMINISTRADOR ---
admin_pwd = st.secrets.get("ADMIN_PASSWORD", "admin123")
st.sidebar.title("🔐 Acceso")
password_ingresada = st.sidebar.text_input("Clave de Administrador", type="password")
es_admin = (password_ingresada == admin_pwd)

if es_admin:
    st.sidebar.success("Modo Administrador Activo ✅")
else:
    st.sidebar.info("Modo de Solo Lectura 👁️")

def obtener_todas_recetas():
    res = supabase.table("recetas").select("*").order("nombre").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

# --- ESTILOS VISUALES ---
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        padding: 6px 0px 16px 0px;
        border-bottom: 2px solid rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #F4EBE1 !important;
        border: 1px solid #E0D3C5 !important;
        border-radius: 12px !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        color: #4A3E3D !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        transition: all 0.2s ease-in-out;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #EBDCCE !important;
        transform: translateY(-1px);
    }
    .stTabs [aria-selected="true"] {
        background-color: #E05A47 !important;
        color: #FFFFFF !important;
        border: 1px solid #E05A47 !important;
        box-shadow: 0 4px 10px rgba(224, 90, 71, 0.3) !important;
    }
    .streamlit-expanderHeader {
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    .indice-letra {
        background-color: #E05A47;
        color: white;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 1.2rem;
        font-weight: bold;
        display: inline-block;
        margin-top: 15px;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

OPCIONES_METODO = ["Al Horno", "A la Olla / Cacerola", "Freidora de aire", "Sartén / Hornalla", "Sin cocción"]

# --- ENCABEZADO ---
st.title("🍳 Mi Recetario Inteligente")
st.title("Creado por E.D.F.")

# Pestañas condicionales según el rol
if es_admin:
    tab_ver, tab_indice, tab_agregar, tab_despensa = st.tabs([
        "📖 Ver y Editar Recetas",
        "🔤 Índice A-Z",
        "➕ Cargar Nueva Receta", 
        "🔍 ¿Qué cocino con lo que tengo?"
    ])
else:
    tab_ver, tab_indice, tab_despensa = st.tabs([
        "📖 Ver Recetas",
        "🔤 Índice A-Z",
        "🔍 ¿Qué cocino con lo que tengo?"
    ])

# ========================================================
# TAB 1: VER, BUSCAR, EDITAR Y ELIMINAR RECETAS
# ========================================================
with tab_ver:
    busqueda_texto = st.text_input(
        "🔎 Buscar receta en tiempo real (por nombre o por ingrediente):",
        placeholder="Escribe para buscar... ej: fugazzeta, harina, manteca"
    )

    col_f1, col_f2, col_f3 = st.columns([1.5, 1.5, 1.5])
    with col_f1:
        filtro_estado = st.selectbox("Estado:", ["Todas", "Para Repetir (Probadas)", "Por Probar (Pendientes)"])
    with col_f2:
        filtro_sabor = st.selectbox("Sabor:", ["Todos", "Salada", "Dulce"])
    with col_f3:
        filtro_metodo = st.selectbox("Método de cocción:", ["Todos"] + OPCIONES_METODO)

    df_base = obtener_todas_recetas()

    if not df_base.empty:
        df = df_base.copy()
        if filtro_estado == "Para Repetir (Probadas)":
            df = df[df['probada'] == 1]
        elif filtro_estado == "Por Probar (Pendientes)":
            df = df[df['probada'] == 0]

        if filtro_sabor != "Todos":
            df = df[df['tipo_sabor'] == filtro_sabor]

        if filtro_metodo != "Todos":
            df = df[df['metodo_coccion'] == filtro_metodo]

        if busqueda_texto.strip():
            termino = busqueda_texto.strip().lower()
            df = df[df['nombre'].str.lower().str.contains(termino, na=False) | 
                    df['ingredientes'].str.lower().str.contains(termino, na=False)]
    else:
        df = pd.DataFrame()

    if df.empty:
        st.info("No se encontraron recetas con los filtros o términos de búsqueda indicados.")
    else:
        st.caption(f"Mostrando {len(df)} receta(s) encontrada(s)")
        for _, row in df.iterrows():
            tag_sabor = "🍰 Dulce" if row.get('tipo_sabor') == "Dulce" else "🧂 Salada"
            
            iconos_metodo = {
                "Al Horno": "🔥 Al Horno",
                "A la Olla / Cacerola": "🍲 A la Olla",
                "Freidora de aire": "🌪️ Airfryer",
                "Sartén / Hornalla": "🍳 En Sartén",
                "Sin cocción": "🥗 Sin Cocción"
            }
            metodo_nombre = row.get('metodo_coccion') if row.get('metodo_coccion') else "Al Horno"
            tag_metodo = iconos_metodo.get(metodo_nombre, f"🍳 {metodo_nombre}")
            tag_estado = "⭐ Para Repetir" if row.get('probada') == 1 else "⏳ Por Probar"
            
            with st.expander(f"{row['nombre']} — [{tag_sabor} | {tag_metodo}] — {tag_estado}"):
                if es_admin:
                    sub_ver, sub_editar = st.tabs(["👁️ Ver Receta", "✏️ Modificar / Eliminar"])
                else:
                    sub_ver = st.container()
                
                # --- VISTA NORMAL ---
                with sub_ver:
                    col_info, col_media = st.columns([1, 1])
                    with col_info:
                        st.markdown(f"**Método:** {tag_metodo}")
                        st.markdown("#### 🛒 Ingredientes")
                        for ing in [i.strip() for i in str(row.get('ingredientes', '')).split(",") if i.strip()]:
                            st.markdown(f"- {ing}")
                        st.markdown("#### 📝 Preparación")
                        st.write(row.get('pasos') if row.get('pasos') else "Sin pasos detallados.")
                        
                        marcado = st.checkbox("¿Receta probada / Para repetir?", value=bool(row.get('probada')), key=f"ver_probada_{row['id']}", disabled=not es_admin)
                        if es_admin and marcado != bool(row.get('probada')):
                            supabase.table("recetas").update({"probada": 1 if marcado else 0}).eq("id", row['id']).execute()
                            st.rerun()

                    with col_media:
                        st.markdown("#### 🎥 Video")
                        if row.get('origen_video'):
                            if row.get('tipo_video') == 'local' and os.path.exists(row['origen_video']):
                                st.video(row['origen_video'])
                            elif row.get('tipo_video') == 'enlace':
                                st.video(row['origen_video'])
                            else:
                                st.warning("Video local no encontrado en la carpeta VIDEOS.")
                        else:
                            st.info("Sin video asignado.")

                # --- MODO EDICIÓN (SOLO ADMINISTRADOR) ---
                if es_admin:
                    with sub_editar:
                        with st.form(f"form_editar_{row['id']}"):
                            edit_nombre = st.text_input("Nombre", value=row['nombre'])
                            col_e1, col_e2 = st.columns(2)
                            with col_e1:
                                edit_sabor = st.radio("Sabor", ["Salada", "Dulce"], index=0 if row.get('tipo_sabor') == "Salada" else 1, horizontal=True)
                            with col_e2:
                                idx_metodo = OPCIONES_METODO.index(metodo_nombre) if metodo_nombre in OPCIONES_METODO else 0
                                edit_metodo = st.selectbox("Método de cocción", OPCIONES_METODO, index=idx_metodo)
                            
                            edit_ingredientes = st.text_area("Ingredientes (separados por coma)", value=row.get('ingredientes', ''))
                            edit_pasos = st.text_area("Instrucciones", value=row.get('pasos') if row.get('pasos') else "")
                            
                            st.markdown("##### Modificar o Cargar Video")
                            edit_video_url = st.text_input("Enlace web de video (dejar vacío si vas a subir archivo)", value=row.get('origen_video', '') if row.get('tipo_video') == 'enlace' else "")
                            edit_video_file = st.file_uploader("O subir/reemplazar video desde la PC (.mp4, .mov)", type=["mp4", "mov", "avi", "mkv"])
                            
                            col_btn1, col_btn2 = st.columns([1, 1])
                            with col_btn1:
                                guardar_cambios = st.form_submit_button("💾 Guardar Cambios")
                            with col_btn2:
                                borrar_receta = st.form_submit_button("🗑️ Eliminar Receta")

                            if guardar_cambios:
                                nuevo_tipo_video = row.get('tipo_video', 'ninguno')
                                nuevo_origen_video = row.get('origen_video', '')
                                
                                if edit_video_file is not None:
                                    nombre_archivo_seguro = f"{edit_nombre.strip().replace(' ', '_').lower()}_{edit_video_file.name}"
                                    ruta_guardado = os.path.join(CARPETA_VIDEOS, nombre_archivo_seguro)
                                    with open(ruta_guardado, "wb") as f:
                                        f.write(edit_video_file.getbuffer())
                                    nuevo_tipo_video = "local"
                                    nuevo_origen_video = ruta_guardado
                                elif edit_video_url.strip():
                                    nuevo_tipo_video = "enlace"
                                    nuevo_origen_video = edit_video_url.strip()

                                supabase.table("recetas").update({
                                    "nombre": edit_nombre.strip(),
                                    "tipo_sabor": edit_sabor,
                                    "metodo_coccion": edit_metodo,
                                    "es_airfryer": 1 if edit_metodo == "Freidora de aire" else 0,
                                    "ingredientes": edit_ingredientes.strip().lower(),
                                    "pasos": edit_pasos.strip(),
                                    "tipo_video": nuevo_tipo_video,
                                    "origen_video": nuevo_origen_video
                                }).eq("id", row['id']).execute()

                                st.success("¡Receta actualizada!")
                                st.rerun()

                            if borrar_receta:
                                supabase.table("recetas").delete().eq("id", row['id']).execute()
                                st.warning(f"Receta '{row['nombre']}' eliminada.")
                                st.rerun()

# ========================================================
# TAB 2: ÍNDICE ALFABÉTICO (A-Z)
# ========================================================
with tab_indice:
    st.subheader("🔤 Índice Alfabético de Recetas")
    df_indice = obtener_todas_recetas()
    
    if df_indice.empty:
        st.info("Aún no tienes recetas cargadas en el recetario.")
    else:
        df_indice['letra'] = df_indice['nombre'].str[0].str.upper()
        letras_disponibles = sorted(df_indice['letra'].dropna().unique())
        
        st.markdown(f"**Letras disponibles:** {' • '.join(letras_disponibles)}")
        st.markdown("---")
        
        for letra in letras_disponibles:
            st.markdown(f"<div class='indice-letra'>{letra}</div>", unsafe_allow_html=True)
            recetas_letra = df_indice[df_indice['letra'] == letra]
            
            for _, row in recetas_letra.iterrows():
                tag_sabor = "🍰 Dulce" if row.get('tipo_sabor') == "Dulce" else "🧂 Salada"
                tag_metodo = row.get('metodo_coccion') if row.get('metodo_coccion') else "Al Horno"
                tag_estado = "⭐ Probada" if row.get('probada') == 1 else "⏳ Por probar"
                
                with st.expander(f"{row['nombre']} — [{tag_sabor} | {tag_metodo}] ({tag_estado})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("##### Ingredientes")
                        for ing in [i.strip() for i in str(row.get('ingredientes', '')).split(",") if i.strip()]:
                            st.markdown(f"- {ing}")
                    with col2:
                        st.markdown("##### Preparación")
                        st.write(row.get('pasos') if row.get('pasos') else "Sin pasos.")
                        if row.get('origen_video'):
                            if row.get('tipo_video') == 'local' and os.path.exists(row['origen_video']):
                                st.video(row['origen_video'])
                            elif row.get('tipo_video') == 'enlace':
                                st.video(row['origen_video'])

# ========================================================
# TAB 3: AGREGAR NUEVA RECETA (SOLO ADMINISTRADOR)
# ========================================================
if es_admin:
    with tab_agregar:
        st.subheader("Cargar una nueva receta")
        
        with st.form("form_alta_receta", clear_on_submit=True):
            nombre = st.text_input("Nombre de la receta *")
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                tipo_sabor = st.selectbox("Sabor *", ["Salada", "Dulce"])
            with col_c2:
                metodo_coccion = st.selectbox("Método de cocción *", OPCIONES_METODO)
                
            ingredientes = st.text_area("Ingredientes (separados por coma, ej: 500 gr harina, 10 gr sal) *")
            pasos = st.text_area("Instrucciones / Paso a paso")
            
            st.markdown("#### Opciones de Video")
            video_url = st.text_input("Enlace web de video (YouTube, TikTok, Instagram - Opcional)")
            video_subido = st.file_uploader("O subir archivo de video (.mp4, .mov)", type=["mp4", "mov", "avi", "mkv"])
                
            probada_inicial = st.checkbox("¿Ya la probaste y es para repetir?")
            
            btn_guardar = st.form_submit_button("💾 Guardar Receta", type="primary")
            
            if btn_guardar:
                if not nombre.strip() or not ingredientes.strip():
                    st.error("Por favor completa al menos el nombre y los ingredientes.")
                else:
                    tipo_final = "ninguno"
                    origen_final = ""
                    
                    if video_subido is not None:
                        nombre_archivo_seguro = f"{nombre.strip().replace(' ', '_').lower()}_{video_subido.name}"
                        ruta_guardado = os.path.join(CARPETA_VIDEOS, nombre_archivo_seguro)
                        with open(ruta_guardado, "wb") as f:
                            f.write(video_subido.getbuffer())
                        tipo_final = "local"
                        origen_final = ruta_guardado
                    elif video_url.strip():
                        tipo_final = "enlace"
                        origen_final = video_url.strip()
                    
                    supabase.table("recetas").insert({
                        "nombre": nombre.strip(),
                        "tipo_sabor": tipo_sabor,
                        "metodo_coccion": metodo_coccion,
                        "es_airfryer": 1 if metodo_coccion == "Freidora de aire" else 0,
                        "ingredientes": ingredientes.strip().lower(),
                        "pasos": pasos.strip(),
                        "tipo_video": tipo_final,
                        "origen_video": origen_final,
                        "probada": 1 if probada_inicial else 0
                    }).execute()

                    st.success(f"¡Receta '{nombre}' guardada con éxito!")
                    st.rerun()

# ========================================================
# TAB 4: BUSCADOR POR DESPENSA
# ========================================================
with tab_despensa:
    st.subheader("¿Qué tienes en casa?")
    ingredientes_disponibles = st.text_input("Ingresa los ingredientes que tienes (ej: huevo, queso, harina)")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        solo_probadas = st.checkbox("Mostrar únicamente recetas probadas", value=False)
    with col_d2:
        filtro_metodo_despensa = st.selectbox("Filtrar por método:", ["Todos"] + OPCIONES_METODO)
    
    if ingredientes_disponibles:
        set_casa = {item.strip().lower() for item in ingredientes_disponibles.split(",") if item.strip()}
        
        todas_df = obtener_todas_recetas()
        if not todas_df.empty:
            if solo_probadas:
                todas_df = todas_df[todas_df['probada'] == 1]
            if filtro_metodo_despensa != "Todos":
                todas_df = todas_df[todas_df['metodo_coccion'] == filtro_metodo_despensa]
                
            completas = []
            parciales = []
            
            for _, fila in todas_df.iterrows():
                items_receta = [i.strip().lower() for i in str(fila.get('ingredientes', '')).split(",") if i.strip()]
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
                    tipo_txt = f"{r.get('tipo_sabor')} | {r.get('metodo_coccion')}"
                    with st.expander(f"🟢 {r['nombre']} ({tipo_txt})"):
                        st.write(f"**Ingredientes:** {r.get('ingredientes')}")
                        st.write(f"**Pasos:** {r.get('pasos')}")
                        if r.get('origen_video'):
                            st.video(r['origen_video'])
                            
            if parciales:
                st.markdown("### 🟡 Recetas a las que les falta poco:")
                parciales.sort(key=lambda x: x[2], reverse=True)
                for r, faltantes, pct in parciales:
                    tipo_txt = f"{r.get('tipo_sabor')} | {r.get('metodo_coccion')}"
                    with st.expander(f"🟡 {r['nombre']} ({tipo_txt}) — Coincidencia: {pct:.0f}%"):
                        st.write(f"**Te falta:** {', '.join(faltantes)}")
                        st.write(f"**Ingredientes:** {r.get('ingredientes')}")
                        if r.get('origen_video'):
                            st.video(r['origen_video'])
        else:
            st.info("No hay recetas disponibles.")
