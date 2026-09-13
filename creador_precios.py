# creador_precios.py - Backend del Gemelo Digital de Pricing Solufar

import pandas as pd
import numpy as np
import functools
from io import StringIO

# ==============================================================================
# 1. INGESTA Y LIMPIEZA DE DATOS
# ==============================================================================
def cargar_datos():
    # A. Historial de Ventas (Odoo)
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
    df_base['Categoria_Producto'] = 'BIOEQUIVALENTE_MARCA'

    # B. Historial de Inflación (IPC)
    data_ipc = """Mes / Año\tIPC INE subclase medicamentos
Noviembre 2023\t0,5\nDiciembre 2023\t-1,8\nEnero 2024\t-0,2\nFebrero 2024\t0,5\nMarzo 2024\t2,0\nAbril 2024\t0,6\nMayo 2024\t0,0\nJunio 2024\t0,1\nJulio 2024\t1,1\nAgosto 2024\t-0,9\nSeptiembre 2024\t1,7\nOctubre 2024\t1,1\nNoviembre 2024\t0,4\nDiciembre 2024\t0,4\nEnero 2025\t1,9\nFebrero 2025\t0,3\nMarzo 2025\t0,1\nAbril 2025\t0,1\nMayo 2025\t-1,3\nJunio 2025\t1,2\nJulio 2025\t1,1\nAgosto 2025\t0,3\nSeptiembre 2025\t0,5\nOctubre 2025\t-1,1\nNoviembre 2025\t1,3\nDiciembre 2025\t0,3\nEnero 2026\t1,3\nFebrero 2026\t1,5\nMarzo 2026\t-0,9\nAbril 2026\t1,1\nMayo 2026\t-0,2\nJunio 2026\t1,6"""
    df_ipc = pd.read_csv(StringIO(data_ipc), sep='\t')
    df_ipc.columns = ['Mes_Ano', 'IPC_INE_subclase_medicamentos']
    df_ipc['IPC_INE_subclase_medicamentos'] = pd.to_numeric(df_ipc['IPC_INE_subclase_medicamentos'].astype(str).str.replace(',', '.'), errors='coerce')
    month_map_ipc = {k.capitalize(): v for k, v in month_map.items()}
    df_ipc['Mes_Ano'] = pd.to_datetime(df_ipc['Mes_Ano'].replace(month_map_ipc, regex=True), format='%b %Y', errors='coerce')

    # C. Historial de Compras (Odoo)
    csv_compras = """Referencia,Fecha_Confirmacion,Cantidad_Total
OC08713,2026-05-25,6\nOC08656,2026-05-19,6\nOC08543,2026-05-08,3\nOC08276,2026-04-09,2\nOC08194,2026-03-31,3\nOC07934,2026-02-27,2\nOC07842,2026-02-17,2\nOC07605,2026-01-19,3\nOC07515,2026-01-07,3\nOC07425,2025-12-23,2\nOC07255,2025-12-04,2\nOC07215,2025-11-28,2\nOC07083,2025-11-12,11\nOC06117,2025-08-05,15\nOC05733,2025-06-10,5\nOC05413,2025-04-29,15\nOC04387,2024-11-05,6\nOC04137,2024-09-24,10\nOC04071,2024-09-10,20\nOC03720,2024-07-09,6\nOC03717,2024-07-09,10\nOC03559,2024-06-12,6\nOC03359,2024-05-14,10\nOC02940,2024-03-12,20\nOC02737,2024-02-07,6\nOC02144,2023-11-08,20"""
    df_compras = pd.read_csv(StringIO(csv_compras), parse_dates=['Fecha_Confirmacion'])
    df_compras['Mes_Ano'] = df_compras['Fecha_Confirmacion'].dt.to_period('M').dt.to_timestamp()
    df_compras_agg = df_compras.groupby('Mes_Ano')['Cantidad_Total'].sum().reset_index().rename(columns={'Cantidad_Total': 'Ctdad_Comprada'})

    return df_base, df_ipc, df_compras_agg

