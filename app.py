import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILO ---
st.set_page_config(page_title="Caserito Store", page_icon="✂️", layout="wide")

# --- 2. CONEXIÓN Y CARGA DE DATOS ---
url_sheet = "https://docs.google.com/spreadsheets/d/1MfLBejcF2aOLi6JeZgXij8p1rZ1EPZzsV9NGpNvsJC4/edit"
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_data(hoja, columnas_default):
    try:
        df = conn.read(spreadsheet=url_sheet, worksheet=hoja)
        if df.empty: return pd.DataFrame(columns=columnas_default)
        return df
    except: return pd.DataFrame(columns=columnas_default)

# Cargar todas las tablas
df_insumos = cargar_data("Insumos", ["ID", "Nombre", "Categoria", "Stock_Actual", "Unidad", "Stock_Minimo", "Costo_Promedio"])
df_productos = cargar_data("Productos", ["ID", "Nombre", "Precio_Venta", "Stock_Terminado"])
df_recetas = cargar_data("Recetas", ["ID_Producto", "ID_Insumo", "Cantidad"])
df_ventas = cargar_data("Ventas", ["Fecha", "ID_Producto", "Cantidad", "Total_Venta", "Ganancia"])

# Limpieza de datos (Asegurar que números sean números)
def limpiar_df(df, cols_num):
    if not df.empty:
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df_insumos = limpiar_df(df_insumos, ["Stock_Actual", "Costo_Promedio", "Stock_Minimo"])
df_productos = limpiar_df(df_productos, ["Precio_Venta", "Stock_Terminado"])
df_recetas = limpiar_df(df_recetas, ["Cantidad"])
df_ventas = limpiar_df(df_ventas, ["Total_Venta", "Ganancia", "Cantidad"])
if not df_ventas.empty: df_ventas["Fecha"] = pd.to_datetime(df_ventas["Fecha"], errors='coerce')

# --- 3. MENÚ LATERAL (SIDEBAR) ---
with st.sidebar:
    st.title("✂️ Caserito Store")
    st.divider()
    
    st.subheader("📍 Navegación")
    opcion = st.radio(
        "Ir a:",
        ["📊 Dashboard Principal", 
         "🏭 Registrar Producción", 
         "🛒 Registrar Venta", 
         "📦 Gestión de Almacén", 
         "👕 Gestión de Productos", 
         "📝 Gestión de Recetas"],
        index=0
    )
    
    st.divider()
    # Botón manual por si acaso
    if st.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

# --- 4. LÓGICA DE PÁGINAS ---

# ========================================================
# PÁGINA 1: DASHBOARD PRINCIPAL
# ========================================================
if opcion == "📊 Dashboard Principal":
    st.title("📊 Centro de Comando")
    
    # --- NIVEL 1: FINANZAS (KPIs) ---
    st.subheader("💰 Resumen Financiero")
    col1, col2, col3, col4 = st.columns(4)
    
    ingresos = df_ventas["Total_Venta"].sum() if not df_ventas.empty else 0
    ganancia = df_ventas["Ganancia"].sum() if not df_ventas.empty else 0
    prendas = df_ventas["Cantidad"].sum() if not df_ventas.empty else 0
    dinero_insumos = (df_insumos["Stock_Actual"] * df_insumos["Costo_Promedio"]).sum()
    
    col1.metric("Ingresos Totales", f"Bs {ingresos:,.2f}")
    col2.metric("Ganancia Neta", f"Bs {ganancia:,.2f}", delta="Beneficio")
    col3.metric("Prendas Vendidas", f"{int(prendas)}")
    col4.metric("Capital en Insumos", f"Bs {dinero_insumos:,.2f}", delta="Stock Valorado", delta_color="off")
    
    st.divider()

    # --- NIVEL 2: RENDIMIENTO DE VENTAS ---
    st.subheader("📈 Rendimiento de Ventas")
    
    if not df_ventas.empty:
        g1, g2 = st.columns(2)
        
        with g1:
            st.write("**Tendencia de Ventas (Por Día)**")
            ventas_dia = df_ventas.groupby(df_ventas["Fecha"].dt.date)["Total_Venta"].sum()
            st.bar_chart(ventas_dia, color="#4CAF50") # Verde
            
        with g2:
            st.write("**🏆 Top Productos Más Vendidos**")
            top_prod = df_ventas.groupby("ID_Producto")["Cantidad"].sum().sort_values(ascending=False).head(5)
            st.bar_chart(top_prod, horizontal=True, color="#FF9800") # Naranja
    else:
        st.info("Registra tu primera venta para ver los gráficos aquí.")

    st.divider()
    
    # --- NIVEL 3: SALUD DEL ALMACÉN ---
    st.subheader("📦 Salud del Inventario")
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        st.write("**⚠️ Alerta: Stock Crítico**")
        if not df_insumos.empty:
            criticos = df_insumos[df_insumos["Stock_Actual"] <= df_insumos["Stock_Minimo"]]
            if not criticos.empty:
                st.dataframe(criticos[["Nombre", "Stock_Actual", "Stock_Minimo"]], hide_index=True, use_container_width=True)
            else:
                st.success("✅ Todo el inventario está saludable.")
        else: st.info("Sin datos.")

    with col_der:
        st.write("**Insumos con Mayor Stock**")
        if not df_insumos.empty:
            top_stock = df_insumos.sort_values(by="Stock_Actual", ascending=False).head(5)
            st.bar_chart(top_stock.set_index("Nombre")["Stock_Actual"], color="#2196F3") # Azul
        else: st.info("Sin datos.")

