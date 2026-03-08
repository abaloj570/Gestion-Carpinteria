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

st.set_page_config(page_title="Medición Pro - Fotos y Plantillas", layout="centered")

# --- LISTAS Y PLANTILLAS ---
TIPOS_ELEMENTO = ["Armario", "Puerta de Paso", "Puerta Entrada", "Puerta Corredera", "Cocina", "Otro"]
MATERIALES = ["Melamina Blanca 19", "Melamina Roble 19", "DM Crudo", "Pino", "Roble Macizo", "Lacado"]

# Diccionario de plantillas (puedes sustituir las rutas por dibujos reales .png)
PLANTILLAS = {
    "Armario": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/shelter.png", # Ejemplo
    "Puerta de Paso": "https://img.icons8.com/ios/452/door.png",
    "Puerta Corredera": "https://img.icons8.com/ios/452/sliding-door.png"
}

if 'lista_medidas' not in st.session_state:
    st.session_state.lista_medidas = []

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
        
        # Insertar Foto Real si existe
        if item['foto_real']:
            pdf.cell(0, 10, "FOTO REAL:", 0, 1)
            pdf.image(item['foto_real'], x=10, w=80)
            pdf.ln(5)
            
        # Insertar Croquis
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
    a = c1.number_input("Alto", value=0.0)
    l = c2.number_input("Ancho", value=0.0)
    f = c3.number_input("Fondo", value=0.0)

    # 1. FOTO REAL (Cámara)
    st.write("📸 Foto del hueco:")
    foto_captura = st.camera_input("Hacer foto para el taller", key=f"cam_{len(st.session_state.lista_medidas)}")

    # 2. CROQUIS CON PLANTILLA
    st.write("🖌️ Dibujo (Usa la plantilla de fondo):")
    bg_image = None # Aquí podrías cargar una imagen local si la tienes
    
    canvas_res = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=3,
        background_color="#eeeeee",
        height=300,
        drawing_mode="freedraw",
        key=f"v5_{tipo}_{len(st.session_state.lista_medidas)}"
    )

    # 3. VOZ A TEXTO (Aprovechamos el dictado nativo del móvil)
    st.info("💡 Pulsa el micro del teclado para dictar las notas")
    notas = st.text_area("Notas dictadas o escritas:", placeholder="Ej: Pared desplomada 2cm a la derecha...")

    if st.button("➕ GUARDAR ELEMENTO EN LA LISTA"):
        t_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar Foto Real
        f_real_path = None
        if foto_captura:
            f_real_path = f"foto_{t_stamp}.png"
            img_p = Image.open(foto_captura)
            img_p.save(f_real_path)

        # Guardar Croquis
        img_path = None
        if canvas_res.image_data is not None:
            img_path = f"croquis_{t_stamp}.png"
            cv2.imwrite(img_path, cv2.cvtColor(canvas_res.image_data.astype(np.uint8), cv2.COLOR_RGBA2BGR))
        
        st.session_state.lista_medidas.append({
            'tipo': tipo, 'cant': cant, 'mat': "Por definir", 'alto': a, 'ancho': l, 'fondo': f, 
            'notas': notas, 'croquis': img_path, 'foto_real': f_real_path, 'mano': mano
        })
        st.success("Elemento añadido.")

# --- FINALIZAR ---
if st.session_state.lista_medidas:
    st.divider()
    if st.button("💾 GENERAR INFORME FINAL (PDF)"):
        ruta_c = row_obra['Ruta_Carpeta']
        # Mover archivos a carpeta de la obra
        for m in st.session_state.lista_medidas:
            if m['foto_real']:
                dest = os.path.join(ruta_c, "Fotos", m['foto_real'])
                os.rename(m['foto_real'], dest)
                m['foto_real'] = dest
            if m['croquis']:
                dest = os.path.join(ruta_c, "Fotos", m['croquis'])
                os.rename(m['croquis'], dest)
                m['croquis'] = dest
        
        pdf_f = generar_pdf_reforma(obra_sel, st.session_state.lista_medidas, ruta_c)
        st.session_state.lista_medidas = []
        st.success(f"Informe PDF creado en la carpeta de la obra")
        st.balloons()
