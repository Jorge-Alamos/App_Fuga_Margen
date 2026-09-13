# app.py - Gemelo Digital de Pricing con Visualización de Capa 1 y Estrategia por Categoría

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Importación del backend modular
from creador_precios import ejecutar_gemelo_digital

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Gemelo Digital de Pricing - Solufar",
    page_icon="💊",
    layout="wide"
)

st.title("💊 Gemelo Digital de Pricing: Motor Solufar")
st.markdown("Plataforma interactiva de auditoría, orquestación de márgenes y recuperación de fuga.")

# ==============================================================================
# 2. CARGA Y PROCESAMIENTO DE DATOS
# ==============================================================================
@st.cache_data
def obtener_datos():
    return ejecutar_gemelo_digital()

df_trazabilidad = obtener_datos()

# Rescate de parámetros dinámicos de la Capa 1
categoria_activa = df_trazabilidad['Categoria_Producto'].iloc[0] if 'Categoria_Producto' in df_trazabilidad.columns else 'CRONICO_MARCA'
margen_politica_base = df_trazabilidad['Margen_Teorico_Base'].iloc[0] if 'Margen_Teorico_Base' in df_trazabilidad.columns else 0.25
umbral_shock_costo = df_trazabilidad['Umbral_Shock_Costo'].iloc[0] if 'Umbral_Shock_Costo' in df_trazabilidad.columns else 30000

# Generador de explicaciones dinámicas para tooltips y auditoría
def generar_explicacion(row):
    if row['Driver_Precio'] == 'MANDATO_HUMANO':
        return (f"🛑 <b>Capa 0: Mandato Humano</b><br>"
                f"El administrador fijó el precio a ${row['Precio_Unitario']:,.0f}.<br>"
                f"El algoritmo aprende y sube el piso de margen al {row.get('Margen_Humano_Historico', 0)*100:.1f}%.")
    
    texto = f"⚙️ <b>Algoritmo Estratégico Activo</b><br>"
    texto += f"Costo Odoo: ${row['Costo_Unitario']:,.0f} | Piso Margen: {row.get('Margen_Objetivo_Activo', 0.25)*100:.1f}%<br>"
    
    if row.get('Flag_Quiebre_Probable', False):
        texto += "📦 <b>Capa 5:</b> Quiebre de stock detectado. No se castiga el precio por baja venta.<br>"
    elif row.get('Multiplicador_Demanda', 1.0) < 1.0:
        texto += f"📉 <b>Capa 5:</b> Caída de demanda. Ajuste defensivo a {row['Multiplicador_Demanda']:.2f}x.<br>"
    elif row.get('Multiplicador_Demanda', 1.0) > 1.0:
        texto += f"📈 <b>Capa 5:</b> Aceleración de demanda. Premio a {row['Multiplicador_Demanda']:.2f}x.<br>"
    
    if np.isclose(row.get('Precio_Capa6_Estrategico', 0), row.get('Piso_Seguridad_C6', 0)):
        texto += "🛡️ <b>Capa 6:</b> Precio frenado por el 'Blindaje de Margen'. Evita vender bajo el piso de seguridad.<br>"
    else:
        texto += "📊 <b>Capa 3:</b> Precio guiado por indexación de inflación macroeconómica.<br>"
    
    return texto

df_trazabilidad['Explicacion_Dinamica'] = df_trazabilidad.apply(generar_explicacion, axis=1)
df_trazabilidad['Mes_Str'] = df_trazabilidad['Mes_Ano'].dt.strftime('%Y-%m')

