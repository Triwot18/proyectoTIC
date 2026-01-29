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

# --- 2. CONEXIÓN ---
url_sheet = "https://docs.google.com/spreadsheets/d/1MfLBejcF2aOLi6JeZgXij8p1rZ1EPZzsV9NGpNvsJC4/edit"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. FUNCIONES DE CARGA (Para que sea rápido) ---
def cargar_data(hoja, columnas_default):
    try:
        df = conn.read(spreadsheet=url_sheet, worksheet=hoja)
        if df.empty:
            return pd.DataFrame(columns=columnas_default)
        # Aseguramos que las columnas numéricas sean números y no texto
        return df
    except:
        return pd.DataFrame(columns=columnas_default)

# Cargamos los 3 cerebros
df_insumos = cargar_data("Insumos", ["ID", "Nombre", "Categoria", "Stock_Actual", "Unidad", "Stock_Minimo", "Costo_Promedio"])
df_productos = cargar_data("Productos", ["ID", "Nombre", "Precio_Venta", "Stock_Terminado"])
df_recetas = cargar_data("Recetas", ["ID_Producto", "ID_Insumo", "Cantidad"])

# Convertir columnas numéricas a float/int para evitar errores de cálculo
if not df_insumos.empty:
    df_insumos["Stock_Actual"] = pd.to_numeric(df_insumos["Stock_Actual"], errors='coerce').fillna(0)
    df_insumos["Costo_Promedio"] = pd.to_numeric(df_insumos["Costo_Promedio"], errors='coerce').fillna(0)

if not df_recetas.empty:
    df_recetas["Cantidad"] = pd.to_numeric(df_recetas["Cantidad"], errors='coerce').fillna(0)

if not df_productos.empty:
    df_productos["Stock_Terminado"] = pd.to_numeric(df_productos["Stock_Terminado"], errors='coerce').fillna(0)


# --- 4. INTERFAZ ---
tab1, tab2, tab3, tab4 = st.tabs(["📦 Almacén", "👕 Productos", "📝 Recetas", "🏭 PRODUCIR (Automático)"])

# ==========================================
# PESTAÑA 1: ALMACÉN (INSUMOS)
# ==========================================
with tab1:
    st.header("Inventario de Materia Prima")
    
    # Alerta visual de stock bajo
    if not df_insumos.empty:
        stock_bajo = df_insumos[df_insumos["Stock_Actual"] <= df_insumos["Stock_Minimo"]]
        if not stock_bajo.empty:
            st.error(f"⚠️ ¡ATENCIÓN! Tienes {len(stock_bajo)} materiales con stock bajo.")
            st.dataframe(stock_bajo[["Nombre", "Stock_Actual", "Stock_Minimo"]], hide_index=True)

    st.dataframe(df_insumos, width='stretch')
    
    with st.expander("➕ Agregar Compra de Material"):
        with st.form("form_insumo"):
            c1, c2, c3 = st.columns(3)
            nuevo_id = c1.text_input("ID Insumo", placeholder="Ej: T-001")
            nuevo_nom = c2.text_input("Nombre")
            nuevo_costo = c3.number_input("Costo Unitario", min_value=0.0)
            c4, c5 = st.columns(2)
            nuevo_stock = c4.number_input("Cantidad", min_value=0.0)
            nueva_cat = c5.selectbox("Categoría", ["Tela", "Forro", "Avíos", "Hilos", "Servicio"])
            
            if st.form_submit_button("Guardar"):
                if nuevo_id in df_insumos["ID"].values:
                     st.warning("Ese ID ya existe. Usa otro.")
                else:
                    nuevo_dato = pd.DataFrame([{
                        "ID": nuevo_id, "Nombre": nuevo_nom, "Categoria": nueva_cat,
                        "Stock_Actual": nuevo_stock, "Unidad": "Unidad", 
                        "Stock_Minimo": 5, "Costo_Promedio": nuevo_costo
                    }])
                    df_upd = pd.concat([df_insumos, nuevo_dato], ignore_index=True)
                    conn.update(spreadsheet=url_sheet, worksheet="Insumos", data=df_upd)
                    st.success("Guardado!")
                    time.sleep(1)
                    st.rerun()

# ==========================================
# PESTAÑA 2: PRODUCTOS
# ==========================================
with tab2:
    st.header("Mis Productos (Sacos)")
    st.dataframe(df_productos, width='stretch')
    
    with st.expander("➕ Nuevo Modelo"):
        with st.form("form_prod"):
            pid = st.text_input("ID Producto", placeholder="Ej: SACO-H")
            pnom = st.text_input("Nombre")
            pprecio = st.number_input("Precio Venta", min_value=0.0)
            if st.form_submit_button("Crear"):
                nuevo = pd.DataFrame([{"ID": pid, "Nombre": pnom, "Precio_Venta": pprecio, "Stock_Terminado": 0}])
                conn.update(spreadsheet=url_sheet, worksheet="Productos", data=pd.concat([df_productos, nuevo], ignore_index=True))
                st.rerun()

