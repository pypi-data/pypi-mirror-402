# maxsciencelib/leitura.py

import os
import sys
import warnings
import polars as pl
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import polars as pl


# ======================================================
# LEITURA SNOWFLAKE
# ======================================================
def leitura_snowflake(
    email_corporativo: str,
    token_account: str,
    query: str
):
    """
    Executa uma query no Snowflake e retorna um DataFrame Polars.
    """

    # Imports lazy (NUNCA no topo)
    import snowflake.connector
    import polars as pl

    warnings.filterwarnings("ignore", message=".*keyring.*")

    sys_stdout, sys_stderr = sys.stdout, sys.stderr

    try:
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

        conn = snowflake.connector.connect(
            user=email_corporativo,
            account=token_account,
            database="MAXPAR",
            schema="ESTATISTICA",
            role="GL_SNOWFLAKE_ACESSO_MAX_CED_DADOS",
            warehouse="WH_USE_CED",
            authenticator="externalbrowser",
            network_timeout=600,
        )

        cursor = conn.cursor()
        try:
            cursor.execute(query)

            # Snowflake → Arrow → Polars
            arrow_table = cursor.fetch_arrow_all()
            df = pl.from_arrow(arrow_table)

        finally:
            cursor.close()

    finally:
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout, sys.stderr = sys_stdout, sys_stderr

        try:
            conn.close()
        except Exception:
            pass

    return df


# ======================================================
# LEITURA TABLEAU
# ======================================================
def leitura_tableau(
    nome_token: str,
    token_acesso: str,
    view_id: str
):
    """
    Lê uma view do Tableau Server e retorna um DataFrame Polars.
    """

    # Imports lazy
    import tableauserverclient as TSC
    import polars as pl
    import io

    warnings.filterwarnings("ignore")

    def tentar_conectar(url: str):
        tableau_auth = TSC.PersonalAccessTokenAuth(
            token_name=nome_token,
            personal_access_token=token_acesso,
            site_id=""
        )
        server = TSC.Server(url, use_server_version=True)
        server.auth.sign_in(tableau_auth)
        return server

    server = None
    try:
        try:
            server = tentar_conectar("http://tableau.autoglass.com.br/")
        except Exception:
            server = tentar_conectar("https://tableau.autoglass.com.br/")

        if server is None:
            raise ConnectionError("Não foi possível conectar ao Tableau Server.")

        view_item = server.views.get_by_id(view_id)
        server.views.populate_csv(view_item)

        csv_bytes = b"".join(view_item.csv)

        # CSV → Polars
        df = pl.read_csv(io.BytesIO(csv_bytes))
        return df

    finally:
        if server:
            server.auth.sign_out()



# ======================================================
# LEITURA FIPEs
# ======================================================

