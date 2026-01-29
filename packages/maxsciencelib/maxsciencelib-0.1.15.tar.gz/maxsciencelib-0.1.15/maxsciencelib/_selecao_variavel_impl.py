import shap
import optuna
import pandas as pd
import numpy as np
import polars as pl
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, OneHotEncoder, MinMaxScaler, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc
import lightgbm as lgb
from tqdm import tqdm
from joblib import dump
import matplotlib.pyplot as plt
from imblearn.pipeline import Pipeline as ImbPipeline
import os
import polars.selectors as cs
from scipy.stats import permutation_test, ks_2samp
from collections import Counter
from scipy.stats import ttest_ind
from scipy.stats import chi2_contingency
from sklearn.base import clone
from sklearn.base import BaseEstimator, TransformerMixin
import warnings
from lightgbm import LGBMClassifier
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.metrics import (
    roc_auc_score,
    accuracy_score,
    f1_score,
    brier_score_loss
)
import re

### Funções bases

# Função de TVD
def total_variation_distance(p, q):
    return 0.5 * np.sum(np.abs(p - q))

def safe_normalize(x):
    total = np.sum(x)
    if total == 0 or np.isnan(total):
        return np.zeros_like(x, dtype=float)
    return x / total

def tvd_p_value(data1, data2, n_permutations=10000):
    p1 = safe_normalize(np.array(data1, dtype=float))
    p2 = safe_normalize(np.array(data2, dtype=float))
    observed_tvd = total_variation_distance(p1, p2)

    def statistic(x, y):
        return total_variation_distance(safe_normalize(x), safe_normalize(y))

    res = permutation_test((data1, data2), statistic, n_resamples=n_permutations)
    return res.pvalue

# Teste KS
def ks_test(dist1, dist2):

    res = ks_2samp(dist1,dist2)
    stat = res[0]
    pval = res[1]

    return stat, pval

## função de split aleatório
def split_treino_teste_aleatorio(base, test_size=0.2, seed=42):
    # Adiciona uma coluna aleatória
    base_random = base.with_columns(
        pl.lit(np.random.RandomState(seed).rand(base.height)).alias("random_split")
    )
    # Split
    base_treino = base_random.filter(pl.col("random_split") > test_size).drop("random_split")
    base_teste = base_random.filter(pl.col("random_split") <= test_size).drop("random_split")

    prop_treino = base_treino.height / base.height
    prop_teste = 1 - prop_treino

    print(f'A proporção de treino/teste (aleatória) é {prop_treino:.2%} / {prop_teste:.2%}')
    
    # Split interno (t1, t2) no treino
    t1, t2 = split_df(base_treino, seed=seed)
    if t1.height != t2.height:
        t2 = t2[:t1.height]

    return t1, t2, base_teste

# Função de split DataFrame
def split_df(df, seed=None, test_size=0.5):
    return df.with_columns(
        pl.int_range(pl.len(), dtype=pl.UInt32)
        .shuffle(seed)
        .gt(pl.len() * test_size)
        .alias("split")
    ).partition_by("split", include_key=False)

# Função de segmentação da base por data
def split_treino_teste_temporal(base, coluna_data_ref, max_periodo_treino = 202307, split_treino = True):
    
    # Split do treino
    base_treino = (
        base
        .with_columns(
            (pl.col(coluna_data_ref).dt.year().cast(pl.String) + pl.col(coluna_data_ref).dt.month().cast(pl.String).str.zfill(2)).cast(pl.Int64).alias('PERIODO')
        )
        .filter(pl.col('PERIODO') <= max_periodo_treino)
    ).drop('PERIODO')

    # Split do teste
    base_teste = (
        base
        .with_columns(
            (pl.col(coluna_data_ref).dt.year().cast(pl.String) + pl.col(coluna_data_ref).dt.month().cast(pl.String).str.zfill(2)).cast(pl.Int64).alias('PERIODO')
        )
        .filter(pl.col('PERIODO') > max_periodo_treino)
    ).drop('PERIODO')

    prop_treino = base_treino.height/base.height
    prop_teste = 1 - prop_treino

    print(f'A proporção de treino/teste temporal é {prop_treino:.2%} / {prop_teste:.2%}')

    if split_treino == True:
        t1, t2 = split_df(base_treino)
        if t1.height != t2.height:
            t2 = t2[:t1.height]

        return t1, t2, base_teste
    else:
        return base_treino, base_teste

# Função auxiliar para normalizar tipo da chave
def _normalize_key(df, var):
    dtype = df.schema[var]
    if dtype.is_integer():
        # se for inteiro muito grande, converte para Int64
        return df.with_columns(pl.col(var).cast(pl.Int64))
    else:
        # senão converte para string
        return df.with_columns(pl.col(var).cast(pl.Utf8))

