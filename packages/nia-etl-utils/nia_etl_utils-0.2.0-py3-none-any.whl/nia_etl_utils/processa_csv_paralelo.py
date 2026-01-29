"""Processamento paralelo de arquivos CSV grandes.

Fornece funções para processar arquivos CSV em chunks paralelos,
otimizando o uso de CPU para transformações em arquivos grandes.

Examples:
    Processamento básico:

    >>> from nia_etl_utils import processar_csv_paralelo
    >>>
    >>> def limpar_texto(texto):
    ...     if pd.isna(texto):
    ...         return texto
    ...     return texto.strip().upper()
    >>>
    >>> processar_csv_paralelo(
    ...     caminho_entrada="dados_brutos.csv",
    ...     caminho_saida="dados_limpos.csv",
    ...     colunas_para_tratar=["nome", "descricao"],
    ...     funcao_transformacao=limpar_texto
    ... )

    Com configurações customizadas:

    >>> processar_csv_paralelo(
    ...     caminho_entrada="arquivo_grande.csv",
    ...     caminho_saida="arquivo_processado.csv",
    ...     colunas_para_tratar=["texto"],
    ...     funcao_transformacao=minha_funcao,
    ...     chunksize=5000,
    ...     num_processos=4,
    ...     remover_entrada=True
    ... )
"""

from collections.abc import Callable
from multiprocessing import Pool, cpu_count
from pathlib import Path

import pandas as pd
from loguru import logger

from .exceptions import LeituraArquivoError, ProcessamentoError


