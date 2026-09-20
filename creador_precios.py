# creador_precios.py - Backend del Gemelo Digital de Pricing Solufar

import pandas as pd
import numpy as np
import functools
from io import StringIO
import warnings

# Suprimir advertencias
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# ==============================================================================
# VARIABLES GLOBALES DE NEGOCIO (Antes en config.py)
# ==============================================================================
MONTH_MAP = {
    'enero': 'Jan', 'febrero': 'Feb', 'marzo': 'Mar', 'abril': 'Apr',
    'mayo': 'May', 'junio': 'Jun', 'julio': 'Jul', 'agosto': 'Aug',
    'septiembre': 'Sep', 'octubre': 'Oct', 'noviembre': 'Nov', 'diciembre': 'Dec'
}

POLITICAS_MARGEN = {
    'KVI_known_Value_Item': 0.15,
    'NICHO': 0.40,
    'GENERICO': 0.30,
    'BIOEQUIVALENTE_MARCA': 0.18
}

POLITICAS_SHOCK = {
    'KVI_known_Value_Item': 20000,
    'NICHO': 10000,
    'GENERICO': 4000,
    'BIOEQUIVALENTE_MARCA': 25000
}

UMBRAL_SHOCK_COSTOS = 30000

# ==============================================================================
# 1. INGESTA DE DATOS (Conectado a GSheets)
# ==============================================================================
def cargar_ventas():
    url_ventas = 'https://docs.google.com/spreadsheets/d/1pvREtGQ-dWrm4XrerV1U8EBqYgMBtgUjYgywdodcR6I/export?format=xlsx'
    hoja_ventas = 'Base_Gemelo_Digital_10_SKUs'
    df_base = pd.read_excel(url_ventas, sheet_name=hoja_ventas)

    df_base['Mes_Ano'] = pd.to_datetime(
        df_base['Mes_Ano'].astype(str).str.lower().replace(MONTH_MAP, regex=True),
        format='%b %Y', errors='coerce'
    )
    df_base = df_base.sort_values(by=['SKU_ID', 'Mes_Ano']).reset_index(drop=True)

    df_base['Precio_Unitario'] = df_base['Precio_Unitario'].replace(0, np.nan)
    df_base['Costo_Unitario'] = df_base['Costo_Unitario'].replace(0, np.nan)

    cols_to_fill = ['Precio_Unitario', 'Costo_Unitario']
    df_base[cols_to_fill] = df_base.groupby('SKU_ID')[cols_to_fill].ffill()

    df_base['Precio_Unitario'] = df_base['Precio_Unitario'].fillna(0)
    df_base['Costo_Unitario'] = df_base['Costo_Unitario'].fillna(0)
    df_base['Ctdad_Ordenada'] = df_base['Ctdad_Ordenada'].fillna(0)

    df_base['Precio_Unitario_Safe'] = df_base['Precio_Unitario'].replace(0, np.nan)
    df_base['Ctdad_Ordenada_Safe'] = df_base['Ctdad_Ordenada'].replace(0, np.nan)

    return df_base