# Função - Calcula TVD entre T1 e T2
def total_variation_t1t2(base, var, t1, t2):
    all_vars = base[[var]].unique()
    all_vars = _normalize_key(all_vars, var)

    a = t1[var].value_counts(normalize=True)
    a = _normalize_key(a, var)
    a = all_vars.join(a, how='left', on=var).fill_null(0).sort(by=var)['proportion'].to_numpy()

    b = t2[var].value_counts(normalize=True)
    b = _normalize_key(b, var)
    b = all_vars.join(b, how='left', on=var).fill_null(0).sort(by=var)['proportion'].to_numpy()

    # 🚨 Verificação adicionada — evita erro se há poucas observações
    if len(a) < 2 or len(b) < 2 or a.sum() == 0 or b.sum() == 0:
        tvd_t1t2 = total_variation_distance(a, b)
        tvd_t1t2_pval = None  # ou 1.0 se quiser indicar “sem diferença”
        return tvd_t1t2, tvd_t1t2_pval

    # Cálculo normal se as amostras são válidas
    tvd_t1t2 = total_variation_distance(a, b)
    tvd_t1t2_pval = tvd_p_value(a, b, 10000)

    return tvd_t1t2, tvd_t1t2_pval

# Função - Calcula TVD para o target
def total_variation_target(base, var, t1, t2, target):
    def _dist(df1, df2, all_vars, var):
        df1 = _normalize_key(df1[var].value_counts(normalize=True), var)
        df2 = _normalize_key(df2[var].value_counts(normalize=True), var)
        all_vars = _normalize_key(all_vars, var)
        a = all_vars.join(df1, how='left', on=var).fill_null(0).sort(by=var)['proportion'].to_numpy()
        b = all_vars.join(df2, how='left', on=var).fill_null(0).sort(by=var)['proportion'].to_numpy()
        return a, b

    # --- T1 ---
    t1t = t1.filter(pl.col(target) == True)
    t1f = t1.filter(pl.col(target) == False)
    all_vars = base[[var]].unique()
    a, b = _dist(t1t, t1f, all_vars, var)

    # 🚨 Verificação adicionada para evitar erro de amostras pequenas
    if len(a) < 2 or len(b) < 2 or a.sum() == 0 or b.sum() == 0:
        tvd_t1 = total_variation_distance(a, b)
        tvd_p_t1 = None  # ou 1.0 para indicar "sem diferença"
    else:
        tvd_t1 = total_variation_distance(a, b)
        tvd_p_t1 = tvd_p_value(a, b, 1000)

    # --- T2 ---
    t2t = t2.filter(pl.col(target) == True)
    t2f = t2.filter(pl.col(target) == False)
    all_vars = base[[var]].unique()
    a, b = _dist(t2t, t2f, all_vars, var)

    # 🚨 Mesmo tratamento para T2
    if len(a) < 2 or len(b) < 2 or a.sum() == 0 or b.sum() == 0:
        tvd_t2 = total_variation_distance(a, b)
        tvd_p_t2 = None
    else:
        tvd_t2 = total_variation_distance(a, b)
        tvd_p_t2 = tvd_p_value(a, b, 1000)

    # --- Q Factor ---
    q_factor = (tvd_t2 + tvd_t1) / (np.abs(tvd_t2 - tvd_t1) + 0.00001)

    return (tvd_t1, tvd_p_t1), (tvd_t2, tvd_p_t2), q_factor

# Função - Calcula KS entre T1 e T2:
def ks_t1t2(var, t1, t2):

    a = t1.drop_nulls(subset=var)[var].to_numpy()
    b = t2.drop_nulls(subset=var)[var].to_numpy()

    ks_t1t2, ks_t1t2_pval = ks_test(a,b)

    return ks_t1t2, ks_t1t2_pval

# Função - Calcula KS para o Target
def ks_target(var, t1, t2,target):

    t1t = t1.drop_nulls(subset=var).filter(pl.col(target)==True)
    t1f = t1.drop_nulls(subset=var).filter(pl.col(target)==False)

    t2t = t2.drop_nulls(subset=var).filter(pl.col(target)==True)
    t2f = t2.drop_nulls(subset=var).filter(pl.col(target)==False)

    a = t1t[var].to_numpy()
    b = t1f[var].to_numpy()

    ks_t1, ks_t1pval = ks_test(a,b)

    a = t2t[var].to_numpy()
    b = t2f[var].to_numpy()

    ks_t2, ks_t2pval = ks_test(a,b)

    q_factor = (ks_t2 + ks_t1)/(np.abs(ks_t2 - ks_t1)+0.00001)

    return (ks_t1, ks_t1pval),(ks_t2, ks_t2pval), q_factor

from scipy.stats import chi2_contingency

def teste_quiquadrado(data: pl.DataFrame, var: str, target: str) -> float:
    # Cria a tabela de contingência
    df = data.select([var, target]).to_pandas()
    contingencia = pd.crosstab(df[var], df[target])

    # Calcula o p-valor
    try:
        _, p_value, _, _ = chi2_contingency(contingencia)
        return p_value
    except:
        return None  # Pode falhar com valores únicos ou vazios
    
