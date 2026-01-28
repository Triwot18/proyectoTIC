import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Caserito Store", page_icon="✂️", layout="wide")
st.title("✂️ Caserito Store: Sistema de Producción")

# Botón de pánico para limpiar caché
if st.sidebar.button("🔄 Refrescar Datos"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

# --- 2. CONEXIÓN (La misma que ya funcionaba) ---
url_sheet = "https://docs.google.com/spreadsheets/d/1MfLBejcF2aOLi6JeZgXij8p1rZ1EPZzsV9NGpNvsJC4/edit"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. FUNCIONES DE CARGA DE DATOS ---
def cargar_insumos():
    return conn.read(spreadsheet=url_sheet, worksheet="Insumos")

def cargar_productos():
    # Si la hoja está vacía, devuelve un DataFrame con las columnas correctas
    try:
        df = conn.read(spreadsheet=url_sheet, worksheet="Productos")
        if df.empty:
            return pd.DataFrame(columns=["ID", "Nombre", "Precio_Venta", "Stock_Terminado"])
        return df
    except:
        return pd.DataFrame(columns=["ID", "Nombre", "Precio_Venta", "Stock_Terminado"])

def cargar_recetas():
    try:
        df = conn.read(spreadsheet=url_sheet, worksheet="Recetas")
        if df.empty:
            return pd.DataFrame(columns=["ID_Producto", "ID_Insumo", "Cantidad"])
        return df
    except:
        return pd.DataFrame(columns=["ID_Producto", "ID_Insumo", "Cantidad"])

# Cargamos todo al inicio
df_insumos = cargar_insumos()
df_productos = cargar_productos()
df_recetas = cargar_recetas()

# --- 4. INTERFAZ CON PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["📦 Almacén (Insumos)", "👕 Mis Productos", "📝 Recetas (Costos)"])

# ==========================================
# PESTAÑA 1: ALMACÉN DE INSUMOS (Lo del Lunes mejorado)
# ==========================================
with tab1:
    st.header("Inventario de Materia Prima")
    st.dataframe(df_insumos, width='stretch')
    
    with st.expander("➕ Agregar Nuevo Insumo"):
        with st.form("form_insumo"):
            c1, c2, c3 = st.columns(3)
            nuevo_id = c1.text_input("ID Insumo", placeholder="Ej: B-CHICO")
            nuevo_nom = c2.text_input("Nombre")
            nuevo_costo = c3.number_input("Costo Unitario (Bs)", min_value=0.0, format="%.2f")
            
            c4, c5, c6 = st.columns(3)
            nueva_cat = c4.selectbox("Categoría", ["Tela", "Forro", "Avíos", "Hilos", "Servicio"])
            nuevo_stock = c5.number_input("Stock Inicial", min_value=0.0)
            nueva_unidad = c6.text_input("Unidad", value="Unidades")
            
            if st.form_submit_button("Guardar Insumo"):
                nuevo_dato = pd.DataFrame([{
                    "ID": nuevo_id, "Nombre": nuevo_nom, "Categoria": nueva_cat,
                    "Stock_Actual": nuevo_stock, "Unidad": nueva_unidad, 
                    "Stock_Minimo": 5, "Costo_Promedio": nuevo_costo
                }])
                df_updated = pd.concat([df_insumos, nuevo_dato], ignore_index=True)
                conn.update(spreadsheet=url_sheet, worksheet="Insumos", data=df_updated)
                st.success("Guardado!")
                time.sleep(1)
                st.rerun()

# ==========================================
# PESTAÑA 2: PRODUCTOS (Sacos, etc.)
# ==========================================
with tab2:
    st.header("Catálogo de Productos")
    st.dataframe(df_productos, width='stretch')
    
    with st.expander("➕ Crear Nuevo Modelo de Saco"):
        with st.form("form_producto"):
            col_a, col_b = st.columns(2)
            prod_id = col_a.text_input("ID Producto", placeholder="Ej: SACO-H-L")
            prod_nom = col_b.text_input("Nombre del Modelo", placeholder="Ej: Saco Varón Talla L")
            prod_precio = st.number_input("Precio de Venta (Bs)", min_value=0.0)
            
            if st.form_submit_button("Crear Producto"):
                nuevo_prod = pd.DataFrame([{
                    "ID": prod_id, "Nombre": prod_nom, 
                    "Precio_Venta": prod_precio, "Stock_Terminado": 0
                }])
                
                if df_productos.empty:
                    df_upd = nuevo_prod
                else:
                    df_upd = pd.concat([df_productos, nuevo_prod], ignore_index=True)
                
                conn.update(spreadsheet=url_sheet, worksheet="Productos", data=df_upd)
                st.success("Producto Creado!")
                time.sleep(1)
                st.rerun()

# ==========================================
# PESTAÑA 3: RECETAS (El Cerebro)
# ==========================================
with tab3:
    st.header("👨‍🍳 Definir Receta (Ficha Técnica)")
    st.info("Aquí le decimos al sistema: 'Un Saco Varón lleva 1.6m de Tela, 6 Botones chicos, etc.'")
    
    col_izq, col_der = st.columns([1, 2])
    
    with col_izq:
        st.subheader("Agregar Ingrediente")
        
        # Selectores inteligentes
        lista_productos = df_productos["ID"].tolist() if not df_productos.empty else []
        lista_insumos = df_insumos["ID"].tolist() + [" - "]
        
        # Formulario de receta
        with st.form("form_receta"):
            prod_seleccionado = st.selectbox("Selecciona el Producto", lista_productos)
            
            # Buscamos el nombre del insumo para que sea fácil elegir
            diccionario_insumos = dict(zip(df_insumos["Nombre"], df_insumos["ID"]))
            nombre_insumo = st.selectbox("Selecciona Material", list(diccionario_insumos.keys()))
            id_insumo_seleccionado = diccionario_insumos[nombre_insumo]
            
            cantidad = st.number_input("Cantidad Necesaria", min_value=0.01, step=0.01)
            
            if st.form_submit_button("🔗 Vincular Material"):
                nueva_relacion = pd.DataFrame([{
                    "ID_Producto": prod_seleccionado,
                    "ID_Insumo": id_insumo_seleccionado,
                    "Cantidad": cantidad
                }])
                
                if df_recetas.empty:
                    df_r_upd = nueva_relacion
                else:
                    df_r_upd = pd.concat([df_recetas, nueva_relacion], ignore_index=True)
                    
                conn.update(spreadsheet=url_sheet, worksheet="Recetas", data=df_r_upd)
                st.toast(f"Agregado: {cantidad} de {nombre_insumo} a {prod_seleccionado}")
                time.sleep(1)
                st.rerun()

    with col_der:
        st.subheader("📋 Recetas Actuales")
        # Mostramos la tabla uniendo datos para que se entienda (Merge)
        if not df_recetas.empty and not df_insumos.empty:
            # Unimos Receta con Insumos para ver nombres y costos
            receta_detalle = pd.merge(df_recetas, df_insumos[['ID', 'Nombre', 'Unidad', 'Costo_Promedio']], 
                                     left_on='ID_Insumo', right_on='ID', how='left')
            
            # Calculamos costo parcial
            receta_detalle['Costo_Insumo'] = receta_detalle['Cantidad'] * receta_detalle['Costo_Promedio']
            
            # Mostramos tabla limpia
            st.dataframe(receta_detalle[['ID_Producto', 'Nombre', 'Cantidad', 'Unidad', 'Costo_Insumo']], width='stretch')
            
            # COSTO TOTAL POR PRODUCTO
            st.divider()
            st.subheader("💰 Costo Total Teórico")
            costos_totales = receta_detalle.groupby("ID_Producto")['Costo_Insumo'].sum().reset_index()
            st.dataframe(costos_totales)
        else:
            st.warning("No hay recetas definidas aún.")