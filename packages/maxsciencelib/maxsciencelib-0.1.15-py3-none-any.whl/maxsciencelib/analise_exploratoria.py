import numpy as np
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt

def relatorio_modelo(model, X_test, y_test, nome_modelo="Modelo", decil=10, threshold=0.5):
    import matplotlib.pyplot as plt
    import seaborn as sns

    from sklearn.metrics import (
        roc_curve,
        roc_auc_score,
        confusion_matrix,
        accuracy_score,
        recall_score,
        precision_score,
        f1_score,
        log_loss,
        brier_score_loss
    )

    

    sns.set_theme(style="whitegrid")

    # Predições
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= threshold).astype(int)

    df_pred = X_test.copy()
    df_pred['acionou'] = y_test
    df_pred['pred'] = y_pred
    df_pred['score'] = y_pred_proba

    # ROC
    fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
    roc_auc = roc_auc_score(y_test, y_pred_proba)

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    # Métricas
    acc = accuracy_score(y_test, y_pred)
    sens = recall_score(y_test, y_pred)
    spec = tn / (tn + fp)
    ppv = precision_score(y_test, y_pred)
    npv = tn / (tn + fn)
    f1 = f1_score(y_test, y_pred)
    brier = brier_score_loss(y_test, y_pred_proba)

    # Layout
    fig, axs = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(f'Avaliação do Modelo - {nome_modelo}', fontsize=18, fontweight='bold')

    # 1. Curva ROC
    axs[0, 0].plot(fpr, tpr, label=f'AUC = {roc_auc:.3f}')
    axs[0, 0].plot([0, 1], [0, 1], 'k--', label='Aleatório')
    axs[0, 0].set_title('Curva ROC')
    axs[0, 0].set_xlabel('False Positive Rate')
    axs[0, 0].set_ylabel('True Positive Rate')
    axs[0, 0].grid(False)
    axs[0, 0].legend()

    # 2. Matriz de confusão
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False, ax=axs[0, 1])
    axs[0, 1].set_title('Matriz de Confusão')
    axs[0, 1].set_xlabel('Predito')
    axs[0, 1].set_ylabel('Real')

    # 3. Histograma com densidade
    axs[1, 0].set_title('Distribuição dos Scores (Probabilidades)')
    sns.histplot(y_pred_proba, bins=30, kde=True, ax=axs[1, 0], color='skyblue')
    axs[1, 0].axvline(threshold, color='red', linestyle='--', label=f'Threshold = {threshold}')
    axs[1, 0].legend()
    axs[1, 0].set_xlabel('Score')
    axs[1, 0].set_ylabel('Frequência')

    # 4. Precisão por Decil
    df_total = df_pred.copy()

    df_total['Decil'], bins = pd.qcut(
        df_total['score'].rank(method='first'),
        decil,
        labels=range(1, decil + 1),
        retbins=True
    )

    score_bins = np.quantile(df_total['score'], np.linspace(0, 1, decil + 1))
    x_labels = [f"{i}\n({score_bins[i]:.2f})" for i in range(1, decil + 1)]

    # 2. Agrupamento
    decil_agg = (
    df_total
    .groupby('Decil', observed=True)
    .agg(
        total_observacoes=('score', 'count'),
        efetivos=('acionou', 'sum')
    )
    .reset_index()
)


    decil_agg['precisao'] = decil_agg['efetivos'] / decil_agg['total_observacoes']

    # 3. Plotagem
    axs[1, 1].plot(
        decil_agg['Decil'].astype(int),
        decil_agg['precisao'],
        marker='o', linestyle='-', color='tab:blue', label='Precisão por Decil', zorder=3
    )

    # Rótulos de %
    for x, y in zip(decil_agg['Decil'].astype(int), decil_agg['precisao']):
        axs[1, 1].text(x, y + (max(decil_agg['precisao'])*0.05), f"{y:.1%}", ha='center', fontsize=10)

    # 4. Linha Vertical do Limiar (Threshold)
    try:
        # Localiza o decil onde o threshold se encaixa
        decil_threshold = np.digitize(threshold, score_bins)
        axs[1, 1].axvline(
            x=decil_threshold, 
            color='red', 
            linestyle='--', 
            alpha=0.7,
            label=f'Limiar de Decisão ({threshold:.2f})'
        )
    except NameError:
        print("Variável 'threshold' não definida. Linha vertical não plotada.")

    # 5. Linhas de Referência Horizontais
    taxa_fraude_base = y_test.mean()
    axs[1, 1].axhline(
        taxa_fraude_base,
        color='black', linestyle=':', alpha=0.6,
        label=f'Taxa Global = {taxa_fraude_base:.3f}'
    )

    # Configurações de Eixo
    axs[1, 1].set_title('Precisão por Decil e Pontos de Corte')
    axs[1, 1].set_xlabel('Decil (Valor Mínimo do Score)')
    axs[1, 1].set_ylabel('Precisão')
    axs[1, 1].set_xticks(range(1, decil + 1))
    axs[1, 1].set_xticklabels(x_labels) # Aplica os rótulos com valores de score
    axs[1, 1].set_ylim(0, max(decil_agg['precisao'].max() * 1.2, 0.2))
    axs[1, 1].legend(fontsize='small')
    axs[1, 1].grid(True, alpha=0.2)

    plt.tight_layout()
    plt.show()

    # Relatório textual simplificado
    print(f"\n📋 Relatório de Classificação - {nome_modelo}")
    print(f"Threshold aplicado: {threshold}")
    print(f"Acurácia       : {acc:.4f}")
    print(f"Sensibilidade  : {sens:.4f}")
    print(f"Especificidade : {spec:.4f}")
    print(f"PPV (Precisão) : {ppv:.4f}")
    print(f"NPV            : {npv:.4f}")
    print(f"F1 Score       : {f1:.4f}")
    print(f"AUC ROC        : {roc_auc:.4f}")
    print(f"Log Loss       : {log_loss(y_test, y_pred_proba):.4f}")
    print(f"Brier Score    : {brier:.4f}")
    

