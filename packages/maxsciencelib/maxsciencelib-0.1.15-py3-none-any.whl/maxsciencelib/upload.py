# maxsciencelib/upload.py

import os
from typing import List


def upload_sharepoint(
    url_sharepoint: str,
    diretorio: str,
    tempo_espera_fim: int = 20,
    timeout: int = 30
) -> None:
    """
    Realiza upload automático de arquivos para um diretório do SharePoint
    utilizando Selenium + Edge.
    """

    # IMPORTS LAZY (obrigatório para dependência opcional)
    import time
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    if not os.path.isdir(diretorio):
        raise FileNotFoundError(f"Diretório não encontrado: {diretorio}")

    arquivos: List[str] = [
        os.path.join(diretorio, f)
        for f in os.listdir(diretorio)
        if os.path.isfile(os.path.join(diretorio, f))
    ]

    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo encontrado em: {diretorio}")

    options = Options()
    options.add_argument("--start-maximized")

    driver = webdriver.Edge(options=options)
    wait = WebDriverWait(driver, timeout)

    try:
        driver.get(url_sharepoint)

        def clicar(xpath: str):
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath))).click()

        clicar("//span[text()='Carregar']")
        clicar("//button[.//span[text()='Arquivos']]")

        input_file = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )
        input_file.send_keys("\n".join(arquivos))

        try:
            wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[contains(text(), 'Substituir tudo')]]")
                )
            ).click()
        except Exception:
            pass

        time.sleep(tempo_espera_fim)

    except Exception as e:
        raise RuntimeError(f"Erro ao realizar upload no SharePoint: {e}") from e

    finally:
        driver.quit()