# ========================================================
# PÁGINA 2: REGISTRAR PRODUCCIÓN (Con Autorefresco)
# ========================================================
elif opcion == "🏭 Registrar Producción":
    st.title("🏭 Fábrica: Registrar Confección")
    
    col_a, col_b = st.columns(2)
    pfab = col_a.selectbox("¿Qué se fabricó?", df_productos["ID"].unique() if not df_productos.empty else [])
    qfab = col_b.number_input("Cantidad Fabricada", min_value=1, step=1)
    
    if pfab:
        receta = df_recetas[df_recetas["ID_Producto"] == pfab]
        if receta.empty:
            st.warning("⚠️ No hay receta para este producto. Configúrala en 'Gestión de Recetas'.")
        else:
            val = pd.merge(receta, df_insumos, left_on="ID_Insumo", right_on="ID", suffixes=("_r", "_s"))
            val["Req"] = val["Cantidad"] * qfab
            val["Futuro"] = val["Stock_Actual"] - val["Req"]
            possible = val["Futuro"] >= 0
            
            st.write("Materiales a descontar:")
            st.dataframe(val[["Nombre", "Stock_Actual", "Req", "Futuro"]], hide_index=True)
            
            if possible.all():
                # --- BOTÓN DE PRODUCCIÓN ACTUALIZADO ---
                if st.button("🚀 Confirmar y Descontar Material", type="primary"):
                    # 1. Actualizar memoria local
                    for i, r in val.iterrows():
                        idx = df_insumos[df_insumos["ID"] == r["ID_Insumo"]].index[0]
                        df_insumos.at[idx, "Stock_Actual"] = r["Futuro"]
                    
                    idx_p = df_productos[df_productos["ID"] == pfab].index[0]
                    df_productos.at[idx_p, "Stock_Terminado"] += qfab
                    
                    # 2. Guardar en Google Sheets
                    conn.update(spreadsheet=url_sheet, worksheet="Insumos", data=df_insumos)
                    conn.update(spreadsheet=url_sheet, worksheet="Productos", data=df_productos)
                    
                    # 3. LIMPIAR CACHÉ Y RECARGAR
                    st.cache_data.clear()
                    st.success(f"✅ Se fabricaron {qfab} unidades de {pfab}. Stock actualizado.")
                    time.sleep(2)
                    st.rerun()
            else:
                st.error("🛑 Falta material. Revisa la tabla.")

# ========================================================
# PÁGINA 3: REGISTRAR VENTA (Con Autorefresco)
# ========================================================
elif opcion == "🛒 Registrar Venta":
    st.title("🛒 Caja: Registrar Venta")
    
    c1, c2, c3 = st.columns(3)
    pven = c1.selectbox("Producto", df_productos["ID"].unique() if not df_productos.empty else [])
    
    stock_disp = 0
    precio_base = 0
    if pven and not df_productos.empty:
        row = df_productos[df_productos["ID"]==pven].iloc[0]
        stock_disp = row["Stock_Terminado"]
        precio_base = row["Precio_Venta"]
        
    c1.caption(f"Stock Disponible: {stock_disp}")
    
    qven = c2.number_input("Cantidad", 1, max_value=int(stock_disp) if stock_disp > 0 else 1)
    total_calc = qven * precio_base
    total_final = c3.number_input("Total Venta (Bs)", value=float(total_calc))
    
    # --- BOTÓN DE VENTA ACTUALIZADO ---
    if st.button("💸 Cobrar y Registrar", type="primary"):
        if stock_disp < qven:
            st.error("❌ No hay stock suficiente.")
        else:
            # Calcular Costo y Ganancia
            receta = df_recetas[df_recetas["ID_Producto"] == pven]
            merge = pd.merge(receta, df_insumos, left_on="ID_Insumo", right_on="ID")
            costo_unit = (merge["Cantidad"] * merge["Costo_Promedio"]).sum() if not merge.empty else 0
            ganancia = total_final - (costo_unit * qven)
            
            # Crear registro de venta
            nueva = pd.DataFrame([{
                "Fecha": datetime.now().strftime("%Y-%m-%d"),
                "ID_Producto": pven, "Cantidad": qven, 
                "Total_Venta": total_final, "Ganancia": ganancia
            }])
            
            # Descontar del producto
            idx = df_productos[df_productos["ID"]==pven].index[0]
            df_productos.at[idx, "Stock_Terminado"] -= qven
            
            # Guardar todo
            conn.update(spreadsheet=url_sheet, worksheet="Ventas", data=pd.concat([df_ventas, nueva], ignore_index=True))
            conn.update(spreadsheet=url_sheet, worksheet="Productos", data=df_productos)
            
            # LIMPIAR CACHÉ Y RECARGAR
            st.cache_data.clear()
            st.balloons()
            st.success(f"✅ Venta registrada. Ganancia: {ganancia} Bs")
            time.sleep(2)
            st.rerun()