from scipy.stats import ttest_ind

def teste_t_student(data: pl.DataFrame, var: str, target: str) -> float:
    df = data.select([var, target]).to_pandas()

    # Separa por classe
    grupo_0 = df[df[target] == 0][var].dropna()
    grupo_1 = df[df[target] == 1][var].dropna()

    # Teste T
    try:
        _, p_value = ttest_ind(grupo_0, grupo_1, equal_var=False)
        return p_value
    except:
        return None


### Split aleatório

def split_aleatorio_fun(X, y, prop_treino=0.8, random_state=42):
    """
    Faz split aleatório baseado na proporção de treino total desejada.
    
    Retorna: 
    X_temp, X_test, y_temp, y_test, X_train, X_val, y_train, y_val
    """
    # Test size é o que falta para prop_treino (ex: 0.2 se prop_treino=0.8)
    test_size = 1 - prop_treino
    # Dentro do X_temp, qual fração será validação? 25% (de acordo com seu exemplo original)
    val_size = 0.25  # 25% de X_temp vira validação, 75% vira treino
    
    # Split base total em treino+validação vs teste
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state
    )

    # Split de treino+validação em treino e validação
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_size, stratify=y_temp, random_state=random_state
    )

    return X_temp, X_test, y_temp, y_test, X_train, X_val, y_train, y_val

### Split temporal

def split_temporal(base, coluna_data_ref, target, remover=[], max_periodo_treino=202307):
    base = base.copy()

    # Cria coluna PERIODO no formato YYYYMM
    base['PERIODO'] = base[coluna_data_ref].dt.year * 100 + base[coluna_data_ref].dt.month

    # Remove colunas se existirem
    base = base.drop(columns=[col for col in remover if col in base.columns])

    # Split em base_temp (treino + val) e base_test
    base_temp = base[base['PERIODO'] <= max_periodo_treino].drop(columns='PERIODO')
    base_test = base[base['PERIODO'] > max_periodo_treino].drop(columns='PERIODO')

    # y e X para treino + val e teste
    y_temp = base_temp[target]
    X_temp = base_temp.drop(columns=[target])

    y_test = base_test[target]
    X_test = base_test.drop(columns=[target, coluna_data_ref], errors='ignore')

    # Ordena base_temp por data
    base_temp_sorted = base_temp.sort_values(by=coluna_data_ref)

    # Divide em treino e validação: 75% / 25%
    corte = int(len(base_temp_sorted) * 0.75)
    treino = base_temp_sorted.iloc[:corte]
    val = base_temp_sorted.iloc[corte:]

    y_train = treino[target]
    X_train = treino.drop(columns=[target, coluna_data_ref], errors='ignore')

    y_val = val[target]
    X_val = val.drop(columns=[target, coluna_data_ref], errors='ignore')

    return X_temp, X_test, y_temp, y_test, X_train, X_val, y_train, y_val

### STEPS

class StepLabelEncode(BaseEstimator, TransformerMixin):
        def __init__(self, columns):
            self.columns = columns
            self.encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)

        def fit(self, X, y=None):
            self.encoder.fit(X[self.columns])
            return self

        def transform(self, X):
            X = X.copy()
            X[self.columns] = self.encoder.transform(X[self.columns]).astype(int)
            return X
        
class StepDummy(BaseEstimator, TransformerMixin):
        def __init__(self, columns):
            self.columns = columns
            self.dummy_columns = None

        def fit(self, X, y=None):
            X_dummies = pd.get_dummies(X, columns=self.columns, drop_first=False)
            self.dummy_columns = X_dummies.columns
            return self

        def transform(self, X):
            X_dummies = pd.get_dummies(X, columns=self.columns, drop_first=False)

            # Descobre quais colunas estão faltando
            missing_cols = [col for col in self.dummy_columns if col not in X_dummies]

            # Adiciona todas de uma vez
            if missing_cols:
                missing_df = pd.DataFrame(0, index=X_dummies.index, columns=missing_cols)
                X_dummies = pd.concat([X_dummies, missing_df], axis=1)

            # Garante a mesma ordem de colunas
            return X_dummies[self.dummy_columns]

class StepNormalize(BaseEstimator, TransformerMixin):
        def __init__(self, columns):
            self.columns = columns

        def fit(self, X, y=None):
            self.means = X[self.columns].mean()
            self.stds = X[self.columns].std().replace(0, 1)
            return self

        def transform(self, X):
            X = X.copy()
            X[self.columns] = (X[self.columns] - self.means) / self.stds
            return X

        