def cargar_inflacion():
    data_ipc = """Mes / Año\tIPC INE subclase medicamentos
Noviembre 2023\t0,5\nDiciembre 2023\t-1,8\nEnero 2024\t-0,2\nFebrero 2024\t0,5\nMarzo 2024\t2,0\nAbril 2024\t0,6\nMayo 2024\t0,0\nJunio 2024\t0,1\nJulio 2024\t1,1\nAgosto 2024\t-0,9\nSeptiembre 2024\t1,7\nOctubre 2024\t1,1\nNoviembre 2024\t0,4\nDiciembre 2024\t0,4\nEnero 2025\t1,9\nFebrero 2025\t0,3\nMarzo 2025\t0,1\nAbril 2025\t0,1\nMayo 2025\t-1,3\nJunio 2025\t1,2\nJulio 2025\t1,1\nAgosto 2025\t0,3\nSeptiembre 2025\t0,5\nOctubre 2025\t-1,1\nNoviembre 2025\t1,3\nDiciembre 2025\t0,3\nEnero 2026\t1,3\nFebrero 2026\t1,5\nMarzo 2026\t-0,9\nAbril 2026\t1,1\nMayo 2026\t-0,2\nJunio 2026\t1,6"""
    df_ipc = pd.read_csv(StringIO(data_ipc), sep='\t')
    df_ipc.columns = ['Mes_Ano', 'IPC_INE_subclase_medicamentos']
    df_ipc['IPC_INE_subclase_medicamentos'] = pd.to_numeric(
        df_ipc['IPC_INE_subclase_medicamentos'].astype(str).str.replace(',', '.'), errors='coerce'
    )
    month_map_ipc = {k.capitalize(): v for k, v in MONTH_MAP.items()}
    df_ipc['Mes_Ano'] = pd.to_datetime(
        df_ipc['Mes_Ano'].replace(month_map_ipc, regex=True), format='%b %Y', errors='coerce'
    )
    return df_ipc

def cargar_compras() -> pd.DataFrame:
    url_base = 'https://docs.google.com/spreadsheets/d/1qN3bRUq04e31fR5s-n_D-kYW98_nqCCuIlaTOm_3rqI'
    hoja_compras = 'Compras_Mes'
    url_compras = f'{url_base}/gviz/tq?tqx=out:csv&sheet={hoja_compras}'
    
    df_compras = pd.read_csv(url_compras)

    if df_compras.empty:
        return pd.DataFrame(columns=['SKU_ID', 'Mes_Ano', 'Ctdad_Comprada', 'Ctdad_Facturada', 'Total_Libre_Impuestos'])

    df_compras['Producto'] = df_compras['Producto'].ffill()
    df_compras['SKU_ID'] = df_compras['Producto'].str.extract(r'\[(.*?)\]')[0].fillna(-1).astype(int)
    df_compras['Nombre_Producto'] = df_compras['Producto'].str.extract(r'\]\s*(.*)')[0].str.strip()

    df_compras['Mes_Ano'] = pd.to_datetime(
        df_compras['Mes'].astype(str).str.lower().replace(MONTH_MAP, regex=True),
        format='%b %Y', errors='coerce'
    )

    columnas_a_sumar = ['Ctdad_recibida', 'Ctdad_facturada', 'Total_libre_impuestos']
    df_compras_agg = df_compras.groupby(['SKU_ID', 'Nombre_Producto', 'Mes_Ano'])[columnas_a_sumar].sum().reset_index()

    df_compras_agg.rename(columns={
        'Ctdad_recibida': 'Ctdad_Comprada',
        'Ctdad_facturada': 'Ctdad_Facturada',
        'Total_libre_impuestos': 'Total_Libre_Impuestos'
    }, inplace=True)

    return df_compras_agg

