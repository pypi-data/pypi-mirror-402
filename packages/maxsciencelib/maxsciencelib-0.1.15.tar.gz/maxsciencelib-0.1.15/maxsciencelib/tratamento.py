import numpy as np
import pandas as pd
import polars as pl
from typing import Union
import re

def _agrupamento_vidro(produto_descricao, agrupar_marca=True, agrupar_lado=True):
    marcas_vid = [' AIS-AGC',' NORDGLASS-AGC',' PK',' SG',' AGC',' FN',' FY',' XYG',' VITRO',' VFORTE',' TYC',' DEPO']
    lados = [' LD/LE ',' LE/LD ',' LE ',' LD ', ' E ', ' D ']

    produto_agrupado = produto_descricao

    if agrupar_marca:
        for marca in marcas_vid:
            if marca in produto_agrupado:
                produto_agrupado = produto_agrupado.replace(marca, '')
                break

    if agrupar_lado:
        for lado in lados:
            if (lado in produto_agrupado 
                and ' CLASSE E ' not in produto_agrupado 
                and ' PEUGEOT E ' not in produto_agrupado):
                produto_agrupado = produto_agrupado.replace(lado, ' ')
                break
            elif produto_agrupado.endswith((' E', ' D')):
                produto_agrupado = produto_agrupado[:-2]
                break
            elif produto_agrupado.endswith((' LE', ' LD')):
                produto_agrupado = produto_agrupado[:-3]
                break
            elif produto_agrupado.endswith(' LD/LE'):
                produto_agrupado = produto_agrupado[:-6]
                break

    produto_agrupado = produto_agrupado.replace(' EXC', '')

    if ' AMT' in produto_agrupado:
        if ' CNT' in produto_agrupado:
            produto_agrupado = produto_agrupado.replace(' AMT CNT', '')
        else:
            produto_agrupado = produto_agrupado.replace(' AMT AER', '')

    return produto_agrupado.strip()


def _agrupamento_retrovisor(produto_descricao, agrupar_marca=True, agrupar_lado=True):
    marcas_retrov = [' MTG/QXP',' MTG/VMAX',' MTG/PWAY',' MTG',' FCS',' VMAX',' SMR',' PWAY',
                     ' ORIGINAL',' F2J',' ARTEB*',' MEKRA',' HELLA',' TYC']
    lados = [' LD/LE ',' LE/LD ',' LE ',' LD ', ' E ', ' D ']

    casos_especificos = {
        'RETROV NISSAN FRONTIER LE 19/ CD ELET EXT CROM LD (CAM/PLED/RET) MTG',
        'ENC RETROV NISSAN FRONTIER LE 19/ CD ELET EXT CROM LD (CAM/LOGO/PLED/RET) ORIGINAL*'
    }

    if produto_descricao in casos_especificos:
        return produto_descricao.replace(' LD', '').strip()

    produto_agrupado = produto_descricao

    if agrupar_marca:
        for marca in marcas_retrov:
            if marca == ' ORIGINAL' and ' ORIGINAL*' in produto_agrupado:
                continue
            if marca in produto_agrupado:
                produto_agrupado = produto_agrupado.replace(marca, '')
                break

    if agrupar_lado:
        for lado in lados:
            if lado in produto_agrupado:
                produto_agrupado = produto_agrupado.replace(lado, ' ')
                break
            elif produto_agrupado.endswith((' E', ' D')):
                produto_agrupado = produto_agrupado[:-2]
                break
            elif produto_agrupado.endswith((' LE', ' LD')):
                produto_agrupado = produto_agrupado[:-3]
                break
            elif produto_agrupado.endswith(' LD/LE'):
                produto_agrupado = produto_agrupado[:-6]
                break

    produto_agrupado = produto_agrupado.replace(' EXC', '')

    if ' AMT' in produto_agrupado:
        if ' CNT' in produto_agrupado:
            produto_agrupado = produto_agrupado.replace(' AMT CNT', '')
        else:
            produto_agrupado = produto_agrupado.replace(' AMT AER', '')

    return produto_agrupado.strip()


