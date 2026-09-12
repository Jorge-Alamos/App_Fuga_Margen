import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from creador_precios import ejecutar_gemelo_digital

st.set_page_config(page_title="Gemelo Digital de Pricing", page_icon="💊", layout="wide")
st.title("💊 Gemelo Digital de Pricing: Motor Solufar")
st.markdown("Plataforma interactiva de auditoría, orquestación de márgenes y recuperación de fuga.")

@st.cache_data
def obtener_datos():
    return ejecutar_gemelo_digital()

df_trazabilidad = obtener_datos()

st.sidebar.header("Filtros del Modelo")
sku_sel = st.sidebar.selectbox("Seleccionar SKU", ["Vannair Inhalador 160/4.5 x 120 Dosis"])

df_calc = df_trazabilidad.dropna(subset=['Precio_Solufar_Emitido', 'Precio_Unitario', 'Ctdad_Ordenada']).copy()
ingreso_real = (df_calc['Precio_Unitario'] * df_calc['Ctdad_Ordenada']).sum()
ingreso_solufar = (df_calc['Precio_Solufar_Emitido'] * df_calc['Ctdad_Ordenada']).sum()
fuga_total = ((df_calc['Precio_Solufar_Emitido'] - df_calc['Precio_Unitario']).clip(lower=0) * df_calc['Ctdad_Ordenada']).sum()
upside = (fuga_total / ingreso_real) * 100 if ingreso_real > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Ingresos Reales (Caja)", f"${ingreso_real:,.0f}".replace(",", "."))
col2.metric("Ingresos Proyectados", f"${ingreso_solufar:,.0f}".replace(",", "."))
col3.metric("Fuga de Margen", f"${fuga_total:,.0f}".replace(",", "."))
col4.metric("Upside Potencial", f"+{upside:.1f}%")

st.markdown("---")

def generar_explicacion(row):
    if row['Driver_Precio'] == 'MANDATO_HUMANO':
        return f"🛑 Capa 0: Mandato Humano. Precio fijado en mostrador: ${row['Precio_Unitario']:,.0f}."
    elif row['Driver_Precio'] == 'HIBRIDO_ORQUESTADO':
        return f"⚖️ Capa 7: Ensamble Ponderado ({int(row['Meses_Desde_Mandato'])} mes/es post-intervención)."
    else:
        return f"⚙️ Algoritmo Estratégico. Costo: ${row['Costo_Unitario']:,.0f} | Margen: {row.get('Margen_Objetivo_Activo', 0.25)*100:.1f}%."

df_trazabilidad['Explicacion_Dinamica'] = df_trazabilidad.apply(generar_explicacion, axis=1)
df_plot = df_trazabilidad.dropna(subset=['Precio_Unitario']).copy()
df_plot['Mes_Str'] = df_plot['Mes_Ano'].dt.strftime('%Y-%m')

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Bar(x=df_plot['Mes_Str'], y=df_plot['Ctdad_Ordenada'], name="Ventas", marker_color='lightblue', opacity=0.4), secondary_y=True)
fig.add_trace(go.Scatter(x=df_plot['Mes_Str'], y=df_plot['Costo_Unitario'], name="Costo Adquisición", line=dict(color='firebrick', width=2)), secondary_y=False)
fig.add_trace(go.Scatter(x=df_plot['Mes_Str'], y=df_plot['Precio_Unitario'], name="Precio Inercial", line=dict(color='gray', width=2, dash='dash')), secondary_y=False)

colores = df_plot['Driver_Precio'].map({'MANDATO_HUMANO': '#E74C3C', 'HIBRIDO_ORQUESTADO': '#F39C12', 'ALGORITMO_ESTRATEGICO': '#27AE60'})

fig.add_trace(go.Scatter(
    x=df_plot['Mes_Str'], y=df_plot['Precio_Solufar_Emitido'], name="Precio Solufar",
    line=dict(color='#2E86C1', width=3), marker=dict(size=10, color=colores),
    customdata=df_plot['Explicacion_Dinamica'], hovertemplate="%{customdata}<br><b>Precio Emitido:</b> $%{y:,.0f}<extra></extra>"
), secondary_y=False)

fig.update_layout(title="<b>Inercia vs Estrategia - Trazabilidad de Capas</b>", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("### 📋 Bitácora de Decisiones Algorítmicas")
df_tabla = df_trazabilidad[['Mes_Str', 'Costo_Unitario', 'Precio_Unitario', 'Precio_Solufar_Emitido', 'Margen_Pct_Final', 'Explicacion_Dinamica']].copy()
df_tabla['Explicacion_Dinamica'] = df_tabla['Explicacion_Dinamica'].str.replace('<b>', '').str.replace('</b>', '').str.replace('<br>', ' ➔ ')
df_tabla.columns = ['Mes', 'Costo Adquisición', 'Precio Inercial', 'Precio Estratégico', 'Margen (%)', 'Justificación']

st.dataframe(df_tabla, column_config={
    "Costo Adquisición": st.column_config.NumberColumn(format="$ %d"),
    "Precio Inercial": st.column_config.NumberColumn(format="$ %d"),
    "Precio Estratégico": st.column_config.NumberColumn(format="$ %d"),
    "Margen (%)": st.column_config.NumberColumn(format="%.1f %%"),
    "Justificación": st.column_config.TextColumn(width="large")
}, hide_index=True, use_container_width=True)

gobernanza = df_calc['Driver_Precio'].value_counts(normalize=True) * 100
margen_antes = df_calc[df_calc['Costo_Unitario'] <= 30000]['Margen_Pct_Final'].mean()
margen_despues = df_calc[df_calc['Costo_Unitario'] > 30000]['Margen_Pct_Final'].mean()

st.markdown(f"""
<div style="background: #f8f9f9; padding: 20px; border-left: 6px solid #2E86C1; margin-top: 20px;">
    <h3 style="color: #34495E; margin-top: 0;">📊 Reporte de Gobernanza y Márgenes</h3>
    <div style="display: flex; gap: 30px; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 280px;">
            <h4 style="color: #2980B9;">⚙️ Gobernanza del Pricing Engine</h4>
            <ul>
                <li><b>Mandato Humano:</b> {gobernanza.get('MANDATO_HUMANO', 0):.1f}%</li>
                <li><b>Híbrido Orquestado:</b> {gobernanza.get('HIBRIDO_ORQUESTADO', 0):.1f}%</li>
                <li><b>Algoritmo Estratégico:</b> {gobernanza.get('ALGORITMO_ESTRATEGICO', 0):.1f}%</li>
            </ul>
        </div>
        <div style="flex: 1; min-width: 280px;">
            <h4 style="color: #27AE60;">📊 Evolución del Margen Bruto</h4>
            <ul>
                <li><b>Antes del Shock de Costos:</b> {margen_antes:.2f}%</li>
                <li><b>Después del Shock de Costos:</b> {margen_despues:.2f}%</li>
            </ul>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