# ========================================================
# PÁGINAS DE GESTIÓN (ADMIN - Con Autorefresco)
# ========================================================
elif opcion == "📦 Gestión de Almacén":
    st.header("📦 Inventario de Insumos")
    st.dataframe(df_insumos, use_container_width=True)
    
    with st.expander("➕ Agregar Nuevo Insumo / Compra"):
        with st.form("add_ins"):
            i_id = st.text_input("ID")
            i_nom = st.text_input("Nombre")
            i_st = st.number_input("Stock Inicial", min_value=0.0)
            i_cos = st.number_input("Costo Unitario", min_value=0.0)
            i_min = st.number_input("Stock Mínimo Aviso", value=5.0)
            i_cat = st.selectbox("Categoría", ["Tela", "Avíos", "Hilos", "Otros"])
            
            # --- BOTÓN GUARDAR INSUMO ACTUALIZADO ---
            if st.form_submit_button("Guardar"):
                nd = pd.DataFrame([{"ID": i_id, "Nombre": i_nom, "Stock_Actual": i_st, "Costo_Promedio": i_cos, "Categoria": i_cat, "Unidad": "U", "Stock_Minimo": i_min}])
                conn.update(spreadsheet=url_sheet, worksheet="Insumos", data=pd.concat([df_insumos, nd], ignore_index=True))
                
                st.cache_data.clear()
                st.success("✅ Insumo guardado correctamente")
                time.sleep(1)
                st.rerun()

elif opcion == "👕 Gestión de Productos":
    st.header("👕 Catálogo de Productos")
    st.dataframe(df_productos, use_container_width=True)
    
    with st.expander("➕ Crear Nuevo Modelo"):
        with st.form("add_prod"):
            p_id = st.text_input("ID")
            p_nom = st.text_input("Nombre")
            p_pre = st.number_input("Precio Venta", min_value=0.0)
            
            # --- BOTÓN GUARDAR PRODUCTO ACTUALIZADO ---
            if st.form_submit_button("Guardar"):
                np = pd.DataFrame([{"ID": p_id, "Nombre": p_nom, "Precio_Venta": p_pre, "Stock_Terminado": 0}])
                conn.update(spreadsheet=url_sheet, worksheet="Productos", data=pd.concat([df_productos, np], ignore_index=True))
                
                st.cache_data.clear()
                st.success("✅ Producto creado correctamente")
                time.sleep(1)
                st.rerun()

elif opcion == "📝 Gestión de Recetas":
    st.header("📝 Fichas Técnicas (Recetas)")
    c1, c2 = st.columns(2)
    with c1:
        st.write("Vincular Insumo a Producto")
        with st.form("add_rec"):
            ps = st.selectbox("Producto", df_productos["ID"].unique() if not df_productos.empty else [])
            ins = st.selectbox("Insumo", df_insumos["ID"].unique() if not df_insumos.empty else [])
            cant = st.number_input("Cantidad usada", step=0.01)
            
            # --- BOTÓN GUARDAR RECETA ACTUALIZADO ---
            if st.form_submit_button("Guardar Relación"):
                nr = pd.DataFrame([{"ID_Producto": ps, "ID_Insumo": ins, "Cantidad": cant}])
                conn.update(spreadsheet=url_sheet, worksheet="Recetas", data=pd.concat([df_recetas, nr], ignore_index=True))
                
                st.cache_data.clear()
                st.success("✅ Receta actualizada correctamente")
                time.sleep(1)
                st.rerun()
    with c2:
        st.write("Recetas Actuales")
        st.dataframe(df_recetas, use_container_width=True)