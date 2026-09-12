# app.py - Archivo único unificado para Streamlit Cloud

import streamlit as st
import pandas as pd
import numpy as np
import functools
from io import StringIO
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==============================================================================
# CONFIGURACIÓN DE LA PÁGINA WEB
# ==============================================================================
st.set_page_config(
    page_title="Gemelo Digital de Pricing - Solufar",
    page_icon="💊",
    layout="wide"
)

st.title("💊 Gemelo Digital de Pricing: Motor Solufar")
st.markdown("Plataforma interactiva de auditoría, orquestación de márgenes y recuperación de fuga.")

# ==============================================================================
# 1. CARGA Y LIMPIEZA DE DATOS (Código Base)
# ==============================================================================
data_ventas = """Mes / Año\tTotal\tCtdad Ordenada\tBase imponible\tMargen\t% Margen\tPrecio_unitario\tCosto_unitario
noviembre 2023\t$55,920\t2\t$46,992\t$21,145\t45.0%\t27960\t15379
diciembre 2023\t$139,800\t5\t$117,480\t$52,440\t44.6%\t27960\t15480
enero 2024\t$139,800\t5\t$117,480\t$52,440\t44.6%\t27960\t15480
febrero 2024\t$195,720\t7\t$164,472\t$73,416\t44.6%\t27960\t15480
marzo 2024\t$111,840\t4\t$93,984\t$43,974\t46.8%\t27960\t14878
abril 2024\t$307,560\t11\t$258,455\t$126,488\t48.9%\t27960\t14276
mayo 2024\t$195,720\t7\t$164,472\t$78,113\t47.5%\t27960\t14681
junio 2024\t$279,600\t10\t$234,960\t$108,793\t46.3%\t27960\t15014
julio 2024\t$291,540\t10\t$244,992\t$119,308\t48.7%\t29154\t14956
agosto 2024\t$389,350\t13\t$327,184\t$164,333\t50.2%\t29950\t14907
septiembre 2024\t$119,800\t4\t$100,672\t$46,349\t46.0%\t29950\t16161
octubre 2024\t$449,250\t15\t$377,520\t$158,010\t41.9%\t29950\t17414
noviembre 2024\t$239,600\t8\t$201,344\t$84,272\t41.9%\t29950\t17414
diciembre 2024\t$239,600\t8\t$201,344\t$84,272\t41.9%\t29950\t17414
enero 2025\t$89,850\t3\t$75,504\t$31,602\t41.9%\t29950\t17414
febrero 2025\t$29,950\t1\t$25,168\t$10,534\t41.9%\t29950\t17414
marzo 2025\t$29,950\t1\t$25,168\t$10,534\t41.9%\t29950\t17414
abril 2025\t\t\t\t\t#DIV/0!\t#DIV/0!
mayo 2025\t$149,750\t5\t$125,840\t$52,670\t41.9%\t29950\t17414
junio 2025\t$269,550\t9\t$226,512\t$94,806\t41.9%\t29950\t17414
julio 2025\t$179,700\t6\t$151,008\t$63,204\t41.9%\t29950\t17414
agosto 2025\t$89,850\t3\t$75,504\t$31,602\t41.9%\t29950\t17414
septiembre 2025\t$209,650\t7\t$176,176\t$73,738\t41.9%\t29950\t17414
octubre 2025\t$149,750\t5\t$125,840\t$52,670\t41.9%\t29950\t17414
noviembre 2025\t$149,970\t3\t$126,025\t$6,475\t5.1%\t49990\t47422
diciembre 2025\t$199,960\t4\t$168,032\t$7,856\t4.7%\t49990\t47652
enero 2026\t$306,940\t6\t$257,931\t$16,903\t6.6%\t51157\t47804
febrero 2026\t$170,970\t3\t$143,673\t$21,418\t14.9%\t56990\t48494
marzo 2026\t$227,960\t4\t$191,564\t$25,952\t13.5%\t56990\t49270
abril 2026\t$170,970\t3\t$143,673\t$19,806\t13.8%\t56990\t49134
mayo 2026\t$227,960\t4\t$191,564\t$26,674\t13.9%\t56990\t49055
junio 2026\t$113,980\t2\t$95,782\t$14,218\t14.8%\t56990\t48531
julio 2026\t$170,970\t3\t$143,673\t$21,327\t14.8%\t56990\t48531
agosto 2026\t$227,960\t4\t$191,564\t$28,436\t14.8%\t56990\t48531
septiembre 2026\t\t\t\t\t#DIV/0!\t#DIV/0!"""