# ==============================================================================
# 3. BARRA LATERAL (FILTROS Y AUDITORÍA DE CAPA 1)
# ==============================================================================
st.sidebar.header("Filtros del Modelo")
sku_sel = st.sidebar.selectbox("Seleccionar SKU", ["Vannair Inhalador 160/4.5 x 120 Dosis"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Parámetros de Capa 1")
st.sidebar.markdown(f"**Categoría:** `{categoria_activa}`")
st.sidebar.markdown(f"**Margen Base de Política:** `{margen_politica_base * 100:.1f}%`")
st.sidebar.markdown(f"**Umbral Quiebre de Costo:** `${umbral_shock_costo:,.0f}`")

# ==============================================================================
# 4. TARJETA VISUAL: ESTRATEGIA DE CATEGORÍA (CAPA 1)
# ==============================================================================
st.markdown(f"""
<div style="background-color: #EBF5FB; border-left: 6px solid #2E86C1; padding: 16px 20px; border-radius: 8px; margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>
            <span style="font-size: 0.85em; font-weight: bold; color: #2E86C1; text-transform: uppercase; letter-spacing: 1px;">🎯 Gobernanza Capa 1: Política por Categoría</span>
            <h3 style="margin: 4px 0 0 0; color: #1B4F72;">Familia: {categoria_activa.replace('_', ' ')}</h3>
        </div>
        <div style="display: flex; gap: 30px; align-items: center;">
            <div style="text-align: right;">
                <span style="font-size: 0.85em; color: #5D6D7E;">Margen Teórico Asignado</span><br>
                <b style="font-size: 1.4em; color: #27AE60;">{margen_politica_base * 100:.1f}%</b>
            </div>
            <div style="text-align: right; border-left: 2px solid #D4E6F1; padding-left: 20px;">
                <span style="font-size: 0.85em; color: #5D6D7E;">Umbral Tolerancia Shock</span><br>
                <b style="font-size: 1.4em; color: #A93226;">${umbral_shock_costo:,.0f}</b>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. TARJETAS KPI FINANCIERAS
# ==============================================================================
df_calc = df_trazabilidad.dropna(subset=['Precio_Solufar_Emitido', 'Precio_Unitario', 'Ctdad_Ordenada']).copy()
ingreso_real = (df_calc['Precio_Unitario'] * df_calc['Ctdad_Ordenada']).sum()
ingreso_solufar = (df_calc['Precio_Solufar_Emitido'] * df_calc['Ctdad_Ordenada']).sum()
fuga_total = ((df_calc['Precio_Solufar_Emitido'] - df_calc['Precio_Unitario']).clip(lower=0) * df_calc['Ctdad_Ordenada']).sum()
upside = (fuga_total / ingreso_real) * 100 if ingreso_real > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Ingresos Reales (Caja)", f"${ingreso_real:,.0f}".replace(",", "."))
col2.metric("Ingresos Proyectados Solufar", f"${ingreso_solufar:,.0f}".replace(",", "."))
col3.metric("Fuga de Margen Recuperable", f"${fuga_total:,.0f}".replace(",", "."))
col4.metric("Upside Potencial", f"+{upside:.1f}%")

st.markdown("---")

# ==============================================================================
# 6. GRÁFICO INTERACTIVO PLOTLY CON PUNTOS
# ==============================================================================
df_plot = df_trazabilidad.dropna(subset=['Precio_Unitario']).copy()

fig = make_subplots(specs=[[{"secondary_y": True}]])

fig.add_trace(go.Bar(
    x=df_plot['Mes_Str'], 
    y=df_plot['Ctdad_Ordenada'], 
    name="Ventas (Cajas)", 
    marker_color='lightblue', 
    opacity=0.4
), secondary_y=True)

fig.add_trace(go.Scatter(
    x=df_plot['Mes_Str'], 
    y=df_plot['Costo_Unitario'], 
    mode='lines+markers',
    name="Costo Adquisición", 
    line=dict(color='gray', width=2, dash='dot'),
    marker=dict(size=6, color='gray'),
    hovertemplate="Costo: $%{y:,.0f}<extra></extra>"
), secondary_y=False)

fig.add_trace(go.Scatter(
    x=df_plot['Mes_Str'], 
    y=df_plot['Precio_Unitario'], 
    mode='lines+markers',
    name="Precio Inercial (Cobrado)", 
    line=dict(color='gray', width=2, dash='dash'),
    marker=dict(size=6, color='gray'),
    hovertemplate="Precio Inercial: $%{y:,.0f}<extra></extra>"
), secondary_y=False)

colores_marcadores = np.where(df_plot['Driver_Precio'] == 'MANDATO_HUMANO', '#E74C3C', '#2E86C1')

fig.add_trace(go.Scatter(
    x=df_plot['Mes_Str'], 
    y=df_plot['Precio_Solufar_Emitido'], 
    mode='lines+markers',
    name="Precio Final Emitido",
    line=dict(color='#2E86C1', width=3),
    marker=dict(size=11, color=colores_marcadores, line=dict(width=2, color='white')),
    customdata=df_plot['Explicacion_Dinamica'],
    hovertemplate="%{customdata}<br><br><b>Precio Final:</b> $%{y:,.0f}<extra></extra>"
), secondary_y=False)

fig.update_layout(
    title="<b>Trazabilidad Algorítmica: ¿Por qué cambió el precio este mes?</b><br><sup>Puntos rojos: intervención manual. Puntos azules: algoritmo estratégico activo.</sup>",
    hovermode="x unified",
    plot_bgcolor="white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
fig.update_yaxes(title_text="<b>Precio ($ CLP)</b>", tickformat="$,.0f", secondary_y=False, gridcolor='lightgray')
fig.update_yaxes(title_text="<b>Volumen (Cajas)</b>", secondary_y=True, showgrid=False)
fig.update_xaxes(title_text="<b>Mes</b>", tickangle=-45)

st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# 7. BITÁCORA DE DECISIONES MENSUALES (TABLA HTML ESTILIZADA)
# ==============================================================================
df_resumen_textual = df_plot[['Mes_Ano', 'Precio_Unitario', 'Precio_Solufar_Emitido', 'Explicacion_Dinamica']].copy()
df_resumen_textual['Mes'] = df_resumen_textual['Mes_Ano'].dt.strftime('%Y-%m')
df_resumen_textual['Precio Inercial'] = df_resumen_textual['Precio_Unitario'].apply(lambda x: f"${x:,.0f}")
df_resumen_textual['Precio Estratégico'] = df_resumen_textual['Precio_Solufar_Emitido'].apply(lambda x: f"${x:,.0f}")
df_resumen_textual = df_resumen_textual[['Mes', 'Precio Inercial', 'Precio Estratégico', 'Explicacion_Dinamica']]
df_resumen_textual.rename(columns={'Explicacion_Dinamica': 'Justificación del Motor Algorítmico'}, inplace=True)

tabla_html = df_resumen_textual.to_html(escape=False, index=False, justify='left')

html_bitacora = f"""
<style>
    .custom-table-container {{
        background-color: #ffffff !important;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-top: 25px;
        margin-bottom: 25px;
        font-family: Arial, sans-serif;
    }}
    .custom-table-container h3 {{
        color: #34495E !important; 
        border-bottom: 2px solid #ECF0F1; 
        padding-bottom: 10px; 
        margin-top: 0;
    }}
    .custom-table-container table {{
        width: 100%;
        border-collapse: collapse;
    }}
    .custom-table-container th {{
        background-color: #2E86C1 !important;
        color: #ffffff !important;
        text-align: left;
        padding: 12px;
        font-weight: bold;
    }}
    .custom-table-container td {{
        padding: 12px;
        vertical-align: top;
        border-bottom: 1px solid #dddddd;
        color: #212F3D !important;
    }}
    .custom-table-container tbody tr:nth-child(odd) {{
        background-color: #f8f9f9 !important;
    }}
    .custom-table-container tbody tr:nth-child(even) {{
        background-color: #ffffff !important;
    }}
    .custom-table-container tbody tr:hover td {{
        background-color: #ebf5fb !important;
    }}
</style>

<div class="custom-table-container">
    <h3>📋 Bitácora de Decisiones Mensuales</h3>
    {tabla_html}
</div>
"""

st.markdown(html_bitacora, unsafe_allow_html=True)

# ==============================================================================
# 8. REPORTE DE GOBERNANZA Y MÁRGENES
# ==============================================================================
total_meses = df_calc['Mes_Ano'].nunique()
gobernanza_counts = df_calc.groupby('Driver_Precio')['Mes_Ano'].nunique().reindex([
    'MANDATO_HUMANO', 'HIBRIDO_ORQUESTADO', 'ALGORITMO_ESTRATEGICO'
], fill_value=0)
gobernanza_pct = (gobernanza_counts / total_meses * 100).fillna(0)

df_before_shock = df_calc[df_calc['Costo_Unitario'] <= umbral_shock_costo]
df_after_shock = df_calc[df_calc['Costo_Unitario'] > umbral_shock_costo]
margen_antes = df_before_shock['Margen_Pct_Final'].mean()
margen_despues = df_after_shock['Margen_Pct_Final'].mean()

html_resumen = f"""
<div style="font-family: Arial, sans-serif; background: #ffffff; padding: 20px; border-radius: 10px; border-left: 6px solid #2E86C1; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 30px;">
    <h3 style="color: #34495E; margin-top: 0;">📊 Reporte de Gobernanza y Márgenes</h3>
    <div style="display: flex; gap: 30px; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 280px;">
            <h4 style="color: #2980B9;">⚙️ Gobernanza del Pricing Engine</h4>
            <ul style="line-height: 1.6; color: #555;">
                <li><b>Mandato Humano:</b> {int(gobernanza_counts['MANDATO_HUMANO'])} meses ({gobernanza_pct['MANDATO_HUMANO']:.1f}%)</li>
                <li><b>Híbrido Orquestado:</b> {int(gobernanza_counts['HIBRIDO_ORQUESTADO'])} meses ({gobernanza_pct['HIBRIDO_ORQUESTADO']:.1f}%)</li>
                <li><b>Algoritmo Estratégico:</b> {int(gobernanza_counts['ALGORITMO_ESTRATEGICO'])} meses ({gobernanza_pct['ALGORITMO_ESTRATEGICO']:.1f}%)</li>
            </ul>
        </div>
        <div style="flex: 1; min-width: 280px;">
            <h4 style="color: #27AE60;">📊 Evolución del Margen Bruto</h4>
            <ul style="line-height: 1.6; color: #555;">
                <li><b>Antes del Shock de Costos (≤ ${umbral_shock_costo:,.0f}):</b> {margen_antes:.2f}%</li>
                <li><b>Después del Shock de Costos (> ${umbral_shock_costo:,.0f}):</b> {margen_despues:.2f}%</li>
            </ul>
        </div>
    </div>
</div>
"""
st.markdown(html_resumen, unsafe_allow_html=True)
