import streamlit as st
import pandas as pd
import os
import cv2
import numpy as np
from datetime import datetime
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF
from PIL import Image

# --- CONFIGURACIÓN ---
FILE_NAME = "pedidos_pro.csv"
BASE_DIR = "PEDIDOS_CARPINTERIA"

st.set_page_config(page_title="Medición Pro - Carpintería", layout="centered")

# --- ESTADO DE LA SESIÓN ---
if 'lista_medidas' not in st.session_state:
    st.session_state.lista_medidas = []

# --- CLASE PDF ---
class PDF_Reforma(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'INFORME DE MEDICION TECNICA - REFORMA', 0, 1, 'C')

def generar_pdf_reforma(obra, lista, ruta_destino):
    pdf = PDF_Reforma()
    for i, item in enumerate(lista):
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        titulo = f"Elemento {i+1}: {item['tipo']}"
        if item['mano']: titulo += f" ({item['mano']})"
        pdf.cell(0, 10, titulo, 0, 1)
        
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f"Cantidad: {item['cant']} | Medidas: {item['alto']} x {item['ancho']} x {item['fondo']} cm", 0, 1)
        
        # Foto Real
        if item['foto_real'] and os.path.exists(item['foto_real']):
            pdf.ln(5)
            pdf.cell(0, 10, "FOTO DEL HUECO:", 0, 1)
            pdf.image(item['foto_real'], x=10, w=90)
            pdf.ln(5)

        # Croquis con plantilla
        if item['croquis'] and os.path.exists(item['croquis']):
            pdf.cell(0, 10, "CROQUIS DETALLADO:", 0, 1)
            pdf.image(item['croquis'], x=10, w=110)

        pdf.ln(10)
        pdf.set_font('Arial', 'I', 11)
        pdf.multi_cell(0, 8, f"NOTAS Y OBSERVACIONES: {item['notas']}")
        
    nombre_f = f"Reforma_{obra}_{datetime.now().strftime('%H%M')}.pdf".replace(" ", "_")
    ruta_pdf = os.path.join(ruta_destino, nombre_f)
    pdf.output(ruta_pdf)
    return ruta_pdf

# --- INTERFAZ ---
st.title("🏗️ Medición de Reforma")

if os.path.exists(FILE_NAME):
    df_obras = pd.read_csv(FILE_NAME)
    obra_sel = st.selectbox("Selecciona la Obra:", df_obras['Obra'].tolist())
    row_obra = df_obras[df_obras['Obra'] == obra_sel].iloc[0]
else:
    st.error("No hay obras en el sistema. Créalas primero en el PC.")
    st.stop()

# --- FORMULARIO DE ELEMENTO ---
with st.expander("➕ AÑADIR ELEMENTO A LA MEDICIÓN", expanded=True):
    tipos = ["Armario", "Puerta de Paso", "Puerta Entrada", "Puerta Corredera", "Cocina", "Suelo", "Otro"]
    tipo = st.selectbox("¿Qué vas a medir?", tipos)
    
    col_c, col_m = st.columns(2)
    cant = col_c.number_input("Cantidad", min_value=1, value=1)
    mano = None
    if "Puerta" in tipo and "Corredera" not in tipo:
        mano = col_m.radio("Mano de apertura:", ["Derecha", "Izquierda"], horizontal=True)

    c1, c2, c3 = st.columns(3)
    a = c1.number_input("Alto (cm)", value=0.0)
    l = c2.number_input("Ancho (cm)", value=0.0)
    f = c3.number_input("Fondo (cm)", value=0.0)

    # 1. CÁMARA REAL
    st.write("📸 **Foto Real (Hueco/Entorno):**")
    foto_captura = st.camera_input("Hacer foto", key=f"cam_{len(st.session_state.lista_medidas)}")

    # 2. LIENZO CON PLANTILLA GENERADA
    st.write("🖌️ **Croquis (Anota descuadres sobre la silueta):**")
    
    # Crear silueta gris de fondo
    bg_img = np.ones((300, 400, 3), dtype=np.uint8) * 245 # Gris muy claro
    if "Puerta" in tipo:
        cv2.rectangle(bg_img, (150, 50), (250, 280), (200, 200, 200), 2)
        cv2.circle(bg_img, (235, 170), 4, (200, 200, 200), -1)
    elif tipo == "Armario":
        cv2.rectangle(bg_img, (100, 40), (300, 260), (200, 200, 200), 2)
        cv2.line(bg_img, (200, 40), (200, 260), (200, 200, 200), 2)
    elif tipo == "Cocina":
        cv2.rectangle(bg_img, (80, 150), (320, 250), (200, 200, 200), 2) # Encimera
        cv2.rectangle(bg_img, (80, 50), (320, 120), (200, 200, 200), 1)  # Muebles altos

    canvas_res = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=3,
        stroke_color="#000000",
        background_image=Image.fromarray(bg_img),
        height=300, width=400,
        drawing_mode="freedraw",
        key=f"canvas_{tipo}_{len(st.session_state.lista_medidas)}",
    )

    # 3. NOTAS POR VOZ
    st.info("🎤 **Dictado:** Pulsa el micro del teclado de tu móvil para dictar notas.")
    notas = st.text_area("Observaciones técnicas:", placeholder="Ej: Falsa escuadra en rincón derecho...")

    if st.button("✅ GUARDAR ELEMENTO Y CONTINUAR"):
        t_stamp = datetime.now().strftime("%H%M%S")
        
        # Guardar archivos temporales
        f_real = None
        if foto_captura:
            f_real = f"temp_f_{t_stamp}.png"
            Image.open(foto_captura).save(f_real)

        f_croquis = None
        if canvas_res.image_data is not None:
            f_croquis = f"temp_c_{t_stamp}.png"
            cv2.imwrite(f_croquis, cv2.cvtColor(canvas_res.image_data.astype(np.uint8), cv2.COLOR_RGBA2BGR))
        
        st.session_state.lista_medidas.append({
            'tipo': tipo, 'cant': cant, 'alto': a, 'ancho': l, 'fondo': f, 
            'notas': notas, 'croquis': f_croquis, 'foto_real': f_real, 'mano': mano,
            'mat': "Melamina/Madera"
        })
        st.success(f"Añadido: {tipo}. Puedes añadir otro o finalizar abajo.")

# --- RESUMEN Y FINALIZAR ---
if st.session_state.lista_medidas:
    st.divider()
    st.subheader("📋 Resumen de la Medición")
    for i, m in enumerate(st.session_state.lista_medidas):
        st.write(f"**{i+1}. {m['tipo']}** - {m['alto']}x{m['ancho']} cm")
    
    if st.button("💾 FINALIZAR REFORMA Y GENERAR PDF"):
        folder = row_obra['Ruta_Carpeta']
        os.makedirs(os.path.join(folder, "Fotos"), exist_ok=True)
        
        # Mover fotos temporales a la carpeta definitiva
        for m in st.session_state.lista_medidas:
            if m['foto_real']:
                dest = os.path.join(folder, "Fotos", m['foto_real'])
                os.rename(m['foto_real'], dest)
                m['foto_real'] = dest
            if m['croquis']:
                dest = os.path.join(folder, "Fotos", m['croquis'])
                os.rename(m['croquis'], dest)
                m['croquis'] = dest
        
        pdf_f = generar_pdf_reforma(obra_sel, st.session_state.lista_medidas, folder)
        st.session_state.lista_medidas = []
        st.success(f"✅ Medición guardada en la carpeta de la obra.")
        st.balloons()

if st.button("🗑️ Vaciar todo"):
    st.session_state.lista_medidas = []
    st.rerun()

