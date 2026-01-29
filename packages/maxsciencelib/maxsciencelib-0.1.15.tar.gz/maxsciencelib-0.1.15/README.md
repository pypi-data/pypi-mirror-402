# MaxScienceLib

Biblioteca com funções utilitárias para a rotina de **Ciência de Dados** na **Maxpar**, focada em **produtividade**, **padronização** e **alta performance**.


## 📚 Sumário

* [Instalação e uso](#-instalação-e-uso)

* [Módulos disponíveis](#-módulos-disponíveis)

  * [`leitura`](#leitura)
    * [`leitura_snowflake`](#leitura_snowflake)
    * [`leitura_tableau`](#leitura_tableau)
    * [`leitura_fipe`](#leitura_fipe)
    * [`leitura_metabase`](#leitura_metabase)

  * [`upload`](#upload)
    * [`upload_sharepoint`](#upload_sharepoint)

  * [`tratamento`](#tratamento)
    * [`media_saneada`](#media_saneada)
    * [`media_saneada_groupby`](#media_saneada_groupby)
    * [`agrupar_produto`](#agrupar_produto)
    * [`limpar_texto`](#limpar_texto)
    * [`extrair_intervalo_ano_modelo`](#extrair_intervalo_ano_modelo)

  * [`machine_learning`](#machine_learning)
    * [`monitorar_degradacao`](#monitorar_degradacao)

  * [`feature_engineering`](#feature_engineering)
    * [`escolha_variaveis`](#escolha_variaveis)
    * [`time_features`](#time_features)
    * [`chassi_features`](#chassi_features)


  * [`analise_exploratoria`](#analise_exploratoria)
    * [`relatorio_modelo`](#relatorio_modelo)
    * [`plot_lift_barplot`](#plot_lift_barplot)
    * [`plot_ks_colunas`](#plot_ks_colunas)
    * [`plot_correlacoes`](#plot_correlacoes)


* [Licença](#licença)
* [Autores](#autores)

## Instalação e uso

Instale a biblioteca via `pip`:

```bash
pip install maxsciencelib
```

Importe os módulos no seu código:

```python
from maxsciencelib import leitura_snowflake
```

---

## Módulos disponíveis

# leitura

Módulo Python para **leitura** de dados, de forma simples, segura e perfomática, resultando em Dataframes Polars


## 🔹 `leitura_snowflake`

Função Python para leitura de dados do **Snowflake** de forma simples, segura e performática, retornando os resultados diretamente como **DataFrame Polars**.

A função abstrai toda a complexidade de conexão, autenticação via `externalbrowser` e execução de queries, permitindo que o usuário execute consultas com apenas **uma função**.



### Funcionalidades

- Conexão automática com Snowflake via `externalbrowser`
- Execução de queries SQL
- Retorno direto em **Polars DataFrame**
- Uso nativo de **Apache Arrow** (alta performance)
- Silenciamento de logs e warnings internos
- Fechamento seguro de conexão e cursor


### Requisitos

- Python **3.11+** (recomendado)
- Acesso ao Snowflake configurado no navegador


### Uso básico

```python
from leitura_snowflake import leitura_snowflake

query = """
SELECT *
FROM MINHA_TABELA
LIMIT 1000
"""

df = leitura_snowflake(
    email_corporativo="nome.sobrenome@empresa.com",
    token_account="abc123.us-east-1",
    query=query
)

df.head()
```

O retorno será um objeto:

```python
polars.DataFrame
```

| Parâmetro           | Tipo  | Descrição                                         |
| ------------------- | ----- | ------------------------------------------------- |
| `email_corporativo` | `str` | Email corporativo utilizado no login do Snowflake |
| `token_account`     | `str` | Identificador da conta Snowflake                  |
| `query`             | `str` | Query SQL a ser executada                         |

--- 

## 🔹 `leitura_tableau`

Função Python para leitura de dados do **Tableau Server** de forma simples, segura e performática, retornando os resultados diretamente como **DataFrame Polars**.

A função abstrai toda a complexidade de autenticação via **Personal Access Token**, conexão com o Tableau Server (HTTP/HTTPS) e download da view, permitindo que o usuário consuma dados com apenas **uma função**.


### Funcionalidades

* Autenticação via **Personal Access Token (PAT)**
* Conexão automática com Tableau Server (fallback HTTP → HTTPS)
* Download de views diretamente do Tableau
* Retorno direto em **Polars DataFrame**
* Leitura eficiente de CSV em memória
* Silenciamento de warnings internos
* Encerramento seguro da sessão (`sign_out`)

### Requisitos

* Python **3.10+** (recomendado)
* Acesso ao Tableau Server
* Personal Access Token ativo no Tableau


### Uso básico

```python
from maxsciencelib import leitura_tableau

df = leitura_tableau(
    nome_token="meu_token_tableau",
    token_acesso="XXXXXXXXXXXXXXXXXXXXXXXX",
    view_id="abcd1234-efgh-5678"
)

df.head()
```

### Retorno

O retorno da função será um objeto:

```python
polars.DataFrame
```

### Parâmetros

| Parâmetro      | Tipo  | Descrição                                           |
| -------------- | ----- | --------------------------------------------------- |
| `nome_token`   | `str` | Nome do Personal Access Token cadastrado no Tableau |
| `token_acesso` | `str` | Token de acesso pessoal do Tableau                  |
| `view_id`      | `str` | Identificador da view no Tableau Server             |

---

## 🔹 `leitura_fipe`

Função Python para **categorização de veículos com base na Tabela FIPE**, utilizando **quantis dinâmicos por tipo de veículo** e separação entre **veículos antigos e recentes**, retornando os resultados em **Polars DataFrame**.

A função abstrai toda a lógica estatística de cálculo de quantis, tratamento de dados e categorização, permitindo que o usuário obtenha a classificação do veículo com **apenas uma função**.

### Funcionalidades

* Leitura da Tabela FIPE diretamente de arquivo Excel
* Padronização automática de colunas
* Tratamento do ano (`ZERO KM` → ano vigente)
* Criação da chave `FIPE-ANO`
* Separação automática entre:

  * Veículos **antigos** (`ano < 2015`)
  * Veículos **recentes** (`ano ≥ 2015`)
* Categorização baseada em quantis por tipo de veículo:

  * **Antigo Popular**
  * **Antigo Premium**
  * **Popular**
  * **Intermediário**
  * **Premium**
* Processamento totalmente vetorizado em **Polars**
* Alta performance para grandes volumes de dados
* Interface simples e pronta para uso analítico

### Requisitos

* Python **3.10+** (recomendado)
* Acesso ao arquivo da Tabela FIPE
* Estrutura de colunas compatível com a base FIPE padrão

### Dependências

```bash
pip install polars pyarrow fastexcel
```

> O pacote `fastexcel` é utilizado pelo Polars para leitura eficiente de arquivos Excel.

### Uso básico

```python
from maxsciencelib import leitura_fipe

df_fipe_categoria = leitura_fipe()

df_fipe_categoria.head()
```

### Retorno

A função retorna um objeto do tipo:

```python
polars.DataFrame
```

com as seguintes colunas:

| Coluna      | Descrição                                    |
| ----------- | -------------------------------------------- |
| `fipe_ano`  | Código FIPE concatenado com o ano do veículo |
| `ano`       | Ano do veículo                               |
| `marca`     | Marca do veículo                             |
| `modelo`    | Modelo do veículo                            |
| `categoria` | Categoria FIPE calculada                     |


### Lógica de categorização

A categorização é feita **por tipo de veículo**, seguindo as regras abaixo:

#### Veículos antigos (`ano < 2015`)

| Condição      | Categoria      |
| ------------- | -------------- |
| `valor ≤ P60` | Antigo Popular |
| `valor > P60` | Antigo Premium |

#### Veículos recentes (`ano ≥ 2015`)

| Condição            | Categoria     |
| ------------------- | ------------- |
| `valor ≤ P50`       | Popular       |
| `P50 < valor ≤ P70` | Intermediário |
| `valor > P70`       | Premium       |

> Os percentis são calculados **dinamicamente por `tipo_veiculo`**.


---

## 🔹 `leitura_metabase`

Função para **consumo direto de dados do Metabase** a partir do **id** da sua view, retornando os resultados como **Polars DataFrame** de forma simples e segura.

A função abstrai todo o processo de **autenticação via API do Metabase**, gerenciamento de **sessão**, tratamento de **expiração (HTTP 401)** e conversão automática do JSON retornado para **Polars**, sendo ideal para **pipelines analíticos e análise exploratória**.


### Funcionalidades

* Autenticação automática no **Metabase API**
* Reutilização de sessão durante a execução
* Retentativa automática em caso de **sessão expirada (401)**
* Download direto de **Id** via API
* Conversão automática para **Polars DataFrame**
* Controle de timeout e número de tentativas
* Logs opcionais para acompanhamento da execução
* Tratamento robusto de erros HTTP e de requisição

### Uso básico

```python
from maxsciencelib import leitura_metabase

df = leitura_metabase(
    metabase_url="http://258.23.45.15:1233",
    id=123,
    username="usuario_metabase",
    password="senha_metabase"
)

df.head()
```

### Retorno

A função retorna:

```python
polars.DataFrame | None
```

* `polars.DataFrame` → quando a consulta é bem-sucedida
* `None` → em caso de erro de autenticação, requisição ou resposta inválida


### Parâmetros

| Parâmetro      | Tipo         | Descrição                                                     |
| -------------- | ------------ | ------------------------------------------------------------- |
| `metabase_url` | `str`        | URL base do Metabase (ex: `https://metabase.exemplo.com`)     |
| `id`           | `int \| str` | ID do Metabase                                                |
| `username`     | `str`        | Usuário com acesso ao Card                                    |
| `password`     | `str`        | Senha do usuário do Metabase                                  |
| `max_retries`  | `int`        | Número máximo de retentativas em caso de erro 401 (default=2) |
| `timeout`      | `int`        | Timeout das requisições HTTP em segundos (default=30)         |
| `verbose`      | `bool`       | Exibe logs no console se `True` (default=True)                |


---

# upload

Módulo Python para **upload** de dados, com foco em realizar carga e output de dados.

## Instalação

```bash
pip install maxsciencelib[upload]
```

---

## 🔹 `upload_sharepoint`

Função Python para **upload automático de arquivos no SharePoint** utilizando automação via navegador (**Selenium + Microsoft Edge**).

A função abstrai toda a complexidade de interação com a interface web do SharePoint, permitindo realizar o upload de **todos os arquivos de um diretório local** com apenas **uma chamada de função**.

> Esta funcionalidade utiliza automação de UI e depende do layout do SharePoint. Recomendada para uso interno e controlado.


### Funcionalidades

- Upload automático de múltiplos arquivos para SharePoint
- Suporte a upload em massa a partir de um diretório local
- Automação via Microsoft Edge (Selenium)
- Detecção automática de sobrescrita (`Substituir tudo`)
- Controle de timeout e tempo de espera
- Fechamento seguro do navegador


### Requisitos

- Python **3.11+** (recomendado)
- Microsoft Edge instalado
- Edge WebDriver compatível
- Acesso ao SharePoint via navegador (login manual)


### Dependências

Caso esteja usando a biblioteca `maxsciencelib` recomenda-se instalar com:

```bash
pip install maxsciencelib[upload]
```


### Uso básico

```python
from maxsciencelib import upload_sharepoint

upload_sharepoint(
    url_sharepoint="https://autoglass365.sharepoint.com/sites/XXXXXXXXX/Shared%20Documents/Forms/AllItems.aspx",
    diretorio=r"C:\Users\usuario\Desktop\arquivos_para_upload"
)
```


### Comportamento da função

* Todos os arquivos presentes no diretório informado serão enviados
* Caso o arquivo já exista no SharePoint, a função tentará clicar em **“Substituir tudo”**
* O navegador será fechado automaticamente ao final do processo
* Em caso de erro, a função lança exceções claras (`FileNotFoundError`, `RuntimeError`)


### Parâmetros

| Parâmetro          | Tipo  | Descrição                                                               |
| ------------------ | ----- | ----------------------------------------------------------------------- |
| `url_sharepoint`   | `str` | URL do diretório do SharePoint onde os arquivos serão carregados        |
| `diretorio`        | `str` | Caminho local contendo **apenas** os arquivos a serem enviados          |
| `tempo_espera_fim` | `int` | Tempo (em segundos) de espera após o upload antes de fechar o navegador |
| `timeout`          | `int` | Timeout máximo (em segundos) para espera de elementos na interface      |


### Retorno

```python
None
```

A função não retorna valores.
Caso ocorra algum erro durante o processo, uma exceção será lançada.



---

# tratamento

Módulo Python para **tratamento** de dados, com métricas desenvolvidas pelo time, de modo a padronizar resultados.

## Instalação

```bash
pip install maxsciencelib[tratamento]
```

---

## 🔹 `agrupar_produto`

Função Python para **padronização e agrupamento de descrições de produtos automotivos**, abstraindo regras complexas de **marca**, **lado (LE/LD)** e **casos específicos por tipo de peça**, retornando o resultado diretamente no **DataFrame original** com uma nova coluna agrupada.

A função foi desenhada para que o usuário precise chamar **apenas uma função**, informando o **DataFrame**, a **coluna de origem** e o **nome da nova coluna**, mantendo a coluna original intacta.


### Funcionalidades

* Agrupamento automático por **tipo de produto**

  * Vidro
  * Retrovisor
  * Farol / Lanterna
* Remoção padronizada de **marca**
* Remoção padronizada de **lado (LE / LD / E / D)**
* Tratamento de **casos específicos**
* Limpeza de sufixos como:

  * `EXC`
  * `AMT`
  * `AMT CNT`
  * `AMT AER`
* Preserva a coluna original
* Compatível com valores nulos (`NaN`)
* Interface simples, orientada a **DataFrame**
* Pronta para uso em pipelines analíticos e feature engineering


### Requisitos

* Python **3.9+**
* Pandas

### Dependências

```bash
pip install pandas
```

### Uso básico

```python
from maxsciencelib import agrupar_produto

df = agrupar_produto(
    df,
    coluna_origem="produto_descricao",
    coluna_nova="produto_agrupado"
)

df.head()
```

### Uso com controle de regras

```python
df = agrupar_produto(
    df,
    coluna_origem="produto_descricao",
    coluna_nova="produto_agrupado",
    agrupar_marca=False,
    agrupar_lado=True
)
```

### Retorno

A função retorna o próprio DataFrame com a nova coluna adicionada:

```python
pandas.DataFrame
```

### Parâmetros

| Parâmetro       | Tipo      | Descrição                                                      |
| --------------- | --------- | -------------------------------------------------------------- |
| `df`            | DataFrame | DataFrame de entrada                                           |
| `coluna_origem` | `str`     | Nome da coluna que contém a descrição original do produto      |
| `coluna_nova`   | `str`     | Nome da nova coluna com o produto agrupado                     |
| `agrupar_marca` | `bool`    | Remove marcas do produto (`True` por padrão)                   |
| `agrupar_lado`  | `bool`    | Remove indicação de lado (LE / LD / E / D) (`True` por padrão) |


### Regras de agrupamento (interno)

A função identifica automaticamente o tipo de produto com base na descrição:

| Tipo identificado | Regra aplicada                    |
| ----------------- | --------------------------------- |
| `VID`             | Agrupamento de vidros             |
| `RETROV`          | Agrupamento de retrovisores       |
| `FAROL` / `LANT`  | Agrupamento de faróis e lanternas |
| Outros            | Mantém a descrição original       |

---

## 🔹 `media_saneada`

Função para cálculo de **média saneada**, removendo outliers de forma iterativa com base no **coeficiente de variação (CV)**, garantindo maior robustez estatística e **alto desempenho computacional**.

A implementação foi projetada para **grandes volumes de dados**, utilizando:

* **NumPy puro no caminho crítico**
* **Paralelização real por grupo (multiprocessing)**

São disponibilizadas **duas funções públicas**:

* uma função **core**, para cálculo direto sobre vetores numéricos
* uma função **groupby**, para agregações eficientes em **DataFrames Pandas**, com paralelização automática


## Funcionalidades

* Cálculo de média robusta com saneamento iterativo
* Remoção automática de outliers com base em:

  * média
  * desvio padrão
  * coeficiente de variação (CV)
* Fallback seguro para **mediana**
* Controle de:

  * número mínimo de amostras
  * CV máximo permitido
* Alta performance:

  * NumPy puro no loop crítico
  * Paralelização por múltiplos processos
* Compatível com:

  * `list`
  * `numpy.ndarray`
  * `pandas.Series`
* Integração nativa com **Pandas `groupby`**


### Assinatura

```python
media_saneada(
    valores,
    min_amostras: int = 3,
    cv_max: float = 0.25
) -> float
```

### Parâmetros

| Parâmetro      | Tipo                                | Descrição                                |
| -------------- | ----------------------------------- | ---------------------------------------- |
| `valores`      | `list` | `np.ndarray` | `pd.Series` | Conjunto de valores numéricos            |
| `min_amostras` | `int`                               | Número mínimo de amostras permitidas     |
| `cv_max`       | `float`                             | Coeficiente de variação máximo aceitável |

### Retorno

```python
float
```

* Retorna a **média saneada** se o CV estiver dentro do limite
* Caso contrário, retorna a **mediana** dos últimos `min_amostras` valores
* Nunca lança erro para vetores pequenos (fallback seguro)

### Uso básico

```python
from maxsciencelib import media_saneada

media = media_saneada([100, 102, 98, 500, 101])
```

---

## 🔹 `media_saneada_groupby`

Aplica a média saneada por grupo em um **DataFrame Pandas**, utilizando **paralelização por múltiplos processos** para reduzir drasticamente o tempo de execução.

### Assinatura

```python
media_saneada_groupby(
    df: pd.DataFrame,
    group_cols: list[str],
    value_col: str,
    min_amostras: int = 3,
    cv_max: float = 0.25,
    n_jobs: int = -1,
    output_col: str = "media_saneada"
) -> pd.DataFrame
```

### Parâmetros

| Parâmetro      | Tipo           | Descrição                                             |
| -------------- | -------------- | ----------------------------------------------------- |
| `df`           | `pd.DataFrame` | DataFrame de entrada                                  |
| `group_cols`   | `list[str]`    | Colunas de agrupamento                                |
| `value_col`    | `str`          | Coluna numérica a ser agregada                        |
| `min_amostras` | `int`          | Número mínimo de amostras por grupo                   |
| `cv_max`       | `float`        | Coeficiente de variação máximo aceitável              |
| `n_jobs`       | `int`          | Número de processos paralelos (`-1` = todos os cores) |
| `output_col`   | `str`          | Nome da coluna de saída                               |

### Retorno

```python
pd.DataFrame
```

DataFrame agregado contendo uma linha por grupo e a média saneada calculada.

---

### Exemplo de uso

```python
import pandas as pd
from maxsciencelib import media_saneada_groupby

df = pd.DataFrame({
    "grupo": ["A", "A", "A", "A", "B", "B", "B"],
    "valor": [100, 102, 98, 500, 50, 52, 51]
})

resultado = media_saneada_groupby(
    df,
    group_cols=["grupo"],
    value_col="valor"
)
```

---

## 🔹 `limpar_texto`

Função Python para **limpeza, normalização e padronização de textos**, suportando tanto **strings individuais** quanto **colunas do Polars (`Series` ou `Expr`)**, com alta performance e reutilização em pipelines de dados.

A função abstrai todo o tratamento comum de textos — remoção de acentos, pontuações, quebras de linha, normalização de espaços e padronização de case — permitindo aplicar o mesmo padrão de limpeza **tanto em valores isolados quanto diretamente em DataFrames Polars**.


### Funcionalidades

* Limpeza de **strings individuais**
* Suporte nativo a **Polars (`Series` e `Expr`)**
* Remoção de acentos (`unidecode`)
* Remoção de quebras de linha e tags `<br>`
* Normalização de espaços
* Remoção total de pontuação ou preservação de `.` e `,`
* Padronização de **lowercase** ou **uppercase**
* Regex pré-compilados para maior performance
* Retorno consistente (`None` para strings vazias ou inválidas)


### Requisitos

* Python **3.10+**
* Biblioteca **polars**
* Biblioteca **unidecode**

### Uso básico

#### 🔸 String simples

```python
from maxsciencelib import limpar_texto

texto = "Olá, Mundo!   <br> Teste de TEXTO."

resultado = limpar_texto(
    texto,
    case="lower",
    mantem_pontuacao=False
)

print(resultado)
```

**Saída:**

```text
ola mundo teste de texto
```


#### 🔸 Coluna Polars (`Series`)

```python
import polars as pl
from maxsciencelib import limpar_texto

df = pl.DataFrame({
    "descricao": [
        "Peça NOVA<br>",
        "Motor 2.0, Turbo!",
        None
    ]
})

df = df.with_columns(
    limpar_texto(pl.col("descricao")).alias("descricao_limpa")
)

df
```


#### 🔸 Uso em expressões (`Expr`)

```python
df = df.with_columns(
    limpar_texto(
        pl.col("descricao"),
        case="upper",
        mantem_pontuacao=True
    ).alias("descricao_padronizada")
)
```


### Retorno

O retorno da função será um dos tipos abaixo, dependendo da entrada:

```python
str | polars.Series | polars.Expr
```

### Parâmetros

| Parâmetro          | Tipo                          | Descrição                                       |
| ------------------ | ----------------------------- | ----------------------------------------------- |
| `texto`            | `str \| pl.Series \| pl.Expr` | Texto ou coluna Polars a ser tratada            |
| `case`             | `str`                         | Define o case do texto (`"lower"` ou `"upper"`) |
| `mantem_pontuacao` | `bool`                        | Se `True`, mantém apenas `.` e `,` no texto     |

---

## 🔹 `extrair_intervalo_ano_modelo`

Função Python para **extração e normalização de intervalos de ano modelo** a partir de **colunas string em Polars**, retornando **expressões (`pl.Expr`) prontas para uso em `with_columns`**.

A função identifica padrões do tipo `YY/YY` ou `YY/` (ano inicial aberto), converte corretamente para anos com quatro dígitos (`YYYY`) e trata automaticamente a virada de século, além de preencher o ano final com o **ano atual** quando necessário.


### Funcionalidades

* Extração de intervalos no formato `YY/YY`
* Suporte a intervalos abertos (`YY/`)
* Conversão automática para anos com 4 dígitos

  * `>= 50` → século XX (19xx)
  * `< 50` → século XXI (20xx)
* Preenchimento automático do ano final com o **ano atual**
* Retorno como **expressões Polars (`pl.Expr`)**
* Personalização dos nomes das colunas de saída
* Tratamento seguro de valores inválidos (retorno `null`)


### Requisitos

* Python **3.10+**
* Biblioteca **polars**


### Uso básico

#### 🔸 Exemplo simples

```python
import polars as pl
from maxsciencelib import extrair_intervalo_ano_modelo

df = pl.DataFrame({
    "ano_modelo": ["10/18", "98/04", "15/", "abc", None]
})

df = df.with_columns(
    extrair_intervalo_ano_modelo(pl.col("ano_modelo"))
)

df
```


### Uso com nomes personalizados de colunas

```python
df = df.with_columns(
    extrair_intervalo_ano_modelo(
        pl.col("ano_modelo"),
        nome_inicio="ano_ini",
        nome_fim="ano_fim"
    )
)
```


### Uso com ano atual customizado

```python
df = df.with_columns(
    extrair_intervalo_ano_modelo(
        pl.col("ano_modelo"),
        ano_atual=2023
    )
)
```


### Retorno

A função retorna uma lista contendo **duas expressões Polars**:

```python
list[polars.Expr]
```

Essas expressões representam:

1. Ano modelo inicial
2. Ano modelo final


### Parâmetros

| Parâmetro     | Tipo          | Descrição                                                             |
| ------------- | ------------- | --------------------------------------------------------------------- |
| `col`         | `pl.Expr`     | Coluna string contendo o intervalo de ano modelo                      |
| `ano_atual`   | `int \| None` | Ano usado para intervalos abertos (`YY/`). Se `None`, usa o ano atual |
| `nome_inicio` | `str`         | Nome da coluna de ano modelo inicial                                  |
| `nome_fim`    | `str`         | Nome da coluna de ano modelo final                                    |


### Padrões reconhecidos

| Valor original | Ano Inicial | Ano Final |
| -------------- | ----------- | --------- |
| `"10/18"`      | 2010        | 2018      |
| `"98/04"`      | 1998        | 2004      |
| `"15/"`        | 2015        | Ano atual |
| `"abc"`        | `null`      | `null`    |
| `None`         | `null`      | `null`    |

---

# feature_engineering

Módulo Python para **feature engineering**, com funçções para seleção e geração de variáveis, com métricas desenvolvidas pelo time, de modo a padronizar resultados e metodologias.

---

## 🔹 `escolha_variaveis`

A função Python para **seleção automática de variáveis** para modelagem preditiva, combinando testes estatísticos, explicabilidade via SHAP, importância por permutação e análise incremental de desempenho.


### Requisitos

* Python **3.9+**
* polars
* scikit-learn>=1.3
* lightgbm>=4.0
* shap>=0.44
* optuna>=3.4
* imbalanced-learn>=0.11
* scipy>=1.10
* joblib>=1.3
* matplotlib>=3.7
* tqdm


### Dependências

```bash
pip install maxsciencelib[feature_engineering]
```


### Uso básico


```python
pip install maxsciencelib
pip install maxsciencelib[feature_engineering]

tabela_resultado, variaveis_selecionadas = escolha_variaveis(
    data = pl.from_pandas(df),
    nivel= 3, #default 3
    random_state = 42, #default 42
    coluna_data_ref = "DATA_REFERENCIA", # data de referência caso for utilizar o split temporal
    max_periodo_treino = 202401, 
    features =  features,
    target = "Fraude_new",
    split_aleatorio = True, #default True 
    p_valor = 0.1, #default 0.05 - quanto maior, menos rígido 
    parametro_nivel_0 = 0.1, #default 0.1 - quanto menor, menos rígido
    parametro_nivel_1 = 0.8, #default 0.1 - quanto maior, menos rígido
    parametro_nivel_2 = 0.01, #default 0.0005 - quanto menor, menos rígido
    parametro_nivel_3 = 0.0001, #default 0.00001 - quanto menor, menos rígido
    qui_quadrado = True #default False 
) 
```

## Parâmetros

A documentação completa do funcionamento da função, junto com os parâmetros estão disponíveis no arquivo hmtl no caminho **R:\\Célula de Dados e Implantação\\Ciencia\\Pastas_individuais\\Elias\\Função escolha de variáveis**

---


## 🔹 `time_features`

Função para **engenharia de atributos temporais** a partir de uma coluna de timestamp, voltada para **modelagem preditiva e análise exploratória**.

A função cria automaticamente **features de data e hora**, identifica **feriados nacionais do Brasil**, adiciona **indicadores de fim de semana**, gera **encoding cíclico** (seno e cosseno) e classifica o **período do dia**, retornando um **Polars DataFrame enriquecido**.

Para mais time_features, recomenda-se a biblioteca tsfresh.

### Funcionalidades

* Extração de atributos temporais básicos (mês, dia, hora, dia da semana)
* Identificação automática de **feriados nacionais brasileiros**
* Flag de **fim de semana**
* **Encoding cíclico** para:

  * Mês do ano
  * Dia da semana
* Classificação do **período do dia** (madrugada, manhã, tarde, noite)
* Implementação performática com **Polars**


### Uso básico

```python
from maxsciencelib import time_features

df_feat = time_features(
    df=base_eventos,
    ts_col="data_evento"
)
```

### Retorno

A função retorna:

```python
polars.DataFrame
```

Com novas colunas adicionadas à base original.

### Features geradas

| Coluna          | Descrição                                    |
| --------------- | -------------------------------------------- |
| `mes`           | Mês do ano (1–12)                            |
| `dia`           | Dia do mês (1–31)                            |
| `dia_semana`    | Dia da semana (0=Seg, …,6=Dom)               |
| `hora`          | Hora do dia (0–23)                           |
| `feriado`       | Indica se a data é feriado nacional (Brasil) |
| `fim_de_semana` | Indica sábado ou domingo                     |
| `mes_sin`       | Seno do mês (encoding cíclico)               |
| `mes_cos`       | Cosseno do mês (encoding cíclico)            |
| `dow_sin`       | Seno do dia da semana                        |
| `dow_cos`       | Cosseno do dia da semana                     |
| `periodo_dia`   | Madrugada / Manhã / Tarde / Noite            |



### Parâmetros

| Parâmetro | Tipo               | Descrição                                    |
| --------- | ------------------ | -------------------------------------------- |
| `df`      | `polars.DataFrame` | Base de dados contendo a coluna de timestamp |
| `ts_col`  | `str`              | Nome da coluna de data/hora                  |


---












Segue a **documentação da função `chassi_features`**, no **mesmo padrão das anteriores**, pronta para uso em README ou documentação da sua biblioteca.

---

## 🔹 `chassi_features`

Função Python para **extração de features estruturadas a partir do número de chassi (VIN)**, retornando informações relevantes para **análise veicular, modelagem e feature engineering**.

A função valida o VIN conforme o padrão internacional (ISO 3779), normaliza o valor e extrai automaticamente **continente/país de origem**, **fabricante (WMI)** e **ano modelo**, considerando corretamente os **ciclos de 30 anos** do código de ano do VIN.


### Funcionalidades

* Validação do VIN (17 caracteres, padrão internacional)
* Normalização automática (upper + trim)
* Extração do **continente / país de origem**
* Extração do **fabricante (WMI – World Manufacturer Identifier)**
* Cálculo correto do **ano modelo** considerando ciclos de 30 anos
* Retorno direto em **DataFrame Pandas**
* Tratamento seguro de valores inválidos (retorno `None`)

---

### Requisitos

* Python **3.10+**
* **pandas**


### Uso básico

```python
from maxsciencelib.veiculos import chassi_features

df = pd.DataFrame({
    "vin": [
        "9BWZZZ377VT004251",
        "1HGCM82633A004352",
        "vin_invalido",
        None
    ]
})

df = chassi_features(df, col_vin="vin")

df
```

### Retorno

A função retorna o **DataFrame original enriquecido** com três novas colunas:

| Coluna       | Descrição                                                        |
| ------------ | ---------------------------------------------------------------- |
| `continente` | Continente ou país de origem do veículo                          |
| `fabricante` | Fabricante identificado pelo WMI (3 primeiros caracteres do VIN) |
| `ano_modelo` | Ano modelo estimado a partir do VIN                              |


### Parâmetros

| Parâmetro | Tipo           | Descrição                                          |
| --------- | -------------- | -------------------------------------------------- |
| `df`      | `pd.DataFrame` | DataFrame contendo a coluna de VIN                 |
| `col_vin` | `str`          | Nome da coluna que contém o número de chassi (VIN) |


### Validação do VIN

A função considera válido apenas VINs que:

* Possuem exatamente **17 caracteres**
* Contêm apenas caracteres alfanuméricos permitidos
* **Excluem** letras inválidas: `I`, `O`, `Q`

VINs inválidos ou ausentes retornam `None` para todas as features.


### Ano modelo — lógica aplicada

* O **10º caractere** do VIN define o código do ano
* O código segue a sequência:

```text
ABCDEFGHJKLMNPRSTVWXY123456789
```

* O cálculo considera ciclos de **30 anos**
* O ano retornado é o **mais recente possível**, sem ultrapassar o ano atual

Exemplo:

| Código | Ano base | Anos possíveis | Ano escolhido |
| ------ | -------- | -------------- | ------------- |
| `A`    | 1980     | 1980, 2010     | 2010          |
| `Y`    | 2000     | 2000, 2030*    | 2000          |

* Anos futuros são descartados.

---








# machine_learning

Módulo Python para **Machine Learning**, com funções relacionadas a criação e monitoramento de modelos, com métricas desenvolvidas pelo time, de modo a padronizar resultados e metodologias.


---

## 🔹 `monitorar_degradacao`

Função Python para **monitoramento de degradação de variáveis ao longo do tempo**, calculando métricas clássicas de **estabilidade e poder discriminativo** — **KS (Kolmogorov-Smirnov)** e **PSI (Population Stability Index)**.

A função percorre automaticamente todas as **variáveis numéricas** do DataFrame, calcula as métricas por período e, opcionalmente, gera **gráficos interativos em Plotly** para acompanhamento visual das variáveis mais relevantes.


### Funcionalidades

* Cálculo de **KS** por variável e período
* Cálculo de **PSI** por variável e período
* Uso do **primeiro período como base de referência** para o PSI
* Suavização temporal via **média móvel**
* Seleção automática das **variáveis numéricas**
* Exclusão de colunas indesejadas
* Monitoramento visual das **Top N variáveis**
* Gráficos interativos com **eixo duplo (KS e PSI)**
* Retorno sempre em **DataFrame Pandas**

### Requisitos

* Python **3.10+**
* **pandas**
* **numpy**
* **scipy**
* **plotly**

### Uso básico

```python
from maxsciencelib import monitorar_degradacao

df_metricas = monitorar_degradacao(
    df=df_modelo,
    data_col="data_ref",
    target_col="target"
)

df_metricas.head()
```

### Uso com exclusão de colunas

```python
df_metricas = monitorar_degradacao(
    df=df_modelo,
    data_col="data_ref",
    target_col="target",
    excluir=["id_cliente", "score_final"]
)
```


### Uso sem geração de gráficos

```python
df_metricas = monitorar_degradacao(
    df=df_modelo,
    data_col="data_ref",
    target_col="target",
    plotar=False
)
```


### Retorno

O retorno da função será um objeto:

```python
pandas.DataFrame
```

Com as colunas:

| Coluna     | Descrição                             |
| ---------- | ------------------------------------- |
| `periodo`  | Período de referência                 |
| `variavel` | Nome da variável numérica             |
| `KS`       | Estatística KS da variável no período |
| `PSI`      | Population Stability Index no período |


## 🖼️ Exemplo visual


![Exemplo do Plot de monitoramento](https://raw.githubusercontent.com/dantunesc/MaxScienceLib/main/plot_monitoramento.png)  


### Parâmetros

| Parâmetro    | Tipo                | Descrição                                      |
| ------------ | ------------------- | ---------------------------------------------- |
| `df`         | `pd.DataFrame`      | DataFrame contendo os dados do modelo          |
| `data_col`   | `str`               | Coluna de data ou período                      |
| `target_col` | `str`               | Coluna binária do target (`0` / `1`)           |
| `excluir`    | `list[str] \| None` | Lista de colunas a serem excluídas da análise  |
| `bins`       | `int`               | Número de bins usados no cálculo do PSI        |
| `top_n`      | `int`               | Quantidade de variáveis exibidas nos gráficos  |
| `window`     | `int`               | Janela da média móvel para suavização temporal |
| `ks_ref`     | `float`             | Linha de referência para KS no gráfico         |
| `psi_ref`    | `float`             | Linha de referência para PSI no gráfico        |
| `plotar`     | `bool`              | Se `True`, gera gráficos interativos           |


### Interpretação das métricas (referência)

* **KS**

  * `> 0.30` → bom poder discriminativo
  * Queda consistente → possível degradação do modelo

* **PSI**

  * `< 0.10` → população estável
  * `0.10 – 0.25` → alerta
  * `> 0.25` → mudança significativa de população








 
---


# analise-exploratoria

Módulo Python para **análise exploratória, avaliação e diagnóstico de modelos de classificação**, com foco em **métricas estatísticas, visualizações interpretáveis e relatórios prontos para tomada de decisão**.

O módulo abstrai cálculos comuns de avaliação de modelos (ROC, AUC, matriz de confusão, métricas clássicas, análise por decis e threshold), entregando **gráficos padronizados e relatório textual** a partir de **uma única função**.


## Instalação

```bash
pip install maxsciencelib[analise_exploratoria]
```

## Funcionalidades

Atualmente, o módulo contém:

### 🔹 `relatorio_modelo`

Função para **avaliação completa de modelos de classificação binária**, incluindo:

* Curva **ROC** e cálculo de **AUC**
* **Matriz de confusão**
* Métricas clássicas de classificação
* Distribuição de scores com **threshold configurável**
* **Precisão por decil** (análise de poder discriminatório)
* Comparação com a **taxa base**
* Relatório textual consolidado
* Visualização padronizada em um único painel (2x2)

Outras funções de análise exploratória poderão ser adicionadas ao módulo futuramente.


## 🖼️ Exemplo visual


  
![Exemplo de Relatório do Modelo](https://raw.githubusercontent.com/dantunesc/MaxScienceLib/main/plot_modelo.png)  



## Requisitos

* Python **3.9+** (recomendado 3.10+)
* Modelo de classificação com método `predict_proba`

Dependências principais:

* `numpy`
* `pandas`
* `matplotlib`
* `seaborn`
* `scikit-learn`


## Uso básico

```python
from maxsciencelib import relatorio_modelo

relatorio_modelo(
    model=modelo_treinado,
    X_test=X_test,
    y_test=y_test,
    nome_modelo="Modelo de Fraude",
    threshold=0.3
)
```

## Retorno

A função **não retorna objetos**, mas produz:

* **Painel gráfico** com:

  * Curva ROC
  * Matriz de confusão
  * Distribuição de scores
  * Precisão por decil
* **Relatório textual** impresso no console com métricas consolidadas

---

## Parâmetros

| Parâmetro     | Tipo           | Descrição                                                    |
| ------------- | -------------- | ------------------------------------------------------------ |
| `model`       | objeto sklearn | Modelo treinado com método `predict_proba`                   |
| `X_test`      | DataFrame      | Conjunto de variáveis explicativas de teste                  |
| `y_test`      | Series / array | Variável resposta real                                       |
| `nome_modelo` | `str`          | Nome exibido no relatório e nos gráficos                     |
| `decil`       | `int`          | Número de decis para análise de precisão (default = 10)      |
| `threshold`   | `float`        | Limiar de decisão para classificação binária (default = 0.5) |

---


## 🔹 `plot_ks_colunas`

Função para **análise exploratória e poder discriminatório de variáveis numéricas**, baseada na **estatística Kolmogorov-Smirnov (KS)**.

A função compara a distribuição de cada variável entre as classes da variável alvo (`0` vs `1`), exibindo **gráficos de densidade (KDE)** lado a lado e o **valor do KS diretamente no título do gráfico**, facilitando a identificação de variáveis mais relevantes para separação de classes.



### Funcionalidades

* Cálculo automático da **estatística KS** por variável
* Comparação visual das distribuições entre classes (`target = 0` vs `1`)
* Suporte a **múltiplas variáveis simultaneamente**
* Layout automático em grade (até 2 gráficos por linha)
* Exibição da **quantidade de observações por classe** na legenda
* Tratamento de colunas com dados insuficientes
* Integração nativa com **Polars DataFrame**



### 🖼️ Exemplo visual

 
![Exemplo de KS por Variável](https://raw.githubusercontent.com/dantunesc/MaxScienceLib/main/plot_ks.png)

### Uso básico

```python
from maxsciencelib import plot_ks_colunas

plot_ks_colunas(
    df=base_modelagem,
    lista_colunas=["idade", "valor_transacao", "score_interno"],
    coluna_target="acionou"
)
```


### Retorno

A função **não retorna objetos**, mas produz:

* **Gráficos KDE** comparando as distribuições por classe
* **Valor do KS** exibido no título de cada gráfico
* **Contagem de amostras por classe** na legenda



### Parâmetros

| Parâmetro       | Tipo               | Descrição                                      |
| --------------- | ------------------ | ---------------------------------------------- |
| `df`            | `polars.DataFrame` | Base de dados contendo as variáveis e o target |
| `lista_colunas` | `list[str]`        | Lista de colunas numéricas a serem avaliadas   |
| `coluna_target` | `str`              | Nome da coluna binária alvo (valores 0 e 1)    |



---

## 🔹 `plot_lift_barplot`

Função para **análise de lift por categoria**, amplamente utilizada em problemas de **classificação, fraude, risco e propensão**, permitindo identificar **categorias com maior concentração relativa do evento de interesse** em comparação à base total.

A função gera um **gráfico de barras interativo (Plotly)** com o valor de *lift* por categoria, facilitando análises exploratórias e apresentações executivas.



### Funcionalidades

* Cálculo automático do **lift por categoria**
* Comparação entre:

  * Distribuição da **base total**
  * Distribuição do **grupo alvo** (`target`)
* Filtro por **quantidade mínima de eventos**
* Ordenação automática por lift (decrescente)
* Suporte a **ordem customizada** de categorias
* Renomeação opcional de rótulos
* Gráfico **interativo** com Plotly
* Compatível com dashboards (Streamlit, Jupyter, etc.)


### 🖼️ Exemplo visual


![Exemplo de Lift por Categoria](https://raw.githubusercontent.com/dantunesc/MaxScienceLib/main/plot_lift.png)


### Uso básico

```python
from maxsciencelib import plot_lift_barplot

fig = plot_lift_barplot(
    df=base_modelagem,
    category_col="segmento_cliente",
    split_col="acionou",
    target_val=1,
    min_target_count=30
)

fig.show()
```


### Retorno

A função retorna:

```python
plotly.graph_objects.Figure
```

Permitindo:

* exibição interativa
* exportação para HTML / PNG
* integração direta em dashboards

---

### Parâmetros

| Parâmetro          | Tipo      | Descrição                                                          |
| ------------------ | --------- | ------------------------------------------------------------------ |
| `df`               | DataFrame | Base de dados com as categorias e variável alvo                    |
| `category_col`     | `str`     | Coluna categórica a ser analisada                                  |
| `split_col`        | `str`     | Coluna alvo (binária ou categórica)                                |
| `target_val`       | `int/str` | Valor do target considerado como evento de interesse (default = 1) |
| `min_target_count` | `int`     | Contagem mínima de eventos por categoria                           |
| `order`            | `list`    | Ordem customizada das categorias                                   |
| `rename_map`       | `dict`    | Dicionário para renomear categorias no eixo X                      |
| `template`         | `str`     | Template visual do Plotly (default = `"plotly_white"`)             |


---

## 🔹 `plot_correlacoes`

Função para **análise de correlação e redundância entre variáveis**, combinando **correlações lineares, monotônicas e dependência não linear**, com foco em **seleção de features e diagnóstico de multicolinearidade**.

A função gera uma **matriz de correlação visual (heatmap)** entre as variáveis explicativas, calcula a correlação de cada feature com o target e identifica **pares altamente correlacionados**, auxiliando decisões de remoção, agrupamento ou regularização de variáveis.



### Funcionalidades

* Visualização da **matriz de correlação de Pearson** entre as features
* Cálculo de correlação com o target usando:

  * **Pearson** (linear)
  * **Spearman** (monotônica)
  * **Mutual Information** (não linear)
* Geração de tabela resumo de relevância das variáveis
* Identificação automática de **variáveis redundantes** acima de um limiar configurável
* Retorno estruturado para uso direto em pipelines de feature selection




### Uso básico

```python
from maxsciencelib import plot_correlacoes

resumo, redundancias = plot_correlacoes(
    df=df_modelagem,
    target="FRAUDE",
    corr_thresh=0.7
)
```



### Retorno

A função retorna **dois objetos**:

```python
resumo, redundancias
```

### 🖼️ Exemplo visual

![Heatmap de Correlações](https://raw.githubusercontent.com/dantunesc/MaxScienceLib/main/plot_correlacao.png)

#### `resumo`

```python
pandas.DataFrame
```

Tabela contendo, para cada variável:

* Correlação de Pearson com o target
* Correlação de Spearman com o target
* Mutual Information com o target

Ordenada por **Mutual Information (decrescente)**.

#### `redundancias`

```python
pandas.DataFrame
```

Tabela com pares de variáveis altamente correlacionadas entre si, contendo:

* `var1`
* `var2`
* `corr_abs` (valor absoluto da correlação)



### Parâmetros

| Parâmetro     | Tipo               | Descrição                                                                   |
| ------------- | ------------------ | --------------------------------------------------------------------------- |
| `df`          | `pandas.DataFrame` | Base de dados contendo features numéricas e o target                        |
| `target`      | `str`              | Nome da variável alvo                                                       |
| `corr_thresh` | `float`            | Limiar de correlação absoluta para identificar redundâncias (default = 0.9) |


---

## Licença

The MIT License (MIT)

## Autores

Daniel Antunes Cordeiros