import streamlit as st
import pandas as pd
import os
import json
import cv2
import numpy as np
from datetime import datetime
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF

# --- CONFIGURACIÓN DE RUTAS ---
FILE_NAME = "pedidos_pro.csv"
BASE_DIR = "PEDIDOS_CARPINTERIA"

st.set_page_config(page_title="Carpintería PRO - Medición", layout="centered")

# --- LISTAS TÉCNICAS ---
LISTA_MATERIALES = ["Melamina Blanca 19mm", "Melamina Roble 19mm", "DM Crudo 16mm", "DM Crudo 19mm", "Pino Macizo", "Haya", "Roble Macizo", "Lacado Blanco"]

# --- CLASE PARA GENERAR EL PDF DE ORDEN DE TALLER ---
class PDF_Orden(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'ORDEN DE FABRICACIÓN / TALLER', 0, 1, 'C')
        self.ln(5)

def generar_pdf(datos, ruta_guardado, croquis_path=None):
    pdf = PDF_Orden()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)
    
    # Datos Principales
    pdf.cell(0, 10, f"Obra: {datos['obra']}", 0, 1)
    pdf.cell(0, 10, f"Cliente: {datos['cliente']}", 0, 1)
    pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", 0, 1)
    pdf.ln(5)
    
    # Especificaciones
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(0, 10, " ESPECIFICACIONES TÉCNICAS ", 1, 1, 'L', 1)
    pdf.cell(0, 10, f"Material: {datos['material']}", 1, 1)
    pdf.cell(0, 10, f"Medidas Hueco: {datos['alto']} x {datos['ancho']} x {datos['fondo']} cm", 1, 1)
    pdf.ln(5)
    
    # Despiece Sugerido
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, " DESPIECE ESTIMADO (Cuerpo 19mm) ", 1, 1, 'L', 1)
    g = 1.9
    pdf.cell(0, 8, f"- 2 Costados: {datos['alto']} x {datos['fondo']} cm", 0, 1)
    pdf.cell(0, 8, f"- Techo/Suelo: {float(datos['ancho']) - (2*g):.1f} x {datos['fondo']} cm", 0, 1)
    pdf.cell(0, 8, f"- Trasera: {float(datos['alto'])-0.5} x {float(datos['ancho'])-0.5} cm", 0, 1)
    pdf.ln(10)
    
    # Insertar Croquis si existe
    if croquis_path and os.path.exists(croquis_path):
        pdf.cell(0, 10, "CROQUIS DE MEDICIÓN:", 0, 1)
        pdf.image(croquis_path, x=10, w=180)
    
    nombre_pdf = f"Orden_{datos['obra']}.pdf".replace(" ", "_")
    ruta_completa = os.path.join(ruta_guardado, nombre_pdf)
    pdf.output(ruta_completa)
    return ruta_completa

# --- LÓGICA DE LA APP ---
st.title("📏 Medición y Orden de Taller")

if os.path.exists(FILE_NAME):
    df_obras = pd.read_csv(FILE_NAME)
    obra_sel = st.selectbox("Selecciona Obra:", ["-- NUEVA --"] + df_obras['Obra'].tolist())
else:
    obra_sel = "-- NUEVA --"

if obra_sel == "-- NUEVA --":
    with st.form("alta"):
        o = st.text_input("Nombre Obra")
        c = st.text_input("Cliente")
        if st.form_submit_button("Crear"):
            ruta = os.path.join(BASE_DIR, o.replace(" ", "_"))
            os.makedirs(os.path.join(ruta, "Fotos"), exist_ok=True)
            os.makedirs(os.path.join(ruta, "Despiece"), exist_ok=True)
            # Guardar en CSV (Lógica simplificada)
            new_df = pd.DataFrame([{'Obra':o, 'Empresa':c, 'Ruta_Carpeta':ruta, 'Estado':'TALLER', 'Historial_Fechas':'[]'}])
            new_df.to_csv(FILE_NAME, mode='a', header=not os.path.exists(FILE_NAME), index=False)
            st.success("Obra creada. Recarga.")
else:
    # Obtener datos de la obra seleccionada
    row_data = df_obras[df_obras['Obra'] == obra_sel].iloc[0]
    
    # 1. MATERIAL Y MEDIDAS
    col1, col2 = st.columns(2)
    with col1: material = st.selectbox("Material:", LISTA_MATERIALES)
    with col2: st.info(f"Cliente: {row_data['Empresa']}")
    
    c1, c2, c3 = st.columns(3)
    alto = c1.number_input("Alto (cm)", value=0.0)
    ancho = c2.number_input("Ancho (cm)", value=0.0)
    fondo = c3.number_input("Fondo (cm)", value=0.0)
    
    # 2. LIENZO DE DIBUJO
    st.subheader("🖌️ Croquis / Descuadres")
    canvas_result = st_canvas(
        fill_color="white", stroke_width=3, stroke_color="black",
        background_color="#eeeeee", height=300, key="canvas_full"
    )
    
    nota_t = st.text_area("Notas:")

    # 3. BOTÓN DE GUARDADO Y GENERACIÓN
    if st.button("💾 GUARDAR Y GENERAR ORDEN DE TALLER"):
        ruta_base = row_data['Ruta_Carpeta']
        timestamp = datetime.now().strftime("%H%M")
        
        # Guardar Croquis
        path_img = None
        if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
            path_img = os.path.join(ruta_base, "Fotos", f"Croquis_{timestamp}.png")
            img_bgr = cv2.cvtColor(canvas_result.image_data.astype(np.uint8), cv2.COLOR_RGBA2BGR)
            cv2.imwrite(path_img, img_bgr)
            
        # Generar PDF
        datos_pdf = {
            'obra': obra_sel, 'cliente': row_data['Empresa'],
            'material': material, 'alto': alto, 'ancho': ancho, 'fondo': fondo
        }
        ruta_pdf = generar_pdf(datos_pdf, os.path.join(ruta_base, "Despiece"), path_img)
        
        # Actualizar Historial en CSV
        hist = json.loads(row_data['Historial_Fechas']) if pd.notna(row_data['Historial_Fechas']) else []
        hist.append({"f": datetime.now().strftime("%d/%m %H:%M"), "n": f"Orden generada: {alto}x{ancho}x{fondo} - {material}"})
        
        # Guardado final en CSV
        df_full = pd.read_csv(FILE_NAME)
        idx = df_full[df_full['Obra'] == obra_sel].index[0]
        df_full.at[idx, 'Historial_Fechas'] = json.dumps(hist)
        df_full.at[idx, 'Material'] = material
        df_full.to_csv(FILE_NAME, index=False)
        
        st.success(f"✅ Orden guardada en: {ruta_pdf}")
        st.balloons()