class StepOrdinalEncode(BaseEstimator, TransformerMixin):
    def __init__(self, columns=None):
        self.columns = columns
        self.encoder = None
        self.columns_ = None

    def fit(self, X, y=None):
        if self.columns is None:
            self.columns_ = X.select_dtypes(include=['object', 'category']).columns.tolist()
        else:
            self.columns_ = self.columns

        self.encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
        self.encoder.fit(X[self.columns_])
        return self

    def transform(self, X):
        X = X.copy()
        X[self.columns_] = self.encoder.transform(X[self.columns_])
        return X
    
class CleanFeatureNames(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        X.columns = [re.sub(r'[^0-9A-Za-z_]+', '_', c) for c in X.columns]
        return X
    
def agrupar_importancia_por_variavel_original(X_train, shap_values, categoricas, numericas):

    # 1. Aplicar StepOrdinalEncode e StepDummy
    X_tmp = X_train.copy()

    # Aplicar transformações
    # step_ordinal = StepOrdinalEncode(columns=categoricas).fit(X_tmp)
    # X_encoded = step_ordinal.transform(X_tmp)

    step_dummy = StepDummy(columns=categoricas).fit(X_tmp)
    X_dummies = step_dummy.transform(X_tmp)

    # 2. Criar mapa de dummies -> original
    depara = []
    for original_col in categoricas:
        dummy_cols = [col for col in X_dummies.columns if col.startswith(original_col + "_")]
        for dummy in dummy_cols:
            depara.append({'variavel_original': original_col, 'variavel_dummy': dummy})
    depara_dummy = pd.DataFrame(depara)

    # 3. Variáveis numéricas (identidade)
    depara_numerica = pd.DataFrame({
        'variavel_original': numericas,
        'variavel_dummy': numericas
    })

    # 4. Unir os dois de-para
    depara_geral = pd.concat([depara_dummy, depara_numerica], ignore_index=True)

    # 5. Importância SHAP por dummy
    importance_df = pd.DataFrame({
        'feature': X_dummies.columns,
        'importance': np.abs(shap_values).mean(axis=0)
    })

    # 6. Agrupar importância por variável original
    importance_df = importance_df.merge(depara_geral, left_on='feature', right_on='variavel_dummy', how='inner')

    importance_agrupada = (
        importance_df
        .groupby('variavel_original')['importance']
        .sum()
        .reset_index()
        .sort_values('importance', ascending=False)
    )


    return importance_agrupada, depara_geral

## Importância por Shap

def calcular_shap_importancia(
    df, variaveis, target, 
    random_state=42, parametro = 0.5,
    split_aleatorio = True, prop_treino = 0.8, max_periodo_treino = 202307, coluna_data_ref = 'DATA_REFERENCIA'
):
    warnings.filterwarnings("ignore", category=UserWarning)

    #  Separar X e y
    X = df.drop(columns=variaveis + [target] + [coluna_data_ref], errors='ignore')
    y = df[target]

    #  Split

    if split_aleatorio:
        # Seleção da base
        X_temp, X_test, y_temp, y_test, X_train, X_val, y_train, y_val = split_aleatorio_fun(
            X, y, 
            prop_treino = prop_treino,
            random_state=random_state)
    else:
        X_temp, X_test, y_temp, y_test, X_train, X_val, y_train, y_val = split_temporal(
        base=df, 
        remover = variaveis,
        coluna_data_ref=coluna_data_ref,
        target=target,
        max_periodo_treino=max_periodo_treino
        )

    # Garantir DataFrame com colunas
    X_train = pd.DataFrame(X_train, columns=X.columns)
    X_val   = pd.DataFrame(X_val,   columns=X.columns)
    X_test  = pd.DataFrame(X_test,  columns=X.columns)
    X_display = X_train.copy()

    # Identificar classe de variáveis
    numericas = X_train.select_dtypes(include=['number']).columns.tolist()
    categoricas = X_train.select_dtypes(include=['object', 'category']).columns.tolist()

    # Pipeline
    steps = []
    steps.extend([
        ('step_normalize', StepNormalize(columns=numericas)),
        ('step_dummy', StepDummy(columns=categoricas)),
        ('clean_names', CleanFeatureNames()),
        ('model', lgb.LGBMClassifier(n_estimators=200, random_state=random_state, verbose=-1))
    ])

    pipeline_model = ImbPipeline(steps=steps)
    pipeline_model.fit(X_train, y_train)

    # Transformar X até antes do modelo
    def transform_until_model(pipeline, X):
        Xt = X.copy()
        for name, step in pipeline.steps[:-1]:
            if name == 'step_smote':
                continue  # SMOTE não aplica transform
            Xt = step.transform(Xt)
        return Xt

    ## transform nas bases
    X_train_transf = transform_until_model(pipeline_model, X_train)
    X_val_transf   = transform_until_model(pipeline_model, X_val)

    #  SHAP
    model = pipeline_model.named_steps['model']
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_train_transf)

    X_display = X_train_transf.copy()
    X_display.columns = [
        (c[:25] + '...') if len(c) > 25 else c  # corta nomes acima de 25 caracteres
        for c in X_train_transf.columns
    ]

    shap.summary_plot(shap_values, X_display, max_display=10)
   
    # shap.summary_plot(shap_values, X_train_transf, max_display=10)

    importance_df = pd.DataFrame({
        'feature': X_train_transf.columns,
        'importance': np.abs(shap_values).mean(axis=0)
    }).sort_values('importance', ascending=False)

    limiar = importance_df['importance'].quantile(parametro)
    top_features = importance_df[importance_df['importance'] > limiar]['feature'].tolist()

    # Trazer importancia agrupad
    importance_agrupada, depara_geral = agrupar_importancia_por_variavel_original(
        X_train, shap_values, categoricas, numericas
    )

    return X_train, X_train_transf, y_train, X_val_transf, y_val, X_val, importance_agrupada, top_features

