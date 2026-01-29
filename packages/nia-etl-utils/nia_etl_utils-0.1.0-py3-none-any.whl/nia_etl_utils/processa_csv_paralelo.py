"""Processamento paralelo de arquivos CSV grandes."""
import sys
from pathlib import Path
from typing import Callable, List, Optional
from multiprocessing import Pool, cpu_count

import pandas as pd
from loguru import logger


def calcular_chunksize(caminho_arquivo: str) -> int:
    """Calcula tamanho ideal de chunk baseado no tamanho do arquivo.

    Args:
        caminho_arquivo: Caminho do arquivo CSV.

    Returns:
        int: Tamanho do chunk otimizado.

    Examples:
        >>> chunksize = calcular_chunksize("dados_grandes.csv")
        >>> # Arquivo < 500MB: 10000 linhas
        >>> # Arquivo 500MB-2GB: 5000 linhas
        >>> # Arquivo 2-5GB: 2000 linhas
        >>> # Arquivo > 5GB: 1000 linhas
    """
    tamanho_mb = Path(caminho_arquivo).stat().st_size / (1024 * 1024)

    if tamanho_mb < 500:
        return 10000
    elif tamanho_mb < 2000:
        return 5000
    elif tamanho_mb < 5000:
        return 2000
    else:
        return 1000


def _processar_chunk(args: tuple) -> pd.DataFrame:
    """Processa um chunk aplicando transformações.

    Função interna usada pelo Pool.imap().
    """
    chunk, colunas_para_tratar, func_tratar_texto, normalizar_colunas = args

    # Aplica transformação nas colunas especificadas
    for coluna in colunas_para_tratar:
        if coluna in chunk.columns:
            chunk[coluna] = chunk[coluna].apply(func_tratar_texto)
        else:
            logger.warning(f"Coluna '{coluna}' não encontrada no chunk")

    # Normaliza nomes de colunas se solicitado
    if normalizar_colunas:
        chunk.columns = [col.lower() for col in chunk.columns]

    return chunk


def processar_csv_paralelo(
    caminho_entrada: str,
    caminho_saida: str,
    colunas_para_tratar: List[str],
    funcao_transformacao: Callable,
    chunksize: Optional[int] = None,
    normalizar_colunas: bool = True,
    remover_entrada: bool = False,
    num_processos: Optional[int] = None
) -> None:
    """Processa CSV grande em paralelo aplicando transformações por chunk.

    Args:
        caminho_entrada: Arquivo CSV de entrada.
        caminho_saida: Arquivo CSV de saída.
        colunas_para_tratar: Lista de colunas para aplicar transformação.
        funcao_transformacao: Função que recebe valor e retorna valor transformado.
        chunksize: Tamanho do chunk. Se None, calcula automaticamente.
        normalizar_colunas: Se True, converte nomes de colunas para lowercase.
        remover_entrada: Se True, remove arquivo de entrada após processar.
        num_processos: Número de processos paralelos. Se None, usa cpu_count().

    Raises:
        SystemExit: Se arquivo de entrada não existe ou erro no processamento.

    Examples:
        >>> from nia_etl_utils import processar_csv_paralelo
        >>>
        >>> def limpar_texto(texto):
        ...     return texto.strip().upper()
        >>>
        >>> processar_csv_paralelo(
        ...     caminho_entrada="dados_brutos.csv",
        ...     caminho_saida="dados_limpos.csv",
        ...     colunas_para_tratar=["nome", "descricao"],
        ...     funcao_transformacao=limpar_texto,
        ...     remover_entrada=True
        ... )
    """
    caminho_entrada_path = Path(caminho_entrada)

    # Validação de entrada
    if not caminho_entrada_path.exists():
        logger.error(f"Arquivo de entrada não encontrado: {caminho_entrada}")
        sys.exit(1)

    try:
        logger.info(f"Iniciando processamento paralelo: {caminho_entrada}")

        # Define chunksize
        if chunksize is None:
            chunksize = calcular_chunksize(caminho_entrada)

        logger.info(f"Chunksize: {chunksize} linhas | Processos: {num_processos or cpu_count()}")

        # Processamento paralelo
        primeiro_chunk = True

        with Pool(processes=num_processos or cpu_count()) as pool:
            reader = pd.read_csv(caminho_entrada, chunksize=chunksize)

            # Prepara tasks para processamento paralelo
            tasks = [
                (chunk, colunas_para_tratar, funcao_transformacao, normalizar_colunas)
                for chunk in reader
            ]

            # Processa chunks em paralelo
            for i, chunk_processado in enumerate(pool.imap(_processar_chunk, tasks), start=1):
                logger.info(f"Escrevendo chunk {i} ({len(chunk_processado)} linhas)")

                chunk_processado.to_csv(
                    caminho_saida,
                    mode='w' if primeiro_chunk else 'a',
                    header=primeiro_chunk,
                    index=False
                )
                primeiro_chunk = False

        logger.success(f"Processamento concluído: {caminho_saida}")

        # Remove arquivo de entrada se solicitado
        if remover_entrada:
            try:
                caminho_entrada_path.unlink()
                logger.info(f"Arquivo de entrada removido: {caminho_entrada}")
            except Exception as e:
                logger.warning(f"Falha ao remover arquivo de entrada: {e}")

    except Exception as error:
        logger.exception(f"Erro no processamento paralelo: {error}")
        sys.exit(1)