def plot_ks_colunas(df: pl.DataFrame, lista_colunas: list, coluna_target: str):
    import math
    import matplotlib.pyplot as plt
    import seaborn as sns

    from scipy.stats import ks_2samp

    n_colunas = len(lista_colunas)
    if n_colunas == 0:
        print("A lista de colunas está vazia.")
        return

    # Define o layout da grade de plots (no máximo 2 colunas de largura)
    ncols = 2 if n_colunas > 1 else 1
    nrows = math.ceil(n_colunas / ncols)

    fig, axes = plt.subplots(nrows, ncols, figsize=(8 * ncols, 6 * nrows))
    sns.set_theme(style="whitegrid")

    # Garante que 'axes' seja sempre um array iterável (útil para n_colunas=1)
    if n_colunas > 1:
        axes = axes.flatten()
    else:
        axes = [axes]

    for i, coluna_plot in enumerate(lista_colunas):
        ax = axes[i]

        # Separa os dados pelos valores da coluna target
        grupo_0 = df.filter(pl.col(coluna_target) == 0)[coluna_plot].drop_nulls()
        grupo_1 = df.filter(pl.col(coluna_target) == 1)[coluna_plot].drop_nulls()
        
        # Verifica se há dados suficientes em ambos os grupos
        if grupo_0.is_empty() or grupo_1.is_empty():
            ax.text(0.5, 0.5, f'Dados insuficientes para\n"{coluna_plot}"', 
                    ha='center', va='center', fontsize=12)
            ax.set_title(f'{coluna_plot}')
            continue

        count_0 = grupo_0.len()
        count_1 = grupo_1.len()
        
        # Calcula a estatística KS
        ks_stat = ks_2samp(grupo_0.to_numpy(), grupo_1.to_numpy()).statistic

        # Plota o gráfico de densidade
        sns.kdeplot(data=df.to_pandas(), x=coluna_plot, hue=coluna_target, 
                    fill=True, ax=ax, palette="viridis", common_norm=False)
        
        ax.set_title(f'{coluna_plot} (KS = {ks_stat:.4f})', fontsize=14)
        ax.set_xlabel(coluna_plot, fontsize=12)
        
        # Adiciona o label do eixo Y apenas para os gráficos da primeira coluna
        if i % ncols == 0:
            ax.set_ylabel('Densidade', fontsize=12)
        else:
            ax.set_ylabel('')

        # Atualiza o texto da legenda com a contagem de amostras
        legend = ax.get_legend()
        if legend and len(legend.texts) >= 2:
            legend.texts[0].set_text(f'0 (n={count_0})')
            legend.texts[1].set_text(f'1 (n={count_1})')

    # Oculta eixos não utilizados se o número de plots for ímpar
    for j in range(n_colunas, len(axes)):
        axes[j].axis('off')

    fig.suptitle(f'Comparação de Distribuições por "{coluna_target}"', fontsize=18, y=1.03)
    plt.tight_layout()
    plt.show()
 