# ==========================================
# PESTAÑA 3: RECETAS
# ==========================================
with tab3:
    st.header("Fichas Técnicas (Recetas)")
    c_izq, c_der = st.columns([1, 2])
    with c_izq:
        with st.form("form_receta"):
            st.subheader("Vincular Materiales")
            prod_sel = st.selectbox("Producto", df_productos["ID"].unique() if not df_productos.empty else [])
            
            # Crear diccionario Nombre -> ID
            mapa_insumos = dict(zip(df_insumos["Nombre"], df_insumos["ID"])) if not df_insumos.empty else {}
            insumo_nom = st.selectbox("Material", list(mapa_insumos.keys()))
            
            cant = st.number_input("Cantidad usada por unidad", min_value=0.01, step=0.01)
            
            if st.form_submit_button("Agregar a Receta"):
                id_ins = mapa_insumos[insumo_nom]
                nueva_receta = pd.DataFrame([{"ID_Producto": prod_sel, "ID_Insumo": id_ins, "Cantidad": cant}])
                conn.update(spreadsheet=url_sheet, worksheet="Recetas", data=pd.concat([df_recetas, nueva_receta], ignore_index=True))
                st.rerun()
                
    with c_der:
        if not df_recetas.empty:
            # Mostrar receta con nombres legibles
            vista = pd.merge(df_recetas, df_insumos[["ID", "Nombre"]], left_on="ID_Insumo", right_on="ID")
            st.dataframe(vista[["ID_Producto", "Nombre", "Cantidad"]], width='stretch')

# ==========================================
# PESTAÑA 4: PRODUCCIÓN (AUTOMATIZACIÓN)
# ==========================================
with tab4:
    st.header("🏭 Registrar Producción")
    st.info("Al registrar, se descontarán automáticamente los materiales y aumentará el stock de sacos.")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        prod_a_fabricar = st.selectbox("¿Qué se fabricó?", df_productos["ID"].unique() if not df_productos.empty else [])
        cantidad_a_fabricar = st.number_input("Cantidad Fabricada", min_value=1, step=1, value=1)
    
    # 1. CALCULAR REQUERIMIENTOS
    if prod_a_fabricar:
        # Filtrar la receta de este producto
        receta_filtro = df_recetas[df_recetas["ID_Producto"] == prod_a_fabricar]
        
        if receta_filtro.empty:
            st.warning("⚠️ Este producto NO tiene receta definida. No se descontará nada.")
        else:
            st.subheader("📋 Materiales a Descontar:")
            
            # Unir con stock actual para validar
            validacion = pd.merge(receta_filtro, df_insumos, left_on="ID_Insumo", right_on="ID", suffixes=("_receta", "_stock"))
            validacion["Consumo_Total"] = validacion["Cantidad"] * cantidad_a_fabricar
            validacion["Stock_Futuro"] = validacion["Stock_Actual"] - validacion["Consumo_Total"]
            validacion["Es_Posible"] = validacion["Stock_Futuro"] >= 0
            
            # Mostrar tabla de validación bonita
            st.dataframe(validacion[["Nombre", "Stock_Actual", "Consumo_Total", "Stock_Futuro", "Es_Posible"]], hide_index=True)
            
            # Verificar si alcanza todo
            falta_material = not validacion["Es_Posible"].all()
            
            if falta_material:
                st.error("🛑 NO HAY SUFICIENTE STOCK DE MATERIALES. Compra más antes de registrar.")
            else:
                st.success("✅ Stock suficiente. Listo para fabricar.")
                
                # BOTÓN FINAL DE EJECUCIÓN
                if st.button("🚀 CONFIRMAR CONFECCIÓN", type="primary"):
                    try:
                        # 1. Descontar Insumos
                        for index, row in validacion.iterrows():
                            # Buscamos el índice en el DF original de insumos
                            idx_insumo = df_insumos[df_insumos["ID"] == row["ID_Insumo"]].index[0]
                            df_insumos.at[idx_insumo, "Stock_Actual"] = row["Stock_Futuro"]
                        
                        # 2. Aumentar Stock de Producto Terminado
                        idx_prod = df_productos[df_productos["ID"] == prod_a_fabricar].index[0]
                        stock_viejo = df_productos.at[idx_prod, "Stock_Terminado"]
                        df_productos.at[idx_prod, "Stock_Terminado"] = stock_viejo + cantidad_a_fabricar
                        
                        # 3. Guardar en Google Sheets (ACTUALIZACIÓN MASIVA)
                        conn.update(spreadsheet=url_sheet, worksheet="Insumos", data=df_insumos)
                        conn.update(spreadsheet=url_sheet, worksheet="Productos", data=df_productos)
                        
                        st.balloons()
                        st.success(f"¡Éxito! Se fabricaron {cantidad_a_fabricar} unidades de {prod_a_fabricar}.")
                        time.sleep(2)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")