# ==============================================================================
# 2. MONITOR Y CAPAS ALGORÍTMICAS
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
def capa1_estrategia_categoria(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    politicas_margen = {
        'KVI_known_Value_Item': 0.15,
        'NICHO': 0.40,
        'GENERICO': 0.30,
        'BIOEQUIVALENTE_MARCA': 0.18
    }
    politicas_shock = {
        'KVI_known_Value_Item': 20000,
        'NICHO': 10000,
        'GENERICO': 4000,
        'BIOEQUIVALENTE_MARCA': 25000
    }
    df_out['Margen_Teorico_Base'] = df_out['Categoria_Producto'].map(politicas_margen).fillna(0.25)
    df_out['Umbral_Shock_Costo'] = df_out['Categoria_Producto'].map(politicas_shock).fillna(30000)
    return df_out


@monitor_pipeline
def capa2_costos(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    post_shock = df_out['Costo_Unitario'] > df_out['Umbral_Shock_Costo']
    df_out['Margen_Objetivo_Activo'] = pd.Series(np.where(
        post_shock,
        df_out['Margen_Teorico_Base'],
        np.maximum(df_out['Margen_Teorico_Base'], df_out['Margen_Humano_Historico'])
    )).clip(upper=0.99)
    df_out['Precio_Costo_Ideal'] = np.maximum(
        df_out['Costo_Unitario'] / (1 - df_out['Margen_Objetivo_Activo']),
        df_out['Precio_Piso_Activo']
    )
    return df_out

@monitor_pipeline
def capa3_inflacion(df: pd.DataFrame, df_inflacion: pd.DataFrame) -> pd.DataFrame:
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
def capa4_techos(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    df_out['Techo_Competitivo'] = np.inf
    return df_out

@monitor_pipeline
def capa5_valvula_stock(df: pd.DataFrame, df_compras_data: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    df_out = pd.merge(df_out, df_compras_data, on='Mes_Ano', how='left')
    df_out['Ctdad_Comprada'] = df_out['Ctdad_Comprada'].fillna(0)
    df_out['Stock_Teorico_Acumulado'] = (df_out['Ctdad_Comprada'] - df_out['Ctdad_Ordenada'].fillna(0)).cumsum()
    df_out['Flag_Quiebre_Probable'] = ((df_out['Stock_Teorico_Acumulado'] <= 1) |
                                       (df_out['Stock_Teorico_Acumulado'].shift(1) <= 1)).fillna(False)
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
    df_out['Precio_Ideal_Capa5'] = np.maximum(
        df_out['Precio_Ideal_Base'] * df_out['Multiplicador_Demanda'],
        df_out['Precio_Piso_Activo']
    )
    return df_out

@monitor_pipeline
def capa6_blindaje(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    df_out['Piso_Seguridad_C6'] = np.maximum(
        df_out['Costo_Unitario'] / (1 - df_out['Margen_Objetivo_Activo']),
        df_out['Precio_Piso_Activo']
    )
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
        delta_t == 0,
        df_out['Precio_Unitario'],
        np.round(precio_acotado / 1000) * 1000 - 10
    )
    df_out['Precio_Solufar_Emitido'] = precio_final
    df_out['Driver_Precio'] = np.select(
        [delta_t == 0, (delta_t > 0) & (delta_t <= 2)],
        ['MANDATO_HUMANO', 'HIBRIDO_ORQUESTADO'],
        default='ALGORITMO_ESTRATEGICO'
    )
    df_out['Margen_CLP_Final'] = df_out['Precio_Solufar_Emitido'] - df_out['Costo_Unitario']
    df_out['Margen_Pct_Final'] = (df_out['Margen_CLP_Final'] / df_out['Precio_Solufar_Emitido']) * 100
    return df_out

# ==============================================================================
# 3. ENSAMBLADOR PRINCIPAL (Exportado a app.py)
# ==============================================================================
def ejecutar_gemelo_digital():
    df_base, df_ipc, df_compras_agg = cargar_datos()
    df_trazabilidad = (df_base.pipe(capa0_sensor_humano)
                              .pipe(capa1_estrategia_categoria)
                              .pipe(capa2_costos)
                              .pipe(capa3_inflacion, df_inflacion=df_ipc)
                              .pipe(capa4_techos)
                              .pipe(capa5_valvula_stock, df_compras_data=df_compras_agg)
                              .pipe(capa6_blindaje)
                              .pipe(capa7_orquestacion_pesos))
    return df_trazabilidad