### Importancia permutação 

def importancia_permutacao(
    X_train, X_train_transf, y_train, 
    X_val_transf, y_val, 
    top_features, 
    metric="auc",          # métrica usada para calcular importância
    random_state=42
):

    # --- Função auxiliar para calcular a métrica escolhida ---
    def calcular_metrica(y_true, y_pred_prob, metric):
        if metric == "auc":
            return roc_auc_score(y_true, y_pred_prob)
        elif metric == "brier":
            return -brier_score_loss(y_true, y_pred_prob)  
            # negativo p/ manter lógica "quanto maior melhor"
        else:
            y_pred = (y_pred_prob >= 0.5).astype(int)
            if metric == "accuracy":
                return accuracy_score(y_true, y_pred)
            elif metric == "f1":
                return f1_score(y_true, y_pred)
            else:
                raise ValueError(f"Métrica '{metric}' não suportada!")

    # 1. Treina o modelo base
    model = lgb.LGBMClassifier(
        max_depth=7,
        n_estimators=200,
        learning_rate=0.1,
        random_state=random_state,
        verbose=-1
    )
    model.fit(X_train_transf[top_features], y_train)

    baseline_preds = model.predict_proba(X_val_transf[top_features])[:, 1]
    baseline_score = calcular_metrica(y_val, baseline_preds, metric)
    print(f"{metric.upper()} baseline: {baseline_score:.4f}")

    # 2. Permutation importance
    permutation_results = []
    for feature in tqdm(top_features, desc='Permutation Importance'):
        X_val_shuffled = X_val_transf[top_features].copy()
        np.random.seed(random_state)
        X_val_shuffled[feature] = np.random.permutation(X_val_shuffled[feature].values)

        shuffled_preds = model.predict_proba(X_val_shuffled)[:, 1]
        shuffled_score = calcular_metrica(y_val, shuffled_preds, metric)

        delta = baseline_score - shuffled_score

        permutation_results.append({
            'feature': feature,
            f'delta_{metric}': delta,
            f'shuffled_{metric}': shuffled_score
        })

    permutation_df = pd.DataFrame(permutation_results)

    # 3. Reconstrução do depara (originais vs dummies)
    categoricas = X_train.select_dtypes(include=['object', 'category']).columns.tolist()

    depara = []
    for col in top_features:
        mapeada = False
        for cat in categoricas:
            if col.startswith(cat + "_") or col == cat:
                depara.append({'variavel_original': cat, 'variavel_dummy': col})
                mapeada = True
                break
        if not mapeada:
            depara.append({'variavel_original': col, 'variavel_dummy': col})  

    depara_geral = pd.DataFrame(depara)

    # 4. Merge resultados com mapeamento
    permutation_df = permutation_df.merge(
        depara_geral, left_on='feature', right_on='variavel_dummy', how='left'
    )

    # 5. Agrupamento por variável original
    importance_agrupada = (
        permutation_df
        .groupby('variavel_original')[f'delta_{metric}']
        .sum()
        .reset_index()
        .sort_values(f'delta_{metric}', ascending=False)
        .rename(columns={f'delta_{metric}': 'importance'})
    )

    return importance_agrupada