def _agrupamento_farol_lanterna(produto_descricao, agrupar_marca=True, agrupar_lado=True):
    marcas_fl = [' IFCAR ARTEB',' VALEO/F2J',' MM',' CASP',' ARTEB',' TYC',' DEPO',
                 ' ORIGINAL',' F2J',' ARTEB*',' VALEO',' HELLA',' FITAM',' ORGUS']
    lados = [' LD/LE ',' LE/LD ',' LE ',' LD ', ' E ', ' D ']

    produto_agrupado = produto_descricao

    if agrupar_marca:
        for marca in marcas_fl:
            if marca == ' ORIGINAL' and ' ORIGINAL*' in produto_agrupado:
                continue
            if marca in produto_agrupado:
                produto_agrupado = produto_agrupado.replace(marca, '')
                break

    if agrupar_lado:
        for lado in lados:
            if lado in produto_agrupado:
                produto_agrupado = produto_agrupado.replace(lado, ' ')
                break
            elif produto_agrupado.endswith((' E', ' D')):
                produto_agrupado = produto_agrupado[:-2]
                break
            elif produto_agrupado.endswith((' LE', ' LD')):
                produto_agrupado = produto_agrupado[:-3]
                break
            elif produto_agrupado.endswith(' LD/LE'):
                produto_agrupado = produto_agrupado[:-6]

    produto_agrupado = produto_agrupado.replace(' EXC', '')

    if ' AMT' in produto_agrupado:
        if ' CNT' in produto_agrupado:
            produto_agrupado = produto_agrupado.replace(' AMT CNT', '')
        else:
            produto_agrupado = produto_agrupado.replace(' AMT AER', '')

    return produto_agrupado.strip()


def agrupar_produto(
    df: pd.DataFrame,
    coluna_origem: str,
    coluna_nova: str,
    agrupar_marca: bool = True,
    agrupar_lado: bool = True
) -> pd.DataFrame:
    """
    Agrupa descrições de produtos (vidro, retrovisor, farol/lanterna)
    criando uma nova coluna no DataFrame.
    """

    df = df.copy()

    def _aplicar(descricao):
        if pd.isna(descricao):
            return np.nan

        descricao = str(descricao)

        if 'VID ' in descricao:
            return _agrupamento_vidro(descricao, agrupar_marca, agrupar_lado)

        elif 'RETROV ' in descricao:
            return _agrupamento_retrovisor(descricao, agrupar_marca, agrupar_lado)

        elif 'FAROL ' in descricao or 'LANT ' in descricao:
            return _agrupamento_farol_lanterna(descricao, agrupar_marca, agrupar_lado)

        return descricao.strip()

    df[coluna_nova] = df[coluna_origem].apply(_aplicar)

    return df


# =========================
# Regex pré-compilados
# =========================
RE_BR_TAG = re.compile(r'(?i)<br\s*/?>')
RE_SPACES = re.compile(r'\s+')
RE_REMOVE_ALL_PUNCT = re.compile(r'[^a-zA-Z0-9\s]')
RE_KEEP_DOT_COMMA = re.compile(r'[^a-zA-Z0-9\s.,]')


# =========================
# Função base (string única)
# =========================
def _clean_text_str(
    text: str,
    case: str = "lower",
    mantem_pontuacao: bool = False
) -> str | None:
    import unidecode

    if not isinstance(text, str):
        return None

    # Normalização de símbolos específicos
    text = text.replace("°", "").replace("×", "")

    # Remove acentos
    text = unidecode.unidecode(text)

    # Remove quebras de linha e <br>
    text = text.replace("\n", " ").replace("\r", " ")
    text = RE_BR_TAG.sub(" ", text)

    # Filtragem de caracteres
    if mantem_pontuacao:
        text = RE_KEEP_DOT_COMMA.sub(" ", text)
    else:
        text = RE_REMOVE_ALL_PUNCT.sub(" ", text)

    # Padroniza espaços
    text = RE_SPACES.sub(" ", text).strip()

    # Case
    if case == "lower":
        text = text.lower()
    elif case == "upper":
        text = text.upper()

    return text if text else None


# =========================
# Função pública da biblioteca
# =========================
def limpar_texto(
    texto: Union[str, pl.Series, pl.Expr],
    case: str = "lower",
    mantem_pontuacao: bool = False
) -> Union[str, pl.Series, pl.Expr]:
    """
    Limpa e normaliza textos (string única ou coluna Polars).

    Parâmetros
    ----------
    texto : str | pl.Series | pl.Expr
        Texto ou coluna a ser tratada.
    case : {'lower', 'upper', None}
        Define o case do texto.
    mantem_pontuacao : bool
        Se True, mantém '.' e ','.

    Retorno
    -------
    str | pl.Series | pl.Expr
    """

    # Caso 1 — string simples
    if isinstance(texto, str):
        return _clean_text_str(texto, case, mantem_pontuacao)

    # Caso 2 — coluna Polars
    if isinstance(texto, (pl.Series, pl.Expr)):
        return texto.map_elements(
            lambda x: _clean_text_str(x, case, mantem_pontuacao),
            return_dtype=pl.Utf8
        )

    raise TypeError(
        "O parâmetro 'texto' deve ser str, pl.Series ou pl.Expr"
    )



