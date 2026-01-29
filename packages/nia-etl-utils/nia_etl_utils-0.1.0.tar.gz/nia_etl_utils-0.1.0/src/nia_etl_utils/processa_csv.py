"""Módulo para exportação de DataFrame para CSV.

Fornece funções utilitárias para salvar DataFrames em formato CSV com
nomenclatura padronizada e logging adequado.
"""
import sys
from pathlib import Path
from typing import Callable, Optional
import pandas as pd
from loguru import logger


def exportar_para_csv(
    df: pd.DataFrame,
    nome_arquivo: str,
    data_extracao: str,
    diretorio_base: str
) -> str:
    """Salva um DataFrame como arquivo CSV.

    Args:
        df: DataFrame a ser salvo.
        nome_arquivo: Nome base do arquivo (sem extensão).
        data_extracao: Data que será usada no nome do arquivo (ex: "2025_01_19").
        diretorio_base: Diretório onde o arquivo será salvo.

    Returns:
        str: Caminho completo do arquivo salvo.

    Raises:
        SystemExit: Se houver erro ao salvar o arquivo.

    Examples:
        >>> import pandas as pd
        >>> from nia_etl_utils.processa_csv import exportar_para_csv
        >>>
        >>> df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        >>> caminho = exportar_para_csv(df, "dados", "2025_01_19", "/tmp")
        >>> # Arquivo salvo: /tmp/dados_2025_01_19.csv
    """
    try:
        # Valida inputs
        if df is None or df.empty:
            logger.warning("DataFrame vazio ou None fornecido. Nenhum arquivo será criado.")
            return ""

        if not nome_arquivo or not nome_arquivo.strip():
            logger.error("Nome do arquivo não pode ser vazio.")
            sys.exit(1)

        # Cria diretório se não existir
        diretorio = Path(diretorio_base)
        diretorio.mkdir(parents=True, exist_ok=True)

        # Monta caminho completo
        caminho_arquivo = diretorio / f"{nome_arquivo}_{data_extracao}.csv"

        # Salva CSV
        df.to_csv(caminho_arquivo, index=False, encoding='utf-8')

        # Log com informações úteis
        tamanho_kb = caminho_arquivo.stat().st_size / 1024
        logger.success(
            f"CSV salvo: {caminho_arquivo} "
            f"({len(df)} linhas, {len(df.columns)} colunas, {tamanho_kb:.2f} KB)"
        )

        return str(caminho_arquivo)

    except PermissionError as error:
        logger.error(f"Sem permissão para salvar arquivo em '{diretorio_base}': {error}")
        sys.exit(1)
    except OSError as error:
        logger.error(f"Erro do sistema ao salvar CSV em '{diretorio_base}': {error}")
        sys.exit(1)
    except Exception as error:
        logger.error(f"Erro inesperado ao salvar CSV: {error}")
        sys.exit(1)


def extrair_e_exportar_csv(
    nome_extracao: str,
    funcao_extracao: Callable[[], pd.DataFrame],
    data_extracao: str,
    diretorio_base: str,
    falhar_se_vazio: bool = False
) -> Optional[str]:
    """Executa uma função de extração e salva o resultado como CSV.

    Args:
        nome_extracao: Nome base para o arquivo CSV (sem extensão).
        funcao_extracao: Função que retorna um DataFrame.
        data_extracao: Data que será usada no nome do arquivo (ex: "2025_01_19").
        diretorio_base: Diretório onde o arquivo será salvo.
        falhar_se_vazio: Se True, encerra com sys.exit(1) quando DataFrame for vazio.
                        Se False, apenas loga warning e retorna None. Defaults to False.

    Returns:
        str: Caminho do arquivo salvo, ou None se DataFrame estiver vazio e falhar_se_vazio=False.

    Raises:
        SystemExit: Se houver erro na extração, ao salvar o arquivo,
                   ou se DataFrame for vazio e falhar_se_vazio=True.

    Examples:
        >>> from nia_etl_utils.processa_csv import extrair_e_exportar_csv
        >>>
        >>> def extrair_dados():
        ...     return pd.DataFrame({"col1": [1, 2, 3]})
        >>>
        >>> caminho = extrair_e_exportar_csv(
        ...     nome_extracao="dados_clientes",
        ...     funcao_extracao=extrair_dados,
        ...     data_extracao="2025_01_19",
        ...     diretorio_base="/tmp/dados"
        ... )
    """
    try:
        logger.info(f"Iniciando extração: {nome_extracao}")

        # Executa função de extração
        df_extraido = funcao_extracao()

        # Valida resultado
        if df_extraido is None or df_extraido.empty:
            mensagem = f"Nenhum dado retornado para extração '{nome_extracao}'"

            if falhar_se_vazio:
                logger.error(mensagem)
                sys.exit(1)
            else:
                logger.warning(mensagem)
                return None

        # Exporta para CSV
        caminho = exportar_para_csv(
            df=df_extraido,
            nome_arquivo=nome_extracao,
            data_extracao=data_extracao,
            diretorio_base=diretorio_base,
        )

        logger.success(f"Extração concluída com sucesso: {nome_extracao}")
        return caminho

    except Exception as error:
        logger.error(f"Erro ao extrair ou salvar '{nome_extracao}': {error}")
        sys.exit(1)


def exportar_multiplos_csv(
    extractions: list[dict],
    data_extracao: str,
    diretorio_base: str,
    falhar_se_vazio: bool = False
) -> dict[str, Optional[str]]:
    """Executa múltiplas extrações e salva cada uma como CSV.

    Args:
        extractions: Lista de dicionários com 'nome' e 'funcao' para cada extração.
        data_extracao: Data que será usada nos nomes dos arquivos.
        diretorio_base: Diretório onde os arquivos serão salvos.
        falhar_se_vazio: Se True, encerra quando algum DataFrame for vazio.

    Returns:
        dict: Mapeamento {nome_extracao: caminho_arquivo} para cada extração bem-sucedida.

    Examples:
        >>> from nia_etl_utils.processa_csv import exportar_multiplos_csv
        >>>
        >>> def extrair_clientes():
        ...     return pd.DataFrame({"id": [1, 2]})
        >>>
        >>> def extrair_vendas():
        ...     return pd.DataFrame({"valor": [100, 200]})
        >>>
        >>> extractions = [
        ...     {"nome": "clientes", "funcao": extrair_clientes},
        ...     {"nome": "vendas", "funcao": extrair_vendas}
        ... ]
        >>>
        >>> resultados = exportar_multiplos_csv(
        ...     extractions=extractions,
        ...     data_extracao="2025_01_19",
        ...     diretorio_base="/tmp/dados"
        ... )
    """
    resultados = {}

    logger.info(f"Iniciando {len(extractions)} extrações em lote")

    for extracao in extractions:
        nome = extracao["nome"]
        funcao = extracao["funcao"]

        caminho = extrair_e_exportar_csv(
            nome_extracao=nome,
            funcao_extracao=funcao,
            data_extracao=data_extracao,
            diretorio_base=diretorio_base,
            falhar_se_vazio=falhar_se_vazio
        )

        resultados[nome] = caminho

    sucesso = sum(1 for v in resultados.values() if v is not None)
    logger.info(f"Extrações concluídas: {sucesso}/{len(extractions)} bem-sucedidas")

    return resultados