def selecionar_variaveis_incremental(
    X_train,
    y_train,
    X_val,
    y_val,
    top_perm,        # variáveis originais iniciais
    retiradas_perm,  # variáveis originais a testar
    modelo_base,
    metrica="auc",   # <<<<<<<<<<<<<<<<<<<<<< nova opção
    qui_quadrado=False,
    tolerancia=0.00001,
    random_state=42
):
    """
    metrica: "auc", "accuracy", "f1", "brier"
    """
    categoricas = X_train.select_dtypes(include=['object', 'category']).columns.tolist()
    numericas = X_train.select_dtypes(include=['number']).columns.tolist()

    selected_vars = list(top_perm)
    restantes = [v for v in retiradas_perm if v not in selected_vars]
    resultado = []

    def calcular_score(vars_originais):
        vars_validas = [v for v in vars_originais if v in X_train.columns]
        if not vars_validas:
            return None

        cats = [v for v in vars_validas if v in categoricas]
        nums = [v for v in vars_validas if v in numericas]

        steps = []

        # Normalização + OneHot
        transformers = []
        if cats:
            transformers.append(('cat', OneHotEncoder(handle_unknown='ignore'), cats))
        if nums:
            transformers.append(('num', StandardScaler(), nums))

        if transformers:
            steps.append(('transform', ColumnTransformer(transformers)))

        steps.append(('model', clone(modelo_base).set_params(verbose=-1)))
        pipeline = ImbPipeline(steps=steps)

        Xtr = X_train[vars_validas].copy()
        Xvl = X_val[vars_validas].copy()

        pipeline.fit(Xtr, y_train)
        preds_proba = pipeline.predict_proba(Xvl)[:, 1]
        preds_label = (preds_proba >= 0.5).astype(int)

        # === Escolha da métrica ===
        if metrica == "auc":
            return roc_auc_score(y_val, preds_proba)
        elif metrica == "accuracy":
            return accuracy_score(y_val, preds_label)
        elif metrica == "f1":
            return f1_score(y_val, preds_label)
        elif metrica == "brier":
            return -brier_score_loss(y_val, preds_proba)  # negativo, pois menor é melhor
        else:
            raise ValueError(f"Métrica '{metrica}' não suportada.")

    # Score inicial
    best_score = calcular_score(selected_vars)
    if best_score is None:
        print("❌ Nenhuma variável válida no início. Verifique top_perm e seu DataFrame.")
        return pd.DataFrame(), []

    print(f"{metrica.upper()} inicial: {best_score:.5f}\n")

    # Seleção incremental
    for var in tqdm(restantes, desc="Selecionando"):
        trial = selected_vars + [var]
        score_t = calcular_score(trial)
        if score_t is None:
            continue

        delta = score_t - best_score
        print(f"{var:20s} → {metrica.upper()} {score_t:.5f} (Δ {delta:+.6f})")
        if delta > tolerancia:
            print("  ✅ Mantém\n")
            selected_vars.append(var)
            best_score = score_t
            resultado.append({'variavel': var,  f'delta_{metrica}_nivel3': delta*100, 'nivel_3': 'Sim'})
        else:
            print("  ❌ Descarta\n")
            resultado.append({'variavel': var,  f'delta_{metrica}_nivel3': delta*100, 'nivel_3': 'Não'})

    df_result = pd.DataFrame(resultado)

    # Garantir que as top_perm apareçam no resultado
    for var in top_perm:
        if var not in df_result['variavel'].values:
            df_result = pd.concat([
                df_result,
                pd.DataFrame([{
                    'variavel': var,
                    f'delta_{metrica}_nivel3': 0.0,
                    'nivel_3': 'Sim'
                }])
            ], ignore_index=True)

    df_result = df_result.sort_values(by='nivel_3', ascending=False).reset_index(drop=True)
    
    return df_result, selected_vars