df_base = pd.read_csv(StringIO(data_ventas), sep='\t')
df_base.columns = ['Mes_Ano', 'Total', 'Ctdad_Ordenada', 'Base_Imponible', 'Margen', 'Porcentaje_Margen', 'Precio_Unitario', 'Costo_Unitario']
for col in ['Total', 'Base_Imponible', 'Margen']:
    df_base[col] = pd.to_numeric(df_base[col].astype(str).str.replace('$', '').str.replace(',', '').str.strip(), errors='coerce')
for col in ['Ctdad_Ordenada', 'Precio_Unitario', 'Costo_Unitario']:
    df_base[col] = pd.to_numeric(df_base[col], errors='coerce')

month_map = {
    'enero': 'Jan', 'febrero': 'Feb', 'marzo': 'Mar', 'abril': 'Apr',
    'mayo': 'May', 'junio': 'Jun', 'julio': 'Jul', 'agosto': 'Aug',
    'septiembre': 'Sep', 'octubre': 'Oct', 'noviembre': 'Nov', 'diciembre': 'Dec'
}
df_base['Mes_Ano'] = pd.to_datetime(df_base['Mes_Ano'].str.lower().replace(month_map, regex=True), format='%b %Y', errors='coerce')
df_base = df_base.sort_values(by='Mes_Ano').reset_index(drop=True)
df_base['Categoria_Producto'] = 'CRONICO_MARCA'

data_ipc = """Mes / Año\tIPC INE subclase medicamentos
Noviembre 2023\t0,5
Diciembre 2023\t-1,8
Enero 2024\t-0,2
Febrero 2024\t0,5
Marzo 2024\t2,0
Abril 2024\t0,6
Mayo 2024\t0,0
Junio 2024\t0,1
Julio 2024\t1,1
Agosto 2024\t-0,9
Septiembre 2024\t1,7
Octubre 2024\t1,1
Noviembre 2024\t0,4
Diciembre 2024\t0,4
Enero 2025\t1,9
Febrero 2025\t0,3
Marzo 2025\t0,1
Abril 2025\t0,1
Mayo 2025\t-1,3
Junio 2025\t1,2
Julio 2025\t1,1
Agosto 2025\t0,3
Septiembre 2025\t0,5
Octubre 2025\t-1,1
Noviembre 2025\t1,3
Diciembre 2025\t0,3
Enero 2026\t1,3
Febrero 2026\t1,5
Marzo 2026\t-0,9
Abril 2026\t1,1
Mayo 2026\t-0,2
Junio 2026\t1,6"""

df_ipc = pd.read_csv(StringIO(data_ipc), sep='\t')
df_ipc.columns = ['Mes_Ano', 'IPC_INE_subclase_medicamentos']
df_ipc['IPC_INE_subclase_medicamentos'] = pd.to_numeric(df_ipc['IPC_INE_subclase_medicamentos'].astype(str).str.replace(',', '.'), errors='coerce')
month_map_ipc = {k.capitalize(): v for k, v in month_map.items()}
df_ipc['Mes_Ano'] = pd.to_datetime(df_ipc['Mes_Ano'].replace(month_map_ipc, regex=True), format='%b %Y', errors='coerce')

csv_compras = """Referencia,Fecha_Confirmacion,Cantidad_Total
OC08713,2026-05-25,6
OC08656,2026-05-19,6
OC08543,2026-05-08,3
OC08276,2026-04-09,2
OC08194,2026-03-31,3
OC07934,2026-02-27,2
OC07842,2026-02-17,2
OC07605,2026-01-19,3
OC07515,2026-01-07,3
OC07425,2025-12-23,2
OC07255,2025-12-04,2
OC07215,2025-11-28,2
OC07083,2025-11-12,11
OC06117,2025-08-05,15
OC05733,2025-06-10,5
OC05413,2025-04-29,15
OC04387,2024-11-05,6
OC04137,2024-09-24,10
OC04071,2024-09-10,20
OC03720,2024-07-09,6
OC03717,2024-07-09,10
OC03559,2024-06-12,6
OC03359,2024-05-14,10
OC02940,2024-03-12,20
OC02737,2024-02-07,6
OC02144,2023-11-08,20"""