# ==============================================================================
# 2. CAPAS ALGORÍTMICAS
# ==============================================================================
def capa0_sensor_humano(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    df_out['Delta_Precio_Real'] = df_out['Precio_Unitario'].diff().fillna(0)
    df_out['Flag_Intervencion_Humana'] = (df_out['Delta_Precio_Real'] > 500).fillna(False)

    primer_valido = df_out['Precio_Unitario_Safe'].first_valid_index()
    if primer_valido is not None:
        df_out.loc[primer_valido, 'Flag_Intervencion_Humana'] = True

    df_out['Margen_Mes_Real'] = ((df_out['Precio_Unitario'] - df_out['Costo_Unitario']) / df_out['Precio_Unitario_Safe']).fillna(0)
    df_out['Precio_Piso_Activo'] = df_out['Precio_Unitario'].cummax().ffill().fillna(0)

    margen_humano = df_out.loc[df_out['Flag_Intervencion_Humana'], 'Margen_Mes_Real']
    df_out['Margen_Humano_Historico'] = margen_humano.cummax().reindex(df_out.index).ffill().fillna(0)
    return df_out

def capa1_estrategia_categoria(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    df_out['Margen_Teorico_Base'] = df_out['Categoria_Producto'].map(POLITICAS_MARGEN).fillna(0.25)
    df_out['Umbral_Shock_Costo'] = df_out['Categoria_Producto'].map(POLITICAS_SHOCK).fillna(30000)
    return df_out

def capa2_costos(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    post_shock = df_out['Costo_Unitario'] > df_out['Umbral_Shock_Costo']

    df_out['Margen_Objetivo_Activo'] = df_out['Margen_Teorico_Base'].where(
        post_shock,
        df_out['Margen_Teorico_Base'].clip(lower=df_out['Margen_Humano_Historico'])
    ).clip(upper=0.99).fillna(0.25)

    costo_ideal = df_out['Costo_Unitario'] / (1 - df_out['Margen_Objetivo_Activo'])
    df_out['Precio_Costo_Ideal'] = costo_ideal.clip(lower=df_out['Precio_Piso_Activo']).fillna(0)
    return df_out

def capa3_inflacion(df: pd.DataFrame, df_inflacion: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    df_out = pd.merge(df_out, df_inflacion, on='Mes_Ano', how='left')
    df_out['IPC_Mes'] = (df_out['IPC_INE_subclase_medicamentos'] / 100).fillna(0.0)

    precios_ideales = []
    last_pib = None

    for _, row in df_out.iterrows():
        pci = row['Precio_Costo_Ideal']
        ppa = row['Precio_Piso_Activo']
        ipc = row['IPC_Mes']
        flag_hum = row['Flag_Intervencion_Humana']

        if last_pib is None:
            pib = max(pci, ppa)
        else:
            p_ipc = last_pib * (1 + ipc)
            pib = max(pci, p_ipc, ppa)

        last_pib = row['Precio_Unitario'] if flag_hum else pib
        precios_ideales.append(pib if pd.notna(pib) else 0.0)

    df_out['Precio_Ideal_Base'] = precios_ideales
    df_out.drop(columns=['IPC_INE_subclase_medicamentos', 'IPC_Mes'], inplace=True, errors='ignore')
    return df_out

def capa4_techos(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    df_out['Techo_Competitivo'] = np.inf
    return df_out

def capa5_valvula_stock(df: pd.DataFrame, df_compras_data: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    df_compras_temp = df_compras_data.drop(columns=['Nombre_Producto'], errors='ignore')
    df_out = pd.merge(df_out, df_compras_temp, on=['SKU_ID', 'Mes_Ano'], how='left')

    df_out['Ctdad_Comprada'] = df_out['Ctdad_Comprada'].fillna(0)
    df_out['Stock_Teorico_Acumulado'] = (df_out['Ctdad_Comprada'] - df_out['Ctdad_Ordenada'].fillna(0)).cumsum()

    df_out['Flag_Quiebre_Probable'] = ((df_out['Stock_Teorico_Acumulado'] <= 1) |
                                       (df_out['Stock_Teorico_Acumulado'].shift(1) <= 1)).fillna(False)

    vol_shift2 = df_out['Ctdad_Ordenada_Safe'].shift(2)
    df_out['Var_Volumen'] = (df_out['Ctdad_Ordenada'].shift(1) / vol_shift2) - 1
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

    ideal_ajustado = df_out['Precio_Ideal_Base'] * df_out['Multiplicador_Demanda']
    df_out['Precio_Ideal_Capa5'] = ideal_ajustado.clip(lower=df_out['Precio_Piso_Activo']).fillna(df_out['Precio_Piso_Activo'])
    return df_out

def capa6_blindaje(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    piso_calc = df_out['Costo_Unitario'] / (1 - df_out['Margen_Objetivo_Activo'])
    df_out['Piso_Seguridad_C6'] = piso_calc.clip(lower=df_out['Precio_Piso_Activo']).fillna(0)

    precio_base = df_out['Precio_Ideal_Capa5'].fillna(df_out['Piso_Seguridad_C6'])
    df_out['Precio_Capa6_Estrategico'] = precio_base.clip(lower=df_out['Piso_Seguridad_C6']).fillna(0)
    return df_out

def capa7_orquestacion_pesos(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    meses_desde = []
    ultimo_mes_humano = None

    for i, flag in enumerate(df_out['Flag_Intervencion_Humana']):
        if flag:
            ultimo_mes_humano = i
            meses_desde.append(0)
        elif ultimo_mes_humano is not None:
            meses_desde.append(i - ultimo_mes_humano)
        else:
            meses_desde.append(999)

    df_out['Meses_Desde_Mandato'] = meses_desde
    delta_t = df_out['Meses_Desde_Mandato']

    w_humano_arr = np.select([delta_t == 0, delta_t == 1, delta_t == 2], [1.00, 0.50, 0.20], default=0.00)
    w_humano = pd.Series(w_humano_arr, index=df_out.index)
    w_algo = 1.00 - w_humano

    p_humano = df_out['Precio_Piso_Activo']
    p_algo = df_out['Precio_Capa6_Estrategico']

    precio_ponderado = (w_humano * p_humano) + (w_algo * p_algo)
    precio_acotado = precio_ponderado.clip(lower=df_out['Precio_Piso_Activo']).fillna(0)
    precio_calculado = np.round(precio_acotado / 1000) * 1000 - 10

    df_out['Precio_Solufar_Emitido'] = df_out['Precio_Unitario'].where(delta_t == 0, precio_calculado).fillna(0)

    df_out['Driver_Precio'] = np.select(
        [delta_t == 0, (delta_t > 0) & (delta_t <= 2)],
        ['MANDATO_HUMANO', 'HIBRIDO_ORQUESTADO'],
        default='ALGORITMO_ESTRATEGICO'
    )

    df_out['Margen_CLP_Final'] = df_out['Precio_Solufar_Emitido'] - df_out['Costo_Unitario']
    precio_emitido_safe = df_out['Precio_Solufar_Emitido'].replace(0, np.nan)
    df_out['Margen_Pct_Final'] = ((df_out['Margen_CLP_Final'] / precio_emitido_safe) * 100).fillna(0)
    return df_out

# ==============================================================================
# 3. ORQUESTADOR PRINCIPAL (Importado por app.py)
# ==============================================================================
def ejecutar_gemelo_digital():
    df_base = cargar_ventas()
    df_ipc = cargar_inflacion()
    df_compras_agg = cargar_compras()

    def procesar_un_sku(df_grupo):
        df_grupo = df_grupo.reset_index(drop=True)
        return (df_grupo.pipe(capa0_sensor_humano)
                        .pipe(capa1_estrategia_categoria)
                        .pipe(capa2_costos)
                        .pipe(capa3_inflacion, df_inflacion=df_ipc)
                        .pipe(capa4_techos)
                        .pipe(capa5_valvula_stock, df_compras_data=df_compras_agg)
                        .pipe(capa6_blindaje)
                        .pipe(capa7_orquestacion_pesos))

    resultados_sku = []
    for sku_id, df_grupo in df_base.groupby('SKU_ID'):
        df_procesado = procesar_un_sku(df_grupo.copy())
        resultados_sku.append(df_procesado)

    df_trazabilidad = pd.concat(resultados_sku, ignore_index=True)

    if 'Nombre_Producto' not in df_trazabilidad.columns:
        df_trazabilidad = df_trazabilidad.reset_index()

    df_trazabilidad = df_trazabilidad.sort_values(by=['Nombre_Producto', 'Mes_Ano']).reset_index(drop=True)
    return df_trazabilidad
