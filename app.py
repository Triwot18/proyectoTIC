import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. ESTO DEBE IR PRIMERO SIEMPRE (Configuración de página)
st.set_page_config(page_title="Caserito Store", page_icon="✂️", layout="wide")

st.title("✂️ Caserito Store: Control de Inventario")

# 2. BOTÓN DE EMERGENCIA (Justo después del título)
if st.button("🔄 Forzar Reinicio de Conexión"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

# --- CONEXIÓN A GOOGLE SHEETS ---
# Usamos el link limpio (sin el ?usp=sharing para evitar problemas)
url_sheet = "https://docs.google.com/spreadsheets/d/1MfLBejcF2aOLi6JeZgXij8p1rZ1EPZzsV9NGpNvsJC4/edit"

# Creamos la conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para traer los datos frescos
def cargar_datos():
    # Especificamos worksheet="Insumos" para ser precisos y evitar errores si mueves las hojas
    return conn.read(spreadsheet=url_sheet, worksheet="Insumos")

# --- INTERFAZ DE USUARIO ---

# 1. MOSTRAR INVENTARIO ACTUAL
st.subheader("📦 Almacén de Telas e Insumos")

# Manejo de errores por si la hoja está vacía o falla la carga
try:
    df_insumos = cargar_datos()
    # Mostramos la tabla interactiva
    st.dataframe(df_insumos, width='stretch')
except Exception as e:
    st.error(f"No se pudo cargar la tabla. Verifica que la hoja se llame 'Insumos'. Error: {e}")
    df_insumos = pd.DataFrame() # DataFrame vacío para que no falle lo de abajo

# 2. FORMULARIO PARA AGREGAR NUEVO MATERIAL
st.divider()
st.subheader("➕ Registrar Nueva Compra / Material")

with st.form("form_nuevo_insumo"):
    col1, col2 = st.columns(2)
    
    with col1:
        nuevo_id = st.text_input("Código (ID)", placeholder="Ej: T-005")
        nuevo_nombre = st.text_input("Nombre del Material", placeholder="Ej: Paño Inglés Gris")
        nueva_categoria = st.selectbox("Categoría", ["Tela", "Forro", "Avíos (Botones/Cierres)", "Hilos", "Otros"])
    
    with col2:
        nuevo_stock = st.number_input("Cantidad Comprada", min_value=0.0, step=0.1)
        nueva_unidad = st.selectbox("Unidad de Medida", ["Metros", "Unidades", "Conos", "Yardas"])
        nuevo_costo = st.number_input("Costo Total de la Compra (Bs)", min_value=0.0, step=1.0)
        stock_minimo = st.number_input("Alerta de Stock Mínimo", value=5.0)

    # Botón de envío
    submitted = st.form_submit_button("💾 Guardar en Inventario")

    if submitted:
        # Verificamos que no falten datos básicos
        if not nuevo_id or not nuevo_nombre:
            st.warning("⚠️ El ID y el Nombre son obligatorios.")
        else:
            try:
                # 1. Crear el nuevo registro
                nuevo_dato = pd.DataFrame([{
                    "ID": nuevo_id,
                    "Nombre": nuevo_nombre,
                    "Categoria": nueva_categoria,
                    "Stock_Actual": nuevo_stock,
                    "Unidad": nueva_unidad,
                    "Stock_Minimo": stock_minimo,
                    "Costo_Promedio": nuevo_costo
                }])

                # 2. Unir con los datos existentes
                # Si la tabla estaba vacía, el nuevo dato es el único
                if df_insumos.empty:
                    df_actualizado = nuevo_dato
                else:
                    df_actualizado = pd.concat([df_insumos, nuevo_dato], ignore_index=True)

                # 3. Subir TODO de nuevo a Google Sheets
                conn.update(spreadsheet=url_sheet, worksheet="Insumos", data=df_actualizado)
                
                st.success(f"✅ ¡{nuevo_nombre} agregado correctamente!")
                
                # 4. Esperar 1 segundo y recargar
                import time
                time.sleep(1) 
                st.rerun()
                
            except Exception as e:
                st.error(f"Error al guardar: {e}")
                st.info("💡 Consejo: Verifica que en Google Sheets el usuario 'bot-tic@...' tenga permiso de EDITOR.")