def escolha_variaveis(
    data: pl.DataFrame,
    nivel: int = 3,
    coluna_data_ref: str = "DATA_REFERENCIA",
    max_periodo_treino: int = 202401,
    features: list = [],
    target: str = "target",
    split_aleatorio: bool = True,
    parametro_nivel_0 = 0.1,
    parametro_nivel_1 = 0.5,
    parametro_nivel_2 = 0.0005,
    parametro_nivel_3 = 0.00001,
    qui_quadrado: bool = False,
    random_state = 42,
    prop_treino = 0.8,
    p_valor = 0.05,
    limite_cardinalidade = 50,
    metrica = "auc",
    drop_null = False

) -> pd.DataFrame:
    """
    Função de escolha de variáveis - Nível 0 (aderência)
    Retorna um DataFrame com colunas padronizadas: variável, tipo, T1_T2, TARGET_T1, TARGET_T2, TARGET_Q_FACTOR
    """

    # Garante que target não está em features
    features = [f for f in features if f != target]

    #### Avaliar cardinalidade 

    variaveis_alta_cardinalidade = []

    # Avalia apenas colunas categóricas (pl.Utf8)
    for col, dtype in zip(data.columns, data.dtypes):
        if dtype == pl.Utf8 and col in features:
            n_unique = data.select(pl.col(col)).unique().height
            if n_unique > limite_cardinalidade:
                variaveis_alta_cardinalidade.append((col, n_unique))
    
    if variaveis_alta_cardinalidade:
        for nome, cardinalidade in variaveis_alta_cardinalidade:
            print(f"[ALTA CARDINALIDADE] A variável '{nome}' possui {cardinalidade} categorias distintas.")
        raise ValueError("A função foi interrompida devido a variáveis com cardinalidade acima do permitido. \n\nAvalie, se necessário, e caso queira incluir mesmo assim inclua na função limite_cardinalidade = valor máximo de categorias.\n \nObs.: Caso tenha muitas categorias a função pode explodir na etapa de dummificação das variáveis categóricas ")


    ## Avaliar valores nulos 
    if ((data.select(pl.col(features), pl.col(target)).null_count().to_numpy().sum() > 0) & (drop_null==False)):
        raise ValueError(
            'Existem variáveis com valores nulos no banco de dados. '
            'Por favor trate ou use o argumento "drop_null=True".'
    )
    if drop_null:
        data = data.select(pl.col(features), pl.col(target)).drop_nulls()
        
    #### NIVEL 0

    # Split
    if split_aleatorio:
        # Seleção da base
        data_temp = data.select(
            pl.col(features), pl.col(target)
        )
        t1, t2, _ = split_treino_teste_aleatorio(data_temp)
    else:
        # Verifica se a coluna de data existe
        if coluna_data_ref not in data.columns:
            raise ValueError(f"[ERRO] A coluna '{coluna_data_ref}' não foi encontrada na base de dados. \n \nInclua uma variável de tempo em coluna_data_ref e um período para o corte de treino e teste em max_periodo_treino, ou faça um split aleatório: \nsplit_aleatorio = True")
        
        # Seleção da base
        data_temp = data.select(
            coluna_data_ref, pl.col(features), pl.col(target)
        )
        t1, t2, _ = split_treino_teste_temporal(data_temp, coluna_data_ref, max_periodo_treino)

    # Tipo de variáveis
    dtypes = data_temp.select(features).dtypes
    numericas = [f for f, t in zip(features, dtypes) if t in [pl.Float64,pl.Float32, pl.Int32, pl.Int64]]
    categoricas = [f for f in features if f not in numericas]

    resultados = []

    for var in numericas:
        stat_t1t2, _ = ks_t1t2(var, t1, t2)
        (stat_t1, _), (stat_t2, _), q = ks_target(var, t1, t2, target)
        p_t = teste_t_student(data_temp, var, target)

        resultados.append({
            "variavel": var,
            "tipo": "numerica",
            "T1_T2": stat_t1t2,
            "TARGET_T1": stat_t1,
            "TARGET_T2": stat_t2,
            "TARGET_Q_FACTOR": q,
            "QUI_T": p_t
        })

    for var in categoricas:
        stat_t1t2, _ = total_variation_t1t2(data_temp, var, t1, t2)
        (stat_t1, _), (stat_t2, _), q = total_variation_target(data_temp, var, t1, t2, target)
        p_q = teste_quiquadrado(data_temp, var, target)

        resultados.append({
            "variavel": var,
            "tipo": "categorica",
            "T1_T2": stat_t1t2,
            "TARGET_T1": stat_t1,
            "TARGET_T2": stat_t2,
            "TARGET_Q_FACTOR": q,
            "QUI_T": p_q
        })

    resultados = pl.DataFrame(resultados)

    print(f"A base tem um total de {len(resultados.select('variavel').to_series().to_list())} variáveis consideradas. \n")

    if qui_quadrado:
        variaveis = (
            resultados
            .filter(((pl.col('QUI_T') > p_valor) & 
            (pl.col('tipo')=='categorica')) |
            ((((pl.col('TARGET_T1') + pl.col('TARGET_T2')) / 2) < parametro_nivel_0) & 
            (pl.col('tipo') == 'numerica')))
            .select('variavel').to_series().to_list()
            )
    else:
        variaveis = (
            resultados
            .filter(((pl.col('TARGET_T1') + pl.col('TARGET_T2')) / 2) < parametro_nivel_0)
            .select('variavel').to_series().to_list()
        )
    
    
    print(f"As variáveis retiradas no Nível 0 (Aderência) foram:\n{variaveis}\nTotalizando {len(variaveis)} variáveis.\n")

    # Cria o DataFrame com as variáveis do nível 0
    dados_aderencia = pl.DataFrame({'variavel': variaveis, 'nivel_0': 'Não'})

    if len(dados_aderencia)==0:
        resultados = resultados.with_columns(
            pl.lit('Sim').alias('nivel_0')
        )
    else:
        # Faz o join com base na coluna 'variavel'
        resultados = resultados.join(dados_aderencia, on='variavel', how='left')

        resultados = resultados.with_columns(
            pl.col('nivel_0').fill_null('Sim')
        )

    selecionadas = resultados.filter(pl.col('nivel_0')=='Sim').select('variavel').to_series().to_list()


    if len(selecionadas) == 0:
        print(f"Não existem variáveis para aplicar o nível 1. Desta forma, a função termina aqui ou flexibilixe os parâmetros da função.")
        return resultados, selecionadas

    if nivel == 0:
        return resultados, selecionadas
    else:
        print(f"Iniciando cálculo do nível 1 - Melhores por Shap.\n")

        X_train, X_train_transf, y_train, X_val_transf, y_val, X_val, shap_agrupado, top_features = calcular_shap_importancia(
            df=data_temp.to_pandas(),
            variaveis=variaveis,
            target=target,
            parametro = parametro_nivel_1,
            random_state=random_state,
            split_aleatorio=split_aleatorio,
            prop_treino = prop_treino, 
            max_periodo_treino = max_periodo_treino, 
            coluna_data_ref = coluna_data_ref
        )

        top_shap = shap_agrupado.head(int(len(shap_agrupado) * parametro_nivel_1))['variavel_original'].tolist()

        # Cria o DataFrame com as variáveis do nível 1
        dados_shap = (
            pl.from_pandas(shap_agrupado)
            .rename({'variavel_original':'variavel',
                    'importance':'importance_permutation_nivel1'})
            .with_columns([
            (pl.col("importance_permutation_nivel1")).alias("importance_permutation_nivel1")
            ])
            .with_columns(pl.when(pl.col('variavel').is_in(top_shap)).then(pl.lit('Sim')).otherwise(pl.lit('Não')).alias('nivel_1'))
        )

        # Faz o join com base na coluna 'variavel'
        resultados = resultados.join(dados_shap, on='variavel', how='left')

        resultados = resultados.with_columns(
            pl.col('nivel_1').fill_null('Não')
        )

        retiradas_shap = data_temp.drop(variaveis).drop(top_shap).drop(pl.col(target)).columns

        print(f"As variáveis retiradas no Nível 1 (Importância Shap) foram:\n{retiradas_shap}\nTotalizando {len(retiradas_shap)} variáveis.\n")
        
        selecionadas = top_shap

        if nivel == 1:
            return resultados, selecionadas
        else:
            
            if len(selecionadas) == 0:
                print(f"Não existem variáveis para aplicar o nível 1. Desta forma, a função termina aqui ou flexibilixe os parâmetros da função.")
                return resultados, selecionadas
            
            else:
                print(f"Iniciando cálculo do nível 2 - Importância por permutação.\n")

                importancia_perm = importancia_permutacao(
                    X_train, X_train_transf, y_train,
                    X_val_transf, y_val,
                    top_features=top_features,
                    random_state=random_state,
                    metric=metrica
                )

                top_perm = pl.from_pandas(importancia_perm).filter(pl.col('importance')>parametro_nivel_2).select('variavel_original').to_series().to_list()


                # Cria o DataFrame com as variáveis do nível 2
                dados_perm = (
                    pl.from_pandas(importancia_perm)
                    .rename({'variavel_original':'variavel',
                            'importance':'importance_permutation_nivel2'})
                    .with_columns([
                    (pl.col("importance_permutation_nivel2") * 100).alias("importance_permutation_nivel2")
                    ])
                    .with_columns(pl.when(pl.col('importance_permutation_nivel2')>parametro_nivel_2*100).then(pl.lit('Sim')).otherwise(pl.lit('Não')).alias('nivel_2'))
                )

                # Faz o join com base na coluna 'variavel'
                resultados = resultados.join(dados_perm, on='variavel', how='left')

                resultados = resultados.with_columns(
                    pl.col('nivel_2').fill_null('Não')
                )
                
                retiradas_perm = data_temp.drop(variaveis,strict=False).drop(retiradas_shap,strict=False).drop(top_perm,strict=False).drop(target).columns
                
                print(f"As variáveis retiradas no Nível 2 (Importância Permutação) foram:\n{retiradas_perm}\nTotalizando {len(retiradas_perm)} variáveis.")

                print(f"As variáveis consideradas aptas para o modelo no Nível 2 (Importância Permutação) foram:\n{top_perm}\nTotalizando {len(top_perm)} variáveis.")
                
                selecionadas = top_perm

                if nivel == 2:
                    return resultados, selecionadas
                else:
                    ### Nível 3 
                    
                    if len(retiradas_perm) == 0:
                        print(f"Não existem variáveis para aplicar o nível 3. Desta forma, a função termina aqui ou flexibilixe os parâmetros.")
                        return resultados, selecionadas
                    else:
                        print(f"\n Iniciando cálculo do nível 3 - Desempenho na AUC.\n")

                        df_result, selecionadas = selecionar_variaveis_incremental(
                            X_train, y_train,
                            X_val, y_val,
                            top_perm=top_perm,
                            retiradas_perm=retiradas_perm,
                            modelo_base=lgb.LGBMClassifier(n_estimators=200,random_state=random_state),
                            tolerancia = parametro_nivel_3,
                            random_state=random_state,
                            metrica=metrica
                        )

                        resultados = resultados.join(pl.DataFrame(df_result), on='variavel', how='left')

                        resultados = resultados.with_columns([
                                pl.col('nivel_3').fill_null('Não'),
                                pl.col('importance_permutation_nivel2').fill_null(0),
                                pl.col(f'delta_{metrica}_nivel3').fill_null(0)
                        ])

                        print(f"As variáveis consideradas aptas para o modelo após o Nível 3 (Desempenho AUC) foram:\n{selecionadas}\nTotalizando {len(selecionadas)} variáveis.")
                
                        # return resultados, data_temp, variaveis
                        return resultados, selecionadas