df_compras = pd.read_csv(StringIO(csv_compras), parse_dates=['Fecha_Confirmacion'])
df_compras['Mes_Ano'] = df_compras['Fecha_Confirmacion'].dt.to_period('M').dt.to_timestamp()
df_compras_agg = df_compras.groupby('Mes_Ano')['Cantidad_Total'].sum().reset_index().rename(columns={'Cantidad_Total': 'Ctdad_Comprada'})

# ==============================================================================
# 2. DEFINICIÓN DE CAPAS (Pipeline de Inteligencia)
# ==============================================================================
def monitor_pipeline(func):
    @functools.wraps(func)
    def wrapper(df, *args, **kwargs):
        return func(df, *args, **kwargs)
    return wrapper

@monitor_pipeline
def capa0_sensor_humano(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    df_out['Delta_Precio_Real'] = df_out['Precio_Unitario'].diff().fillna(0)
    df_out['Flag_Intervencion_Humana'] = df_out['Delta_Precio_Real'] > 500
    primer_valido = df_out['Precio_Unitario'].first_valid_index()
    if primer_valido is not None:
        df_out.loc[primer_valido, 'Flag_Intervencion_Humana'] = True
    df_out['Margen_Mes_Real'] = (df_out['Precio_Unitario'] - df_out['Costo_Unitario']) / df_out['Precio_Unitario']
    df_out['Precio_Piso_Activo'] = df_out['Precio_Unitario'].cummax().reindex(df_out.index).ffill().fillna(0)
    margen_humano = df_out.loc[df_out['Flag_Intervencion_Humana'], 'Margen_Mes_Real']
    df_out['Margen_Humano_Historico'] = margen_humano.cummax().reindex(df_out.index).ffill().fillna(0)
    return df_out

@monitor_pipeline
def capa1_costos(df: pd.DataFrame, margen_teorico_base: float = 0.25) -> pd.DataFrame:
    df_out = df.copy()
    post_shock = df_out['Costo_Unitario'] > 30000
    df_out['Margen_Objetivo_Activo'] = pd.Series(np.where(
        post_shock, margen_teorico_base, np.maximum(margen_teorico_base, df_out['Margen_Humano_Historico'])
    )).clip(upper=0.99)
    df_out['Precio_Costo_Ideal'] = np.maximum(
        df_out['Costo_Unitario'] / (1 - df_out['Margen_Objetivo_Activo']),
        df_out['Precio_Piso_Activo']
    )
    return df_out

@monitor_pipeline
def capa2_inflacion(df: pd.DataFrame, df_inflacion: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    df_out = pd.merge(df_out, df_inflacion, on='Mes_Ano', how='left')
    df_out['IPC_Mes'] = (df_out['IPC_INE_subclase_medicamentos'] / 100).fillna(0.0)
    df_out['Precio_Ideal_Base'] = np.nan
    last_pib = None
    for i, row in df_out.iterrows():
        pci = row['Precio_Costo_Ideal'] if pd.notna(row['Precio_Costo_Ideal']) else 0.0
        ppa = row['Precio_Piso_Activo'] if pd.notna(row['Precio_Piso_Activo']) else 0.0
        ipc = row['IPC_Mes']
        flag_hum = row['Flag_Intervencion_Humana']
        if last_pib is None:
            pib = max(pci, ppa)
        else:
            p_ipc = last_pib * (1 + ipc)
            pib = max(pci, p_ipc, ppa)
        if flag_hum:
            last_pib = row['Precio_Unitario']
        else:
            last_pib = pib
        df_out.loc[i, 'Precio_Ideal_Base'] = pib
    df_out.drop(columns=['IPC_INE_subclase_medicamentos', 'IPC_Mes'], inplace=True)
    return df_out

@monitor_pipeline
def capa3_techos(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    df_out['Techo_Competitivo'] = np.inf
    return df_out

@monitor_pipeline
def capa5_valvula_stock(df: pd.DataFrame, df_compras_data: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    df_out = pd.merge(df_out, df_compras_data, on='Mes_Ano', how='left')
    df_out['Ctdad_Comprada'] = df_out['Ctdad_Comprada'].fillna(0)
    df_out['Stock_Teorico_Acumulado'] = (df_out['Ctdad_Comprada'] - df_out['Ctdad_Ordenada'].fillna(0)).cumsum()
    df_out['Flag_Quiebre_Probable'] = ((df_out['Stock_Teorico_Acumulado'] <= 1) | (df_out['Stock_Teorico_Acumulado'].shift(1) <= 1)).fillna(False)
    df_out['Var_Volumen'] = (df_out['Ctdad_Ordenada'].shift(1) / df_out['Ctdad_Ordenada'].shift(2)) - 1
    df_out['Var_Volumen'] = df_out['Var_Volumen'].replace([np.inf, -np.inf], np.nan).fillna(0)
    condiciones = [
        (df_out['Var_Volumen'] > 0),
        (df_out['Var_Volumen'] < 0) & (df_out['Flag_Quiebre_Probable'] == True),
        (df_out['Var_Volumen'] < 0) & (df_out['Flag_Quiebre_Probable'] == False)
    ]
    resultados = [
        (1 + (df_out['Var_Volumen'] * 0.15)).clip(upper=1.15),
        1.00,
        (1 + (df_out['Var_Volumen'] * 0.15)).clip(lower=0.85)
    ]
    df_out['Multiplicador_Demanda'] = np.select(condiciones, resultados, default=1.00)
    diff_u = (df_out['Ctdad_Ordenada'].shift(1) - df_out['Ctdad_Ordenada'].shift(2)).abs()
    df_out.loc[(diff_u <= 1) | (df_out['Ctdad_Ordenada'] <= 4), 'Multiplicador_Demanda'] = 1.00
    df_out['Precio_Ideal_Capa5'] = np.maximum(df_out['Precio_Ideal_Base'] * df_out['Multiplicador_Demanda'], df_out['Precio_Piso_Activo'])
    return df_out

@monitor_pipeline
def capa6_estrategia(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    df_out['Piso_Seguridad_C6'] = np.maximum(df_out['Costo_Unitario'] / (1 - df_out['Margen_Objetivo_Activo']), df_out['Precio_Piso_Activo'])
    precio_base = np.where(df_out['Precio_Ideal_Capa5'].isna(), df_out['Piso_Seguridad_C6'], df_out['Precio_Ideal_Capa5'])
    df_out['Precio_Capa6_Estrategico'] = np.maximum(precio_base, df_out['Piso_Seguridad_C6'])
    return df_out

@monitor_pipeline
def capa7_orquestacion_pesos(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    df_out['Meses_Desde_Mandato'] = 999
    ultimo_mes_humano = None
    for idx in df_out.index.tolist():
        if df_out.loc[idx, 'Flag_Intervencion_Humana']:
            ultimo_mes_humano = idx
            df_out.loc[idx, 'Meses_Desde_Mandato'] = 0
        elif ultimo_mes_humano is not None:
            df_out.loc[idx, 'Meses_Desde_Mandato'] = idx - ultimo_mes_humano
    delta_t = df_out['Meses_Desde_Mandato']
    w_humano = np.select([delta_t == 0, delta_t == 1, delta_t == 2], [1.00, 0.50, 0.20], default=0.00)
    w_algo = 1.00 - w_humano
    p_humano = df_out['Precio_Piso_Activo']
    p_algo = df_out['Precio_Capa6_Estrategico']
    precio_ponderado = w_humano * p_humano + w_algo * p_algo
    precio_acotado = np.maximum(precio_ponderado, df_out['Precio_Piso_Activo'])
    precio_final = np.where(
        delta_t == 0, df_out['Precio_Unitario'], np.round(precio_acotado / 1000) * 1000 - 10
    )
    df_out['Precio_Solufar_Emitido'] = precio_final
    df_out['Driver_Precio'] = np.select(
        [delta_t == 0, (delta_t > 0) & (delta_t <= 2)], ['MANDATO_HUMANO', 'HIBRIDO_ORQUESTADO'], default='ALGORITMO_ESTRATEGICO'
    )
    df_out['Margen_CLP_Final'] = df_out['Precio_Solufar_Emitido'] - df_out['Costo_Unitario']
    df_out['Margen_Pct_Final'] = (df_out['Margen_CLP_Final'] / df_out['Precio_Solufar_Emitido']) * 100
    return df_out

# Ejecución del Pipeline unificado
df_trazabilidad = (df_base.pipe(capa0_sensor_humano)
                          .pipe(capa1_costos, margen_teorico_base=0.25)
                          .pipe(capa2_inflacion, df_inflacion=df_ipc)
                          .pipe(capa3_techos)
                          .pipe(capa5_valvula_stock, df_compras_data=df_compras_agg)
                          .pipe(capa6_estrategia)
                          .pipe(capa7_orquestacion_pesos))

# ==============================================================================
# 3. INTERFAZ VISUAL STREAMLIT (Gráfico interactivo y Resumen Ejecutivo)
# ==============================================================================
st.sidebar.header("Filtros del Modelo")
sku_sel = st.sidebar.selectbox("Seleccionar SKU", ["Vannair Inhalador 160/4.5 x 120 Dosis"])

# Cálculos Financieros
df_calc = df_trazabilidad.dropna(subset=['Precio_Solufar_Emitido', 'Precio_Unitario', 'Ctdad_Ordenada']).copy()
ingreso_real = (df_calc['Precio_Unitario'] * df_calc['Ctdad_Ordenada']).sum()
ingreso_solufar = (df_calc['Precio_Solufar_Emitido'] * df_calc['Ctdad_Ordenada']).sum()
fuga_total = ((df_calc['Precio_Solufar_Emitido'] - df_calc['Precio_Unitario']).clip(lower=0) * df_calc['Ctdad_Ordenada']).sum()
upside = (fuga_total / ingreso_real) * 100 if ingreso_real > 0 else 0

# Tarjetas KPI
col1, col2, col3, col4 = st.columns(4)
col1.metric("Ingresos Reales (Caja)", f"${ingreso_real:,.0f}".replace(",", "."))
col2.metric("Ingresos Proyectados Solufar", f"${ingreso_solufar:,.0f}".replace(",", "."))
col3.metric("Fuga de Margen Recuperable", f"${fuga_total:,.0f}".replace(",", "."))
col4.metric("Upside Potencial", f"+{upside:.1f}%")

st.markdown("---")

# Motor de Explicación Textual
def generar_explicacion(row):
    if row['Driver_Precio'] == 'MANDATO_HUMANO':
        return f"🛑 Capa 0: Mandato Humano. Precio fijado en mostrador: ${row['Precio_Unitario']:,.0f}."
    elif row['Driver_Precio'] == 'HIBRIDO_ORQUESTADO':
        return f"⚖️ Capa 7: Ensamble Ponderado ({int(row['Meses_Desde_Mandato'])} mes/es post-intervención)."
    else:
        return f"⚙️ Algoritmo Estratégico Activo. Costo: ${row['Costo_Unitario']:,.0f} | Margen: {row['Margen_Objetivo_Activo']*100:.1f}%."

if 'Explicacion_Dinamica' not in df_trazabilidad.columns:
    df_trazabilidad['Explicacion_Dinamica'] = df_trazabilidad.apply(generar_explicacion, axis=1)

df_plot = df_trazabilidad.dropna(subset=['Precio_Unitario']).copy()
df_plot['Mes_Str'] = df_plot['Mes_Ano'].dt.strftime('%Y-%m')

# Gráfico Interactivo Plotly
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Bar(x=df_plot['Mes_Str'], y=df_plot['Ctdad_Ordenada'], name="Ventas (Cajas)", marker_color='lightblue', opacity=0.4), secondary_y=True)
fig.add_trace(go.Scatter(x=df_plot['Mes_Str'], y=df_plot['Costo_Adquisicion'] if 'Costo_Adquisicion' in df_plot else df_plot['Costo_Unitario'], name="Costo Adquisición", line=dict(color='firebrick', width=2)), secondary_y=False)
fig.add_trace(go.Scatter(x=df_plot['Mes_Str'], y=df_plot['Precio_Unitario'], name="Precio Inercial (Cobrado)", line=dict(color='gray', width=2, dash='dash')), secondary_y=False)

mapa_colores = {'MANDATO_HUMANO': '#E74C3C', 'HIBRIDO_ORQUESTADO': '#F39C12', 'ALGORITMO_ESTRATEGICO': '#27AE60'}
colores = df_plot['Driver_Precio'].map(mapa_colores)

fig.add_trace(go.Scatter(
    x=df_plot['Mes_Str'], y=df_plot['Precio_Solufar_Emitido'],
    name="Precio Estratégico Solufar",
    line=dict(color='#2E86C1', width=3),
    marker=dict(size=10, color=colores),
    customdata=df_plot['Explicacion_Dinamica'],
    hovertemplate="%{customdata}<br><b>Precio Emitido:</b> $%{y:,.0f}<extra></extra>"
), secondary_y=False)

fig.update_layout(title="<b>Inercia vs Estrategia - Trazabilidad y Auditoría de Capas</b>", hovermode="x unified", plot_bgcolor="white")
fig.update_yaxes(title_text="<b>Precio ($ CLP)</b>", tickformat="$,.0f", secondary_y=False)
fig.update_yaxes(title_text="<b>Volumen</b>", secondary_y=True, showgrid=False)

st.plotly_chart(fig, use_container_width=True)

# Resumen Ejecutivo HTML
total_meses = df_calc['Mes_Ano'].nunique()
gobernanza_counts = df_calc.groupby('Driver_Precio')['Mes_Ano'].nunique().reindex([
    'MANDATO_HUMANO', 'HIBRIDO_ORQUESTADO', 'ALGORITMO_ESTRATEGICO'
], fill_value=0)
gobernanza_pct = (gobernanza_counts / total_meses * 100).fillna(0)

UMBRAL_SHOCK_COSTOS = 30000
df_before_shock = df_calc[df_calc['Costo_Unitario'] <= UMBRAL_SHOCK_COSTOS]
df_after_shock = df_calc[df_calc['Costo_Unitario'] > UMBRAL_SHOCK_COSTOS]
margen_antes = df_before_shock['Margen_Pct_Final'].mean()
margen_despues = df_after_shock['Margen_Pct_Final'].mean()

html_resumen = f"""
<div style="font-family: Arial, sans-serif; background: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-top: 20px;">
    <h2 style="color: #34495E; border-bottom: 2px solid #ECF0F1; padding-bottom: 10px;">📊 Reporte de Gobernanza y Márgenes</h2>
    <div style="display: flex; gap: 30px; flex-wrap: wrap; margin-top: 20px;">
        <div style="flex: 1; min-width: 300px;">
            <h3 style="color: #2980B9; font-size: 1.1em;">⚙️ Gobernanza del Pricing Engine</h3>
            <ul style="line-height: 1.6; color: #555;">
                <li><b>Mandato Humano:</b> {int(gobernanza_counts['MANDATO_HUMANO'])} meses ({gobernanza_pct['MANDATO_HUMANO']:.1f}%)</li>
                <li><b>Híbrido Orquestado:</b> {int(gobernanza_counts['HIBRIDO_ORQUESTADO'])} meses ({gobernanza_pct['HIBRIDO_ORQUESTADO']:.1f}%)</li>
                <li><b>Algoritmo Estratégico:</b> {int(gobernanza_counts['ALGORITMO_ESTRATEGICO'])} meses ({gobernanza_pct['ALGORITMO_ESTRATEGICO']:.1f}%)</li>
            </ul>
        </div>
        <div style="flex: 1; min-width: 300px;">
            <h3 style="color: #27AE60; font-size: 1.1em;">📊 Evolución del Margen Bruto</h3>
            <ul style="line-height: 1.6; color: #555;">
                <li><b>Antes del Shock de Costos:</b> {margen_antes:.2f}%</li>
                <li><b>Después del Shock de Costos:</b> {margen_despues:.2f}%</li>
            </ul>
        </div>
    </div>
</div>
"""
st.markdown(html_resumen, unsafe_allow_html=True)
