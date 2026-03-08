import pandas as pd
import os
import json
import shutil
from datetime import datetime

FILE_NAME = "pedidos_pro.csv"
BASE_DIR = "PEDIDOS_CARPINTERIA"

def inicializar_db():
    if not os.path.exists(BASE_DIR): os.makedirs(BASE_DIR)
    if not os.path.exists(FILE_NAME):
        columnas = ['Obra', 'Empresa', 'Ruta_Carpeta', 'Estado', 'Contactos', 
                   'Fecha_Entrega', 'Historial_Fechas', 'Fecha_Creacion', 
                   'Ultima_Modif', 'Motivo_Modif', 'Checklist', 'Prioridad', 'Cobro', 'Material']
        df = pd.DataFrame(columns=columnas)
        df.to_csv(FILE_NAME, index=False)

def realizar_backup():
    if os.path.exists(FILE_NAME):
        if not os.path.exists("BACKUPS"): os.makedirs("BACKUPS")
        fecha = datetime.now().strftime("%Y%m%d")
        destino = f"BACKUPS/copia_{fecha}.csv"
        if not os.path.exists(destino): shutil.copy(FILE_NAME, destino)

def guardar_registro(nuevo_dato):
    df = pd.read_csv(FILE_NAME)
    for campo in ['Contactos', 'Historial_Fechas', 'Checklist']:
        if campo not in nuevo_dato: nuevo_dato[campo] = "{}" if campo == 'Checklist' else "[]"
    nuevo_dato['Prioridad'] = 'NO'
    nuevo_dato['Cobro'] = 'PENDIENTE'
    nuevo_dato['Fecha_Creacion'] = datetime.now().strftime("%d/%m/%Y %H:%M")
    df = pd.concat([df, pd.DataFrame([nuevo_dato])], ignore_index=True)
    df.to_csv(FILE_NAME, index=False)

def obtener_todo():
    if not os.path.exists(FILE_NAME): inicializar_db()
    return pd.read_csv(FILE_NAME)

def actualizar_fila(idx, nuevos_datos):
    df = pd.read_csv(FILE_NAME)
    for clave, valor in nuevos_datos.items(): df.at[idx, clave] = valor
    df.to_csv(FILE_NAME, index=False)

def crear_carpetas_obra(nombre_obra):
    nombre_limpio = "".join([c for c in nombre_obra if c.isalnum() or c in (' ', '_')]).rstrip()
    ruta = os.path.join(BASE_DIR, nombre_limpio)
    for sub in ["Despiece", "Presupuestos", "Facturas", "Fotos", "Diseños", "Notas_Escaneadas"]:
        os.makedirs(os.path.join(ruta, sub), exist_ok=True)
    return ruta

def borrar_obra(nombre_obra):
    df = pd.read_csv(FILE_NAME)
    df = df[df['Obra'] != nombre_obra]
    df.to_csv(FILE_NAME, index=False)
    return True