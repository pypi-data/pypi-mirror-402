import polars as pl

def escolha_variaveis(*args, **kwargs):
    """
    Wrapper para carregar a implementação pesada sob demanda.
    """
    try:
        from ._selecao_variavel_impl import escolha_variaveis as _impl
    except ImportError as e:
        raise ImportError(
            "A função escolha_variaveis requer dependências opcionais de ML.\n"
            "Instale com: pip install maxsciencelib[selecao_variavel]"
        ) from e

    return _impl(*args, **kwargs)


def time_features(df: pl.DataFrame, ts_col: str) -> pl.DataFrame:
    """
    Cria um conjunto de features de data e hora a partir de uma coluna de timestamp.
    Inclui features básicas, feriados no Brasil, e encoding cíclico para mês e dia da semana.
    """
    import polars as pl
    import numpy as np
    from datetime import datetime, timedelta

    from holidays import Brazil

    # Calendário de feriados do Brasil
    cal = Brazil()

    # Converter coluna de timestamp para Datetime e renomear
    df = df.with_columns(
        pl.col(ts_col).cast(pl.Datetime).alias("ts")
    )

    # Extrair atributos de data e hora básicos
    df = df.with_columns([
        pl.col("ts").dt.month().alias("mes"),          # 1–12
        pl.col("ts").dt.day().alias("dia"),            # 1–31
        pl.col("ts").dt.weekday().alias("dia_semana"), # 1=Segunda, …,7=Domingo (Ajustado abaixo)
        pl.col("ts").dt.hour().alias("hora"),          # 0–23
        pl.col("ts")
          .dt.date()
          .map_elements(lambda dt: cal.is_holiday(dt), return_dtype=pl.Boolean)
          .alias("feriado")
    ])

    # Indicar fim de semana (sábado/domingo)
    df = df.with_columns(
        (pl.col("dia_semana") >= 5).alias("fim_de_semana")
    )

    # Encoding cíclico
    df = df.with_columns([
        (2 * np.pi * pl.col("mes") / 12).sin().alias("mes_sin"),
        (2 * np.pi * pl.col("mes") / 12).cos().alias("mes_cos"),
        (2 * np.pi * pl.col("dia_semana") / 7).sin().alias("dow_sin"),
        (2 * np.pi * pl.col("dia_semana") / 7).cos().alias("dow_cos")
    ])

    # Definir período do dia: madrugada/manhã/tarde/noite
    df = df.with_columns(
        pl.when(pl.col("hora") < 6)
          .then(pl.lit("madrugada"))
        .when(pl.col("hora") < 12)
          .then(pl.lit("manhã"))
        .when(pl.col("hora") < 18)
          .then(pl.lit("tarde"))
        .otherwise(pl.lit("noite"))
        .alias("periodo_dia")
    )

    # Remover coluna temporária e retornar
    return df.drop("ts")