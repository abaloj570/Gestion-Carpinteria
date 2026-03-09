import streamlit as st
import pandas as pd
import os
import json
import cv2
import numpy as np
from datetime import datetime
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
from PIL import Image

# --- CONFIGURACIÓN ---
FILE_NAME = "pedidos_pro.csv"
BASE_DIR = "PEDIDOS_CARPINTERIA"
PLANTILLAS_DIR = "plantillas"

if not os.path.exists(PLANTILLAS_DIR):
    os.makedirs(PLANTILLAS_DIR)

st.set_page_config(page_title="Medición Pro - Fotos y Plantillas", layout="centered")

# --- CSS PARA FORZAR PANTALLA COMPLETA REAL ---
st.markdown("""
    <style>
    div[data-testid="stDialog"] div[role="dialog"] {
        max-width: 95vw !important;
        width: 95vw !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LISTAS Y PLANTILLAS ---
TIPOS_ELEMENTO = ["Armario", "Puerta de Paso", "Puerta Entrada", "Puerta Corredera", "Cocina", "Otro"]

if 'lista_medidas' not in st.session_state:
    st.session_state.lista_medidas = []
if 'temp_canvas_data' not in st.session_state:
    st.session_state.temp_canvas_data = None

# --- FUNCIÓN PANTALLA COMPLETA ---
@st.dialog("CROQUIS A PANTALLA COMPLETA")
def pantalla_completa_dibujo(bg_image):
    st.write("Gira el móvil para dibujar mejor")
    # Lienzo maximizado
    canvas_full = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=3,
        stroke_color="#000000",
        background_image=bg_image,
        background_color="#ffffff" if bg_image is None else None,
        height=600, # Mucho más alto
        width=800,  # Mucho más ancho
        drawing_mode="freedraw",
        key="full_canvas"
    )
    if st.button("✅ FINALIZAR Y GUARDAR DIBUJO"):
        if canvas_full.image_data is not None:
            st.session_state.temp_canvas_data = canvas_full.image_data
            st.rerun()

# --- CLASE PDF ---
class PDF_Reforma(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'INFORME DE MEDICIÓN TÉCNICA', 0, 1, 'C')

def generar_pdf_reforma(obra, lista, ruta_destino):
    pdf = PDF_Reforma()
    for i, item in enumerate(lista):
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f"{i+1}. {item['tipo']} {'('+item['mano']+')' if item['mano'] else ''}", 0, 1)
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 8, f"Cant: {item['cant']} | Mat: {item['mat']} | Medidas: {item['alto']}x{item['ancho']}x{item['fondo']}", 0, 1)
        if item['foto_real']:
            pdf.cell(0, 10, "FOTO REAL:", 0, 1)
            pdf.image(item['foto_real'], x=10, w=80)
            pdf.ln(5)
        if item['croquis'] and os.path.exists(item['croquis']):
            pdf.cell(0, 10, "CROQUIS / PLANTA:", 0, 1)
            pdf.image(item['croquis'], x=10, w=100)
        pdf.ln(5)
        pdf.multi_cell(0, 8, f"NOTAS: {item['notas']}")
    nombre_f = f"Reforma_{obra}_{datetime.now().strftime('%H%M')}.pdf".replace(" ", "_")
    ruta_pdf = os.path.join(ruta_destino, nombre_f)
    pdf.output(ruta_pdf)
    return ruta_pdf

# --- INTERFAZ ---
st.title("🏗️ Medición Inteligente")

if os.path.exists(FILE_NAME):
    df_obras = pd.read_csv(FILE_NAME)
    obra_sel = st.selectbox("Obra:", df_obras['Obra'].tolist())
    row_obra = df_obras[df_obras['Obra'] == obra_sel].iloc[0]
else:
    st.stop()

# --- FORMULARIO ---
with st.expander("➕ AÑADIR ELEMENTO", expanded=True):
    tipo = st.selectbox("Elemento:", TIPOS_ELEMENTO)
    col1, col2 = st.columns(2)
    cant = col1.number_input("Cant.", min_value=1, value=1)
    mano = None
    if tipo in ["Puerta de Paso", "Puerta Entrada"]:
        mano = col2.radio("Mano:", ["Derecha", "Izquierda"], horizontal=True)

    c1, c2, c3 = st.columns(3)
    a, l, f = c1.number_input("Alto", value=0.0), c2.number_input("Ancho", value=0.0), c3.number_input("Fondo", value=0.0)

    st.write("📸 Foto del hueco:")
    foto_captura = st.camera_input("Hacer foto", key=f"cam_{len(st.session_state.lista_medidas)}")

    # --- SECCIÓN DE DIBUJO ---
    st.divider()
    st.write("🖌️ Croquis:")
    opcion_fondo = st.radio("Fondo:", ["Blanco", "Usar Plantilla"], horizontal=True)
    
    bg_image = None
    if opcion_fondo == "Usar Plantilla":
        archivos = [f for f in os.listdir(PLANTILLAS_DIR) if f.lower().endswith(('.png', '.jpg'))]
        if archivos:
            plantilla_sel = st.selectbox("Selecciona plantilla:", archivos)
            bg_image = Image.open(os.path.join(PLANTILLAS_DIR, plantilla_sel)).convert("RGB")
    
    # Botón para abrir el lienzo Gigante
    if st.button("🔍 DIBUJAR A PANTALLA COMPLETA", use_container_width=True):
        pantalla_completa_dibujo(bg_image)

    # Vista previa pequeña para confirmar que hay dibujo
    if st.session_state.temp_canvas_data is not None:
        st.image(st.session_state.temp_canvas_data, caption="Dibujo capturado", width=250)

    notas = st.text_area("Notas dictadas o escritas:")

    if st.button("➕ GUARDAR ELEMENTO EN LA LISTA"):
        t_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        f_real_path = None
        if foto_captura:
            f_real_path = f"foto_{t_stamp}.png"
            Image.open(foto_captura).save(f_real_path)

        img_path = None
        if st.session_state.temp_canvas_data is not None:
            img_path = f"croquis_{t_stamp}.png"
            cv2.imwrite(img_path, cv2.cvtColor(st.session_state.temp_canvas_data.astype(np.uint8), cv2.COLOR_RGBA2BGR))
        
        st.session_state.lista_medidas.append({
            'tipo': tipo, 'cant': cant, 'mat': "Por definir", 'alto': a, 'ancho': l, 'fondo': f, 
            'notas': notas, 'croquis': img_path, 'foto_real': f_real_path, 'mano': mano
        })
        st.session_state.temp_canvas_data = None # Reset dibujo
        st.success("Elemento añadido.")

# --- FINALIZAR ---
if st.session_state.lista_medidas:
    st.divider()
    if st.button("💾 GENERAR INFORME FINAL (PDF)"):
        ruta_c = row_obra['Ruta_Carpeta']
        os.makedirs(os.path.join(ruta_c, "Fotos"), exist_ok=True)
        for m in st.session_state.lista_medidas:
            for key in ['foto_real', 'croquis']:
                if m[key] and os.path.exists(m[key]):
                    dest = os.path.join(ruta_c, "Fotos", m[key])
                    os.rename(m[key], dest)
                    m[key] = dest
        generar_pdf_reforma(obra_sel, st.session_state.lista_medidas, ruta_c)
        st.session_state.lista_medidas = []
        st.success(f"Informe PDF creado")
        st.balloons()
