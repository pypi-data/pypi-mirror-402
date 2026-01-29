import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import ks_2samp


def _plotar_degradacao(
    df_metricas: pd.DataFrame,
    top_n: int,
    window: int,
    ks_ref: float,
    psi_ref: float
):
    df = df_metricas.copy()
    df["periodo"] = pd.to_datetime(df["periodo"])

    ranking = (
        df.groupby("variavel")["KS"]
        .mean()
        .sort_values(ascending=False)
        .head(top_n)
        .index
    )

    for var in ranking:
        d = (
            df[df["variavel"] == var]
            .groupby("periodo", as_index=False)
            .agg({
                "KS": "mean",
                "PSI": "mean"
            })
            .sort_values("periodo")
        )

        d["KS_MA"] = d["KS"].rolling(window, min_periods=1).mean()
        d["PSI_MA"] = d["PSI"].rolling(window, min_periods=1).mean()

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=d["periodo"],
                y=d["KS_MA"],
                name="KS (MM)",
                line=dict(width=3)
            ),
            secondary_y=False
        )

        fig.add_trace(
            go.Scatter(
                x=d["periodo"],
                y=d["PSI_MA"],
                name="PSI (MM)",
                line=dict(width=3)
            ),
            secondary_y=True
        )

        fig.add_hline(y=ks_ref, line_dash="dash", secondary_y=False)
        fig.add_hline(y=psi_ref, line_dash="dash", secondary_y=True)

        fig.update_layout(
            title=f"Monitoramento de Degradação — <b>{var}</b>",
            template="plotly_white",
            legend=dict(
                orientation="h",
                y=-0.25,
                x=0.5,
                xanchor="center"
            )
        )

        fig.update_yaxes(title_text="KS", range=[0, 1], secondary_y=False)
        fig.update_yaxes(title_text="PSI", secondary_y=True)

        fig.show()


def monitorar_degradacao(
    df: pd.DataFrame,
    data_col: str,
    target_col: str,
    excluir: list[str] | None = None,
    bins: int = 20,
    top_n: int = 10,
    window: int = 7,
    ks_ref: float = 0.30,
    psi_ref: float = 0.25,
    plotar: bool = True
) -> pd.DataFrame:
    """
    Calcula métricas de degradação (KS e PSI) ao longo do tempo e,
    opcionalmente, gera gráficos de monitoramento.

    Retorna sempre um DataFrame com as métricas.
    """

    df = df.copy()
    df[data_col] = pd.to_datetime(df[data_col])

    excluir = (excluir or []) + [data_col]
    num_cols = df.select_dtypes(include=[np.number]).columns.difference(excluir + [target_col])

    periodos = sorted(df[data_col].unique())
    metricas = []

    for col in num_cols:
        serie_total = df[col].dropna()
        if serie_total.empty:
            continue

        _, bins_edges = np.histogram(serie_total, bins=bins)

        # Base de referência = primeiro período
        base_vals = df.loc[df[data_col] == periodos[0], col].dropna()
        base_counts, _ = np.histogram(base_vals, bins=bins_edges)
        p_base = (base_counts + 0.5) / (base_counts.sum() + 0.5 * bins)

        for periodo in periodos:
            df_p = df.loc[df[data_col] == periodo, [col, target_col]].dropna()
            if df_p.empty:
                continue

            pos = df_p.loc[df_p[target_col] == 1, col]
            neg = df_p.loc[df_p[target_col] == 0, col]

            ks = (
                ks_2samp(pos, neg)[0]
                if len(pos) > 5 and len(neg) > 5
                else np.nan
            )

            cur_counts, _ = np.histogram(df_p[col], bins=bins_edges)
            p_cur = (cur_counts + 0.5) / (cur_counts.sum() + 0.5 * bins)

            psi = np.sum((p_cur - p_base) * np.log(p_cur / p_base))

            metricas.append({
                "periodo": periodo,
                "variavel": col,
                "KS": ks,
                "PSI": psi
            })

    df_metricas = pd.DataFrame(metricas)

    if plotar:
        _plotar_degradacao(
            df_metricas,
            top_n=top_n,
            window=window,
            ks_ref=ks_ref,
            psi_ref=psi_ref
        )

    return df_metricas
