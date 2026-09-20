# app.py - Frontend del Gemelo Digital de Pricing Solufar

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Importación del backend matemático
from creador_precios import ejecutar_gemelo_digital

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y CACHÉ
# ==============================================================================
st.set_page_config(
    page_title="Gemelo Digital de Pricing - Solufar",
    page_icon="💊",
    layout="wide"
)

# Cacheamos la función para que no recargue GSheets con cada click
@st.cache_data(ttl=3600)
def obtener_datos():
    return ejecutar_gemelo_digital()

try:
    df_trazabilidad = obtener_datos()
except Exception as e:
    st.error(f"🚨 Error de conexión o procesamiento de datos: {e}")
    st.stop()

# ==============================================================================
# 2. FUNCIONES DE GRAFICADO Y FORMATO
# ==============================================================================
def generar_explicacion(row):
    if row.get('Driver_Precio') == 'MANDATO_HUMANO':
        return (f"🛑 <b>Capa 0: Mandato Humano</b><br>"
                f"El administrador fijó el precio a ${row['Precio_Unitario']:,.0f}.<br>"
                f"El algoritmo aprende y sube el piso de margen al {row.get('Margen_Humano_Historico',0)*100:.1f}%.")

    texto = f"⚙️ <b>Algoritmo Estratégico Activo</b><br>"
    texto += f"Costo Odoo: ${row['Costo_Unitario']:,.0f} | Piso Margen: {row.get('Margen_Objetivo_Activo',0)*100:.1f}%<br>"

    if row.get('Flag_Quiebre_Probable', False):
        texto += "📦 <b>Capa 5:</b> Quiebre de stock detectado. No castiga el precio.<br>"
    elif row.get('Multiplicador_Demanda', 1.0) < 1.0:
        texto += f"📉 <b>Capa 5:</b> Caída de demanda. Ajuste a {row['Multiplicador_Demanda']:.2f}x.<br>"
    elif row.get('Multiplicador_Demanda', 1.0) > 1.0:
        texto += f"📈 <b>Capa 5:</b> Aceleración de demanda. Premio a {row['Multiplicador_Demanda']:.2f}x.<br>"

    if np.isclose(row.get('Precio_Capa6_Estrategico', 0), row.get('Piso_Seguridad_C6', 0)):
        texto += "🛡️ <b>Capa 6:</b> Blindaje de Margen activo. Evita vender bajo costo.<br>"
    else:
        texto += "📊 <b>Capa 2/3:</b> Precio guiado por costos e inflación macroeconómica.<br>"

    return texto