def leitura_fipe() -> pl.DataFrame:
    # ======================================================
    # 1. Leitura da base FIPE
    # ======================================================
    import polars as pl

    base_fipe = (
        pl.read_excel(
            r'R://Célula de Pesquisa/Equipe/Dados_externos/FIPE/Mensal/FIPE_mais_atualizada.xlsx'
        )
        .rename({
            'Marca': 'marca',
            'Modelo': 'modelo',
            'FIPE': 'fipe',
            'Ano': 'ano',
            'Valor': 'valor',
            'Tipo Veiculo': 'tipo_veiculo',
            'Media valor FIPE': 'media_valor_fipe',
            'SF': 'sf'
        })
    )

    # ======================================================
    # 2. Tratamento do ano
    # ======================================================
    base_fipe = (
        base_fipe
        .with_columns(
            pl.when(pl.col('ano') == 'ZERO KM')
              .then(pl.lit(2025))
              .otherwise(pl.col('ano'))
              .cast(pl.Int32)
              .alias('ano')
        )
    )

    # ======================================================
    # 3. Criação da coluna FIPE-ANO
    # ======================================================
    base_fipe = base_fipe.with_columns(
        (pl.col('fipe') + pl.lit('-') + pl.col('ano').cast(pl.Utf8))
        .alias('fipe_ano')
    )

    # ======================================================
    # 4. Cálculo dos quantis por tipo de veículo
    # ======================================================
    quantis = (
        base_fipe
        .group_by('tipo_veiculo')
        .agg([
            # Recentes (ano >= 2015)
            pl.col('valor')
              .filter(pl.col('ano') >= 2015)
              .quantile(0.50)
              .alias('q1_recente'),

            pl.col('valor')
              .filter(pl.col('ano') >= 2015)
              .quantile(0.70)
              .alias('q2_recente'),

            # Antigos (ano < 2015)
            pl.col('valor')
              .filter(pl.col('ano') < 2015)
              .quantile(0.60)
              .alias('q1_antigo')
        ])
    )

    # ======================================================
    # 5. Join dos quantis na base principal
    # ======================================================
    base = base_fipe.join(quantis, on='tipo_veiculo', how='left')

    # ======================================================
    # 6. Categorização
    # ======================================================
    base = base.with_columns(
        pl.when((pl.col('ano') < 2015) & (pl.col('valor') <= pl.col('q1_antigo')))
          .then(pl.lit('Antigo Popular'))

        .when((pl.col('ano') < 2015) & (pl.col('valor') > pl.col('q1_antigo')))
          .then(pl.lit('Antigo Premium'))

        .when((pl.col('ano') >= 2015) & (pl.col('valor') <= pl.col('q1_recente')))
          .then(pl.lit('Popular'))

        .when(
            (pl.col('ano') >= 2015) &
            (pl.col('valor') > pl.col('q1_recente')) &
            (pl.col('valor') <= pl.col('q2_recente'))
        )
          .then(pl.lit('Intermediário'))

        .when((pl.col('ano') >= 2015) & (pl.col('valor') > pl.col('q2_recente')))
          .then(pl.lit('Premium'))

        .otherwise(pl.lit(None))
        .alias('categoria')
    )

    # ======================================================
    # 7. Seleção final
    # ======================================================
    fipes_categoria = base.select([
        'fipe_ano',
        'ano',
        'marca',
        'modelo',
        'categoria'
    ])

    return fipes_categoria



def leitura_metabase(
    metabase_url: str,
    id: int | str,
    username: str,
    password: str,
    max_retries: int = 2,
    timeout: int = 30,
    verbose: bool = True
) -> Optional[pl.DataFrame]:
    """
    Autentica no Metabase e retorna os dados de um Card como Polars DataFrame.

    Parâmetros
    ----------
    metabase_url : str
        URL base do Metabase
    id : int | str
        ID do Metabase
    username : str
        Usuário do Metabase
    password : str
        Senha do Metabase
    max_retries : int, default 2
        Número máximo de retentativas em caso de erro 401
    timeout : int, default 30
        Timeout das requisições HTTP
    verbose : bool, default True
        Se True, exibe logs no console

    Retorno
    -------
    pl.DataFrame | None
    """

    import json
    import time
    import requests
    import polars as pl
    from typing import Optional

    def log(msg: str):
        if verbose:
            print(msg)

    session_id = None

    for attempt in range(max_retries + 1):
        try:
            # 🔐 Autenticação
            if session_id is None:
                auth_url = f"{metabase_url}/api/session"
                auth_payload = {
                    "username": username,
                    "password": password
                }

                auth_response = requests.post(
                    auth_url,
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(auth_payload),
                    timeout=timeout
                )
                auth_response.raise_for_status()

                session_id = auth_response.json().get("id")
                if not session_id:
                    raise RuntimeError("Session ID não retornada pelo Metabase")

                log("[Metabase] Sessão autenticada com sucesso")

            # 📊 Consulta do card
            data_url = f"{metabase_url}/api/card/{id}/query/json"
            headers = {
                "Content-Type": "application/json",
                "X-Metabase-Session": session_id
            }

            response = requests.post(
                data_url,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, list):
                raise ValueError("Resposta inesperada: esperado list[dict]")

            log(f"[Metabase] Id {id} retornado com {len(data)} linhas")

            return pl.DataFrame(data)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401 and attempt < max_retries:
                log("[Metabase] Sessão expirada. Reautenticando...")
                session_id = None
                time.sleep(1)
                continue
            else:
                log(f"[Metabase] Erro HTTP: {e}")
                return None

        except requests.exceptions.RequestException as e:
            log(f"[Metabase] Erro de requisição: {e}")
            return None

        except Exception as e:
            log(f"[Metabase] Erro inesperado: {e}")
            return None

    return None