def plot_lift_barplot(df, category_col, split_col, target_val=1, min_target_count=1, order=None, rename_map=None, template='plotly_white'):
    import plotly.graph_objects as go

    # Divide o DataFrame nos dois grupos
    df_base = df
    df_target = df[df[split_col] == target_val]

    # Calcula as frequências normalizadas para cada grupo
    prop_base   = df_base[category_col].value_counts(normalize=True)
    prop_target = df_target[category_col].value_counts(normalize=True)

    # Calcula a contagem absoluta no grupo de interesse (para o filtro)
    count_target = df_target[category_col].value_counts()

    # Junta tudo em um DataFrame para cálculo do lift
    df_lift = pd.concat([prop_base, prop_target, count_target], axis=1, keys=['base', 'target', 'count_target']).fillna(0)
    
    # Calcula o lift, tratando divisão por zero ou NaN
    df_lift['lift'] = (df_lift['target'] / df_lift['base']).replace([np.inf, -np.inf, np.nan], 0)

    # Aplica o filtro de contagem mínima
    df_lift = df_lift[df_lift['count_target'] >= min_target_count]

    # Ordena o resultado
    if order:
        df_lift = df_lift.reindex(order).fillna(0)
    else:
        df_lift = df_lift.sort_values(by='lift', ascending=False)

    # Renomeia as categorias se um mapa for fornecido
    x_labels = [rename_map.get(v, v) if rename_map else str(v) for v in df_lift.index]

    # Plota o gráfico
    fig = go.Figure()
    fig.add_bar(
        x=x_labels,
        y=df_lift['lift'],
        marker_color='steelblue',
        name='Lift'
    )

    fig.update_layout(
        title=f"Lift de {category_col}",
        xaxis_title=f"{category_col}",
        yaxis_title=f"Lift",
        yaxis_tickformat=".2f",
        template=template,
        bargap=0.3
    )

    return fig


def plot_correlacoes(df: pd.DataFrame, target: str, corr_thresh: float = 0.9):
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.feature_selection import mutual_info_classif

    assert target in df.columns, f"Target {target} não encontrado no DataFrame"

    # Matriz de correlação entre features
    corr_matrix = df.drop(columns=[target]).corr(method="pearson")
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, cmap="coolwarm", center=0, annot=False)
    plt.title("Matriz de Correlação (Pearson)")
    plt.show()

    # Correlação com o target
    corr_pearson = df.corr(method="pearson")[target].drop(target)
    corr_spearman = df.corr(method="spearman")[target].drop(target)

    # MI
    y = df[target]
    X = df.drop(columns=[target])
    mi = mutual_info_classif(X, y, random_state=42)
    corr_mi = pd.Series(mi, index=X.columns)

    resumo = pd.DataFrame({
        "Pearson_vs_target": corr_pearson,
        "Spearman_vs_target": corr_spearman,
        "MutualInfo_vs_target": corr_mi
    }).sort_values("MutualInfo_vs_target", ascending=False)

    # Pares correlacionados entre si
    redundancias = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i):
            if abs(corr_matrix.iloc[i, j]) >= corr_thresh:
                redundancias.append((
                    corr_matrix.index[i],
                    corr_matrix.columns[j],
                    corr_matrix.iloc[i, j]
                ))

    redundancias = pd.DataFrame(redundancias, columns=["var1", "var2", "corr_abs"])
    redundancias["corr_abs"] = redundancias["corr_abs"].abs()
    redundancias = redundancias.sort_values("corr_abs", ascending=False).reset_index(drop=True)

    return resumo, redundancias
 