def crear_grafico_auditoria(df_trazabilidad, sku_nombre):
    df_explicativo = df_trazabilidad[df_trazabilidad['Nombre_Producto'] == sku_nombre].copy()
    df_explicativo = df_explicativo.dropna(subset=['Precio_Solufar_Emitido', 'Costo_Unitario'])
    df_explicativo['Mes_Str'] = df_explicativo['Mes_Ano'].dt.strftime('%Y-%m')
    df_explicativo['Explicacion_Dinamica'] = df_explicativo.apply(generar_explicacion, axis=1)

    colores_marcadores = np.where(df_explicativo.get('Driver_Precio', '') == 'MANDATO_HUMANO', '#E74C3C', '#2E86C1')

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df_explicativo['Mes_Str'], y=df_explicativo['Ctdad_Ordenada'], name="Ventas (Cajas)", marker_color='lightblue', opacity=0.4), secondary_y=True)
    fig.add_trace(go.Scatter(x=df_explicativo['Mes_Str'], y=df_explicativo['Precio_Solufar_Emitido'], mode='lines+markers', name='Precio Final Emitido', line=dict(color='#2E86C1', width=3), marker=dict(size=12, color=colores_marcadores, line=dict(width=2, color='white')), customdata=df_explicativo['Explicacion_Dinamica'], hovertemplate="%{customdata}<br><br><b>Precio Final:</b> $%{y:,.0f}<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_explicativo['Mes_Str'], y=df_explicativo['Precio_Unitario'], name="Precio Inercial (Cobrado)", line=dict(color='gray', width=2, dash='dash')), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_explicativo['Mes_Str'], y=df_explicativo['Costo_Unitario'], mode='lines', name='Costo Adquisición', line=dict(color='gray', width=4, dash='dot'), hovertemplate="Costo: $%{y:,.0f}<extra></extra>"), secondary_y=False)

    fig.update_layout(
        title=f"<b>Auditoría Algorítmica: {sku_nombre}</b>", 
        hovermode="x unified", 
        plot_bgcolor="white", 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=550
    )
    fig.update_yaxes(title_text="<b>Precio ($ CLP)</b>", tickformat="$,.0f", secondary_y=False, gridcolor='lightgray')
    fig.update_yaxes(title_text="<b>Volumen (Cajas)</b>", secondary_y=True, showgrid=False)
    fig.update_xaxes(title_text="<b>Mes</b>", tickangle=-45)

    return fig

# ==============================================================================
# 3. BARRA DE NAVEGACIÓN LATERAL
# ==============================================================================
st.sidebar.image("https://img.icons8.com/color/96/000000/pills.png", width=60)
st.sidebar.title("Solufar Pricing Engine")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegación",
    ("📊 Resumen Ejecutivo Global", "🔍 Auditoría Detallada por SKU")
)

# ==============================================================================
# 4. PÁGINA 1: RESUMEN EJECUTIVO GLOBAL
# ==============================================================================
if menu == "📊 Resumen Ejecutivo Global":
    st.title("💊 Gemelo Digital de Pricing: Motor Solufar")
    st.header("📊 Diagnóstico Ejecutivo")
    st.markdown("Radiografía financiera de la cartera evaluada demostrando el impacto del algoritmo predictivo frente a la inercia comercial.")
    
    # Pre-cálculos para KPIs
    df_calc = df_trazabilidad.dropna(subset=['Mes_Ano', 'Ctdad_Ordenada', 'Precio_Unitario', 'Costo_Unitario', 'Precio_Solufar_Emitido']).copy()
    
    ingresos_reales = (df_calc['Precio_Unitario'] * df_calc['Ctdad_Ordenada']).sum()
    ingresos_solufar = (df_calc['Precio_Solufar_Emitido'] * df_calc['Ctdad_Ordenada']).sum()
    df_calc['Brecha'] = (df_calc['Precio_Solufar_Emitido'] - df_calc['Precio_Unitario']).clip(lower=0)
    df_calc['Fuga_Valor'] = df_calc['Brecha'] * df_calc['Ctdad_Ordenada']
    fuga_total = df_calc['Fuga_Valor'].sum()
    upside_pct = ((ingresos_solufar - ingresos_reales) / ingresos_reales) * 100 if ingresos_reales > 0 else 0.0

    cantidad_skus = df_calc['Nombre_Producto'].nunique()
    total_cajas = df_calc['Ctdad_Ordenada'].sum()
    meses_totales = df_calc['Mes_Ano'].nunique()
    
    costo_total_vendido = (df_calc['Costo_Unitario'] * df_calc['Ctdad_Ordenada']).sum()
    margen_real_pct = ((ingresos_reales - costo_total_vendido) / ingresos_reales) * 100 if ingresos_reales > 0 else 0
    margen_solufar_pct = ((ingresos_solufar - costo_total_vendido) / ingresos_solufar) * 100 if ingresos_solufar > 0 else 0

    df_calc = df_calc.sort_values(by=['Nombre_Producto', 'Mes_Ano'])
    df_calc['Cambio_Precio'] = df_calc.groupby('Nombre_Producto')['Precio_Unitario'].diff().fillna(1)
    meses_congelados_totales = (df_calc['Cambio_Precio'] == 0).sum()
    promedio_congelado_por_sku = meses_congelados_totales / cantidad_skus if cantidad_skus > 0 else 0

    # Fila 1: Impacto Financiero
    st.markdown("### 💰 Impacto Directo en Flujo de Caja")
    col1, col2, col3 = st.columns(3)
    col1.metric("Ingresos Históricos (Cobrados)", f"${ingresos_reales:,.0f}".replace(",", "."))
    col2.metric("Proyección Óptima (Solufar)", f"${ingresos_solufar:,.0f}".replace(",", "."), f"+{upside_pct:.1f}% Upside")
    col3.metric("Fuga de Margen Identificada", f"${fuga_total:,.0f}".replace(",", "."), delta="- Dinero dejado en la mesa", delta_color="inverse")

    st.markdown("---")

    # Fila 2: Alcance Operativo
    st.markdown("### ⚙️ Alcance del Estudio y Eficiencia")
    col4, col5, col6, col7 = st.columns(4)
    col4.metric("SKUs Analizados", cantidad_skus)
    col5.metric("Periodo Analizado", f"{meses_totales} Meses")
    col6.metric("Volumen Evaluado", f"{total_cajas:,.0f} Cajas")
    col7.metric("Inercia Promedio", f"{promedio_congelado_por_sku:.1f} Meses/SKU")

    # Fila 3: Eficiencia de Margen
    st.markdown("---")
    st.markdown("### 📈 Eficiencia Comercial Global (%)")
    col8, col9, col10 = st.columns(3)
    col8.metric("Margen Bruto Histórico", f"{margen_real_pct:.1f}%")
    col9.metric("Nuevo Margen Solufar", f"{margen_solufar_pct:.1f}%", f"+{(margen_solufar_pct - margen_real_pct):.1f} Puntos")

    # Fila 4: Desglose por SKU en Tabla Interactiva
    st.markdown("---")
    st.markdown("### 📋 Desglose de Impacto por Medicamento")
    resumen_sku = df_calc.groupby('Nombre_Producto').agg(
        Cajas_Vendidas=('Ctdad_Ordenada', 'sum'),
        Meses_Inercia=('Cambio_Precio', lambda x: (x == 0).sum()),
        Fuga_Recuperable_CLP=('Fuga_Valor', 'sum')
    ).reset_index().sort_values(by='Fuga_Recuperable_CLP', ascending=False)
    
    st.dataframe(
        resumen_sku.style.format({
            "Cajas_Vendidas": "{:,.0f}",
            "Fuga_Recuperable_CLP": "${:,.0f}"
        }).background_gradient(subset=['Fuga_Recuperable_CLP'], cmap='Reds'),
        use_container_width=True,
        hide_index=True
    )

# ==============================================================================
# 5. PÁGINA 2: AUDITORÍA DETALLADA POR SKU
# ==============================================================================
elif menu == "🔍 Auditoría Detallada por SKU":
    st.header("🔍 Auditoría Detallada del Motor de Precios")
    st.markdown("Revisa el comportamiento mes a mes de las 8 capas estratégicas del algoritmo para cada medicamento.")
    
    lista_productos = df_trazabilidad['Nombre_Producto'].dropna().unique().tolist()
    
    # Selector de Producto
    producto_sel = st.selectbox("Seleccione un Medicamento para Analizar:", lista_productos)
    
    # Generar y mostrar gráfico interactivo Plotly
    st.plotly_chart(crear_grafico_auditoria(df_trazabilidad, producto_sel), use_container_width=True)

    # Tabla de bitácora
    st.markdown("### 📝 Bitácora de Decisiones Algorítmicas")
    cols_mostrar = ['Mes_Ano', 'Costo_Unitario', 'Precio_Unitario', 'Precio_Solufar_Emitido', 'Margen_Pct_Final', 'Driver_Precio']
    df_filtrado = df_trazabilidad[df_trazabilidad['Nombre_Producto'] == producto_sel][cols_mostrar].dropna()
    
    # Convertir fecha a string limpio
    df_filtrado['Mes_Ano'] = df_filtrado['Mes_Ano'].dt.strftime('%Y-%m')
    
    st.dataframe(
        df_filtrado.style.format({
            "Costo_Unitario": "${:,.0f}",
            "Precio_Unitario": "${:,.0f}",
            "Precio_Solufar_Emitido": "${:,.0f}",
            "Margen_Pct_Final": "{:.1f}%"
        }),
        use_container_width=True,
        hide_index=True
    )
