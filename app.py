import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Importación del backend modular
from creador_precios import ejecutar_gemelo_digital

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==============================================================================
st.set_page_config(page_title="Gemelo Digital de Pricing - Solufar", page_icon="💊", layout="wide")

# ==============================================================================
# 2. CARGA Y PROCESAMIENTO DE DATOS
# ==============================================================================
@st.cache_data(ttl=3600)
def obtener_datos():
    return ejecutar_gemelo_digital()

try:
    df_trazabilidad = obtener_datos()
except Exception as e:
    st.error(f"🚨 Error al procesar los datos: {e}")
    st.stop()

# ==============================================================================
# FUNCIONES AUXILIARES DE TEXTO Y GRÁFICOS
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

def generar_resumen_ejecutivo(df: pd.DataFrame) -> str:
    df_calc = df.dropna(subset=['Mes_Ano', 'Ctdad_Ordenada', 'Precio_Unitario', 'Costo_Unitario', 'Precio_Solufar_Emitido']).copy()
    
    ingresos_reales = (df_calc['Precio_Unitario'] * df_calc['Ctdad_Ordenada']).sum()
    ingresos_solufar = (df_calc['Precio_Solufar_Emitido'] * df_calc['Ctdad_Ordenada']).sum()
    df_calc['Brecha'] = (df_calc['Precio_Solufar_Emitido'] - df_calc['Precio_Unitario']).clip(lower=0)
    df_calc['Fuga_Valor'] = df_calc['Brecha'] * df_calc['Ctdad_Ordenada']
    fuga_total = df_calc['Fuga_Valor'].sum()
    upside_pct = ((ingresos_solufar - ingresos_reales) / ingresos_reales) * 100 if ingresos_reales > 0 else 0.0

    cantidad_skus = df_calc['Nombre_Producto'].nunique()
    total_cajas = df_calc['Ctdad_Ordenada'].sum()
    meses_totales = df_calc['Mes_Ano'].nunique()
    capas_activas = 8 
    
    df_calc = df_calc.sort_values(by=['Nombre_Producto', 'Mes_Ano'])
    df_calc['Cambio_Precio'] = df_calc.groupby('Nombre_Producto')['Precio_Unitario'].diff().fillna(1)
    meses_congelados_totales = (df_calc['Cambio_Precio'] == 0).sum()
    promedio_congelado_por_sku = meses_congelados_totales / cantidad_skus if cantidad_skus > 0 else 0
    
    costo_total_vendido = (df_calc['Costo_Unitario'] * df_calc['Ctdad_Ordenada']).sum()
    margen_real_pct = ((ingresos_reales - costo_total_vendido) / ingresos_reales) * 100 if ingresos_reales > 0 else 0
    margen_solufar_pct = ((ingresos_solufar - costo_total_vendido) / ingresos_solufar) * 100 if ingresos_solufar > 0 else 0

    resumen_sku = df_calc.groupby('Nombre_Producto').agg(
        Cajas_Vendidas=('Ctdad_Ordenada', 'sum'),
        Meses_Inercia=('Cambio_Precio', lambda x: (x == 0).sum()),
        Fuga=('Fuga_Valor', 'sum')
    ).reset_index().sort_values(by='Fuga', ascending=False)

    filas_tabla_html = ""
    for _, row in resumen_sku.iterrows():
        nombre_corto = str(row['Nombre_Producto'])[:45] + "..." if len(str(row['Nombre_Producto'])) > 45 else str(row['Nombre_Producto'])
        filas_tabla_html += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ecf0f1; font-size: 13px; color: #2c3e50;">{nombre_corto}</td>
            <td style="padding: 10px; border-bottom: 1px solid #ecf0f1; text-align: center; font-size: 13px; font-weight: bold; color: #2c3e50;">{row['Cajas_Vendidas']:,.0f}</td>
            <td style="padding: 10px; border-bottom: 1px solid #ecf0f1; text-align: center; font-size: 13px; color: #2c3e50;">{row['Meses_Inercia']} meses</td>
            <td style="padding: 10px; border-bottom: 1px solid #ecf0f1; text-align: right; color: #C0392B; font-weight: bold; font-size: 13px;">${row['Fuga']:,.0f}</td>
        </tr>
        """

    html_content = f"""
    <div style="max-width: 1100px; font-family: 'Segoe UI', Arial, sans-serif; padding: 25px; background: #ffffff; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-radius: 12px; border-top: 6px solid #2C3E50;">
        <h2 style="color: #2C3E50; margin-top: 0; font-size: 22px; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px;">
            📊 Diagnóstico Gemelo Digital Solufar
        </h2>
        
        <div style="display: flex; gap: 20px; margin-top: 20px;">
            <div style="flex: 1; padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: center; border: 1px solid #e9ecef;">
                <h4 style="margin:0; color:#34495E; font-size: 14px; text-transform: uppercase;">Ingresos Reales (Inercia)</h4>
                <p style="font-size:26px; font-weight:bold; margin:10px 0 0 0; color:#2C3E50;">${ingresos_reales:,.0f}</p>
            </div>
            <div style="flex: 1; padding: 20px; background: #E8F8F5; border-radius: 8px; text-align: center; border: 1px solid #A3E4D7;">
                <h4 style="margin:0; color:#27AE60; font-size: 14px; text-transform: uppercase;">Proyección Solufar</h4>
                <p style="font-size:26px; font-weight:bold; margin:10px 0 0 0; color:#1E8449;">${ingresos_solufar:,.0f}</p>
            </div>
            <div style="flex: 1; padding: 20px; background: #FDEDEC; border-radius: 8px; text-align: center; border: 1px solid #F5B7B1;">
                <h4 style="margin:0; color:#C0392B; font-size: 14px; text-transform: uppercase;">Fuga Identificada</h4>
                <p style="font-size:26px; font-weight:bold; margin:10px 0 0 0; color:#A93226;">${fuga_total:,.0f}</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #A93226; font-weight: bold;">Upside General: +{upside_pct:,.1f}%</p>
            </div>
        </div>

        <h3 style="color: #34495E; font-size: 16px; margin-top: 30px; margin-bottom: 15px;">⚙️ Alcance del Estudio y Eficiencia</h3>
        <div style="display: flex; gap: 15px; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 150px; padding: 15px; background: #fdfefe; border: 1px solid #ecf0f1; border-radius: 6px; text-align: center;">
                <p style="margin:0; color:#7f8c8d; font-size:12px; text-transform: uppercase; font-weight:bold;">SKUs Analizados</p>
                <p style="margin:5px 0 0 0; color:#2c3e50; font-size:20px; font-weight:bold;">{cantidad_skus}</p>
            </div>
            <div style="flex: 1; min-width: 150px; padding: 15px; background: #fdfefe; border: 1px solid #ecf0f1; border-radius: 6px; text-align: center;">
                <p style="margin:0; color:#7f8c8d; font-size:12px; text-transform: uppercase; font-weight:bold;">Periodo (Meses)</p>
                <p style="margin:5px 0 0 0; color:#2c3e50; font-size:20px; font-weight:bold;">{meses_totales}</p>
            </div>
            <div style="flex: 1; min-width: 150px; padding: 15px; background: #fdfefe; border: 1px solid #ecf0f1; border-radius: 6px; text-align: center;">
                <p style="margin:0; color:#7f8c8d; font-size:12px; text-transform: uppercase; font-weight:bold;">Capas Algoritmo</p>
                <p style="margin:5px 0 0 0; color:#2c3e50; font-size:20px; font-weight:bold;">{capas_activas} Activas</p>
            </div>
            <div style="flex: 1; min-width: 150px; padding: 15px; background: #fff4e6; border: 1px solid #ffd8a8; border-radius: 6px; text-align: center;">
                <p style="margin:0; color:#d35400; font-size:12px; text-transform: uppercase; font-weight:bold;">Inercia Promedio</p>
                <p style="margin:5px 0 0 0; color:#d35400; font-size:20px; font-weight:bold;">{promedio_congelado_por_sku:,.1f} Meses/SKU</p>
                <p style="margin:0; font-size:10px; color:#e67e22;">Sin actualizar precio</p>
            </div>
        </div>

        <div style="display: flex; margin-top: 15px; background: #f8f9fa; border: 1px solid #ecf0f1; border-radius: 6px; padding: 15px;">
            <div style="flex: 1; text-align: center; border-right: 1px solid #ddd;">
                <p style="margin:0; color:#34495E; font-size:13px; font-weight:bold;">Margen Bruto Histórico</p>
                <p style="margin:5px 0 0 0; color:#7f8c8d; font-size:20px; font-weight:bold;">{margen_real_pct:,.1f}%</p>
            </div>
            <div style="flex: 1; text-align: center;">
                <p style="margin:0; color:#2980B9; font-size:13px; font-weight:bold;">Margen Proyectado Solufar</p>
                <p style="margin:5px 0 0 0; color:#2980B9; font-size:20px; font-weight:bold;">{margen_solufar_pct:,.1f}%</p>
            </div>
        </div>

        <h3 style="color: #34495E; font-size: 16px; margin-top: 30px; margin-bottom: 15px;">📋 Desglose de Impacto por SKU</h3>
        <table style="width: 100%; border-collapse: collapse; background: #ffffff;">
            <thead>
                <tr style="background-color: #34495E; color: white;">
                    <th style="padding: 10px; text-align: left; font-size: 13px; border-radius: 6px 0 0 0;">Medicamento</th>
                    <th style="padding: 10px; text-align: center; font-size: 13px;">Volumen (Cajas)</th>
                    <th style="padding: 10px; text-align: center; font-size: 13px;">Inercia (Meses sin actualizar)</th>
                    <th style="padding: 10px; text-align: right; font-size: 13px; border-radius: 0 6px 0 0;">Fuga Recuperable (CLP)</th>
                </tr>
            </thead>
            <tbody>
                {filas_tabla_html}
            </tbody>
        </table>
    </div>
    """
    return html_content

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
    st.markdown("Radiografía financiera de la cartera evaluada demostrando el impacto del algoritmo predictivo frente a la inercia comercial.")
    
    html_resumen = generar_resumen_ejecutivo(df_trazabilidad)
    # 🔴 INSTRUCCIÓN DE SEGURIDAD CORREGIDA
    st.markdown(html_resumen, unsafe_allow_html=True)

# ==============================================================================
# 5. PÁGINA 2: AUDITORÍA DETALLADA POR SKU
# ==============================================================================
elif menu == "🔍 Auditoría Detallada por SKU":
    st.header("🔍 Auditoría Detallada del Motor de Precios")
    st.markdown("Revisa el comportamiento mes a mes de las 8 capas estratégicas del algoritmo para cada medicamento.")
    
    lista_productos = df_trazabilidad['Nombre_Producto'].dropna().unique().tolist()
    producto_sel = st.selectbox("Seleccione un Medicamento para Analizar:", lista_productos)
    
    # Renderizamos el gráfico
    st.plotly_chart(crear_grafico_auditoria(df_trazabilidad, producto_sel), use_container_width=True)

    # -------------------------------------------------------------------------
    # 📝 BITÁCORA CON DIAGNÓSTICO DETALLADO HTML
    # -------------------------------------------------------------------------
    st.markdown("### 📝 Bitácora de Decisiones Algorítmicas")
    
    df_filtrado = df_trazabilidad[df_trazabilidad['Nombre_Producto'] == producto_sel].dropna(subset=['Precio_Solufar_Emitido', 'Costo_Unitario']).copy()
    
    # Aplicamos la misma función para la explicación detallada
    df_filtrado['Explicacion_Dinamica'] = df_filtrado.apply(generar_explicacion, axis=1)
    
    # Formateo de las columnas
    df_filtrado['Mes'] = df_filtrado['Mes_Ano'].dt.strftime('%Y-%m')
    df_filtrado['Costo_Odoo'] = df_filtrado['Costo_Unitario'].apply(lambda x: f"${x:,.0f}")
    df_filtrado['Precio_Inercial'] = df_filtrado['Precio_Unitario'].apply(lambda x: f"${x:,.0f}")
    df_filtrado['Precio_Solufar'] = df_filtrado['Precio_Solufar_Emitido'].apply(lambda x: f"${x:,.0f}")
    df_filtrado['Margen_Final'] = df_filtrado['Margen_Pct_Final'].apply(lambda x: f"{x:.1f}%")
    
    # Selección y renombre
    df_vista = df_filtrado[['Mes', 'Costo_Odoo', 'Precio_Inercial', 'Precio_Solufar', 'Margen_Final', 'Explicacion_Dinamica']].copy()
    df_vista.rename(columns={
        'Costo_Odoo': 'Costo Adquisición',
        'Precio_Inercial': 'Precio Histórico (Cobrado)',
        'Precio_Solufar': 'Precio Óptimo (Solufar)',
        'Margen_Final': 'Margen Proyectado',
        'Explicacion_Dinamica': 'Diagnóstico de Capas (Algoritmo)'
    }, inplace=True)
    
    # Conversión a tabla HTML cruda
    tabla_html = df_vista.to_html(escape=False, index=False, classes="tabla-bitacora")
    
    # Inyección de CSS para diseño ejecutivo
    estilo_tabla = f"""
    <style>
        .tabla-bitacora {{
            background-color: #ffffff;
            border-collapse: collapse;
            width: 100%;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }}
        .tabla-bitacora th {{
            background-color: #34495E;
            color: white;
            text-align: left;
            padding: 12px 15px;
            border: none;
        }}
        .tabla-bitacora td {{
            padding: 12px 15px;
            border-bottom: 1px solid #ecf0f1;
            color: #2c3e50;
            vertical-align: middle;
        }}
        .tabla-bitacora tbody tr:hover {{
            background-color: #f8f9fa;
        }}
    </style>
    <div style="overflow-x: auto; border-radius: 8px; border: 1px solid #ecf0f1; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top: 10px;">
        {tabla_html}
    </div>
    """
    
    st.markdown(estilo_tabla, unsafe_allow_html=True)