def calcular_chunksize(caminho_arquivo: str) -> int:
    """Calcula tamanho ideal de chunk baseado no tamanho do arquivo.

    Retorna um tamanho de chunk otimizado para balancear uso de memória
    e eficiência de processamento paralelo.

    Args:
        caminho_arquivo: Caminho do arquivo CSV.

    Returns:
        Tamanho do chunk em número de linhas:
            - Arquivo < 500MB: 10000 linhas
            - Arquivo 500MB-2GB: 5000 linhas
            - Arquivo 2-5GB: 2000 linhas
            - Arquivo > 5GB: 1000 linhas

    Raises:
        LeituraArquivoError: Se o arquivo não existir.

    Examples:
        >>> chunksize = calcular_chunksize("dados_grandes.csv")
        >>> print(f"Usando chunks de {chunksize} linhas")
    """
    arquivo = Path(caminho_arquivo)

    if not arquivo.exists():
        raise LeituraArquivoError(
            f"Arquivo não encontrado: {caminho_arquivo}",
            details={"caminho": caminho_arquivo}
        )

    tamanho_mb = arquivo.stat().st_size / (1024 * 1024)

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

    Função interna usada pelo Pool.imap(). Não deve ser chamada
    diretamente.

    Args:
        args: Tupla contendo (chunk, colunas_para_tratar,
            func_tratar_texto, normalizar_colunas).

    Returns:
        DataFrame com transformações aplicadas.
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
    colunas_para_tratar: list[str],
    funcao_transformacao: Callable,
    chunksize: int | None = None,
    normalizar_colunas: bool = True,
    remover_entrada: bool = False,
    num_processos: int | None = None
) -> int:
    """Processa CSV grande em paralelo aplicando transformações por chunk.

    Lê o arquivo CSV em chunks, processa cada chunk em paralelo usando
    multiprocessing, e escreve o resultado no arquivo de saída.

    Args:
        caminho_entrada: Caminho do arquivo CSV de entrada.
        caminho_saida: Caminho do arquivo CSV de saída.
        colunas_para_tratar: Lista de nomes de colunas para aplicar
            a função de transformação.
        funcao_transformacao: Função que recebe um valor e retorna
            o valor transformado. Deve tratar valores nulos (None/NaN).
        chunksize: Número de linhas por chunk. Se None, calcula
            automaticamente baseado no tamanho do arquivo.
        normalizar_colunas: Se True, converte nomes de colunas para
            lowercase. Defaults to True.
        remover_entrada: Se True, remove arquivo de entrada após
            processar com sucesso. Defaults to False.
        num_processos: Número de processos paralelos. Se None, usa
            o número de CPUs disponíveis.

    Returns:
        Número total de linhas processadas.

    Raises:
        LeituraArquivoError: Se arquivo de entrada não existir.
        ProcessamentoError: Se houver erro durante o processamento.

    Examples:
        Processamento básico:

        >>> def limpar_texto(texto):
        ...     if pd.isna(texto):
        ...         return texto
        ...     return texto.strip().upper()
        >>>
        >>> linhas = processar_csv_paralelo(
        ...     caminho_entrada="dados_brutos.csv",
        ...     caminho_saida="dados_limpos.csv",
        ...     colunas_para_tratar=["nome", "descricao"],
        ...     funcao_transformacao=limpar_texto
        ... )
        >>> print(f"{linhas} linhas processadas")

        Com configurações customizadas:

        >>> linhas = processar_csv_paralelo(
        ...     caminho_entrada="arquivo_grande.csv",
        ...     caminho_saida="arquivo_processado.csv",
        ...     colunas_para_tratar=["texto"],
        ...     funcao_transformacao=minha_funcao,
        ...     chunksize=5000,
        ...     num_processos=4,
        ...     remover_entrada=True
        ... )

        Tratando erros:

        >>> from nia_etl_utils.exceptions import ProcessamentoError
        >>> try:
        ...     processar_csv_paralelo(...)
        ... except ProcessamentoError as e:
        ...     logger.error(f"Falha no processamento: {e}")
    """
    caminho_entrada_path = Path(caminho_entrada)

    # Validação de entrada
    if not caminho_entrada_path.exists():
        raise LeituraArquivoError(
            f"Arquivo de entrada não encontrado: {caminho_entrada}",
            details={"caminho": caminho_entrada}
        )

    try:
        logger.info(f"Iniciando processamento paralelo: {caminho_entrada}")

        # Define chunksize
        if chunksize is None:
            chunksize = calcular_chunksize(caminho_entrada)

        processos = num_processos or cpu_count()
        logger.info(f"Chunksize: {chunksize} linhas | Processos: {processos}")

        # Processamento paralelo
        primeiro_chunk = True
        total_linhas = 0

        with Pool(processes=processos) as pool:
            reader = pd.read_csv(caminho_entrada, chunksize=chunksize)

            # Prepara tasks para processamento paralelo
            tasks = [
                (chunk, colunas_para_tratar, funcao_transformacao, normalizar_colunas)
                for chunk in reader
            ]

            # Processa chunks em paralelo
            for i, chunk_processado in enumerate(pool.imap(_processar_chunk, tasks), start=1):
                linhas_chunk = len(chunk_processado)
                total_linhas += linhas_chunk
                logger.debug(f"Escrevendo chunk {i} ({linhas_chunk} linhas)")

                chunk_processado.to_csv(
                    caminho_saida,
                    mode='w' if primeiro_chunk else 'a',
                    header=primeiro_chunk,
                    index=False
                )
                primeiro_chunk = False

        logger.success(f"Processamento concluído: {caminho_saida} ({total_linhas} linhas)")

        # Remove arquivo de entrada se solicitado
        if remover_entrada:
            try:
                caminho_entrada_path.unlink()
                logger.info(f"Arquivo de entrada removido: {caminho_entrada}")
            except Exception as e:
                logger.warning(f"Falha ao remover arquivo de entrada: {e}")

        return total_linhas

    except pd.errors.EmptyDataError as e:
        raise ProcessamentoError(
            f"Arquivo de entrada está vazio: {caminho_entrada}",
            details={"caminho": caminho_entrada, "erro": str(e)}
        ) from e
    except pd.errors.ParserError as e:
        raise ProcessamentoError(
            f"Erro ao parsear CSV: {caminho_entrada}",
            details={"caminho": caminho_entrada, "erro": str(e)}
        ) from e
    except Exception as e:
        raise ProcessamentoError(
            f"Erro no processamento paralelo: {caminho_entrada}",
            details={"caminho": caminho_entrada, "erro": str(e)}
        ) from e