def media_saneada(valores, min_amostras=3, cv_max=0.25):
    
    """
    Calcula a média saneada de um conjunto de valores numéricos.

    A função remove iterativamente valores fora do intervalo
    [média ± desvio padrão] até que o coeficiente de variação (CV)
    fique abaixo do limite definido ou o número mínimo de amostras
    seja atingido.

    Parâmetros
    ----------
    valores : array-like
        Lista, array NumPy ou pd.Series contendo valores numéricos.
    min_amostras : int, default=3
        Número mínimo de observações permitido.
    cv_max : float, default=0.25
        Coeficiente de variação máximo aceitável.

    Retorna
    -------
    float
        Média saneada ou mediana dos últimos `min_amostras` valores.
    """
    arr = np.asarray(valores, dtype=float)
    arr = arr[~np.isnan(arr)]

    n = arr.size
    if n < min_amostras:
        return float(np.median(arr))

    while True:
        media = arr.mean()
        desvio = arr.std()

        if media != 0 and (desvio / media) <= cv_max:
            return float(media)

        if n <= min_amostras:
            break

        li = media - desvio
        ls = media + desvio

        mask = (arr >= li) & (arr <= ls)
        novo_n = mask.sum()

        if novo_n < min_amostras:
            arr.sort()
            return float(np.median(arr[:min_amostras]))

        if novo_n == n:
            break

        arr = arr[mask]
        n = novo_n

    arr.sort()
    return float(np.median(arr[:min_amostras]))

def _media_saneada_worker(key, valores, min_amostras, cv_max):
    return (*key, media_saneada(valores, min_amostras, cv_max))


def media_saneada_groupby(
    df,
    group_cols,
    value_col,
    min_amostras=3,
    cv_max=0.25,
    n_jobs=-1,
    output_col="media_saneada"
):
    from joblib import Parallel, delayed
    
    """
    Aplica a média saneada por grupo em um DataFrame,
    utilizando paralelização por múltiplos processos.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame de entrada.
    group_cols : list[str]
        Colunas utilizadas para o agrupamento.
    value_col : str
        Coluna numérica sobre a qual será calculada a média saneada.
    min_amostras : int, default=3
        Número mínimo de observações permitido por grupo.
    cv_max : float, default=0.25
        Coeficiente de variação máximo aceitável.
    n_jobs : int, default=-1
        Número de processos paralelos. -1 utiliza todos os cores.
    output_col : str, default="media_saneada"
        Nome da coluna de saída.

    Retorna
    -------
    pd.DataFrame
        DataFrame agregado com a média saneada por grupo.
    """
    grouped = df.groupby(group_cols, sort=False)[value_col]

    results = Parallel(
        n_jobs=n_jobs,
        backend="loky",
        prefer="processes"
    )(
        delayed(_media_saneada_worker)(
            key,
            group.values,
            min_amostras,
            cv_max
        )
        for key, group in grouped
    )

    return pd.DataFrame(
        results,
        columns=[*group_cols, output_col]
    )



def extrair_intervalo_ano_modelo(
    col: pl.Expr,
    ano_atual: int | None = None,
    nome_inicio: str = "Ano Modelo Inicial",
    nome_fim: str = "Ano Modelo Final",
) -> list[pl.Expr]:

    import polars as pl
    from datetime import datetime

    if ano_atual is None:
        ano_atual = datetime.now().year

    # Regex SEM lookahead (compatível com Polars)
    regex = r"(\d{2})\s*/\s*(\d{2})?(?:\s|$)"

    # Bloqueio por prefixo
    bloqueado = (
        col.str.to_uppercase().str.starts_with("PNEU")
        | col.str.to_uppercase().str.starts_with("CALOTA")
    )

    # ---------- Ano inicial ----------
    ano_ini_raw = (
        pl.when(bloqueado)
        .then(None)
        .otherwise(col.str.extract(regex, 1))
        .cast(pl.Int32)
    )

    ano_inicio = (
        pl.when(ano_ini_raw.is_not_null())
        .then(
            pl.when(ano_ini_raw >= 50)
            .then(1900 + ano_ini_raw)
            .otherwise(2000 + ano_ini_raw)
        )
        .otherwise(None)
        .alias(nome_inicio)
    )

    # ---------- Ano final ----------
    ano_fim_raw = (
        pl.when(bloqueado)
        .then(None)
        .otherwise(col.str.extract(regex, 2))
        .cast(pl.Int32)
    )

    ano_fim = (
        pl.when(ano_ini_raw.is_null())
        .then(None)
        .when(ano_fim_raw.is_null())
        .then(ano_atual)
        .when(ano_fim_raw >= 50)
        .then(1900 + ano_fim_raw)
        .otherwise(2000 + ano_fim_raw)
        .alias(nome_fim)
    )

    return [ano_inicio, ano_fim]
