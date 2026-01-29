"""Módulo para exportação de DataFrame para CSV.

Fornece funções utilitárias para salvar DataFrames em formato CSV com
nomenclatura padronizada, logging adequado e tratamento de erros.

Examples:
    Exportação simples:

    >>> from nia_etl_utils import exportar_para_csv
    >>> import pandas as pd
    >>> df = pd.DataFrame({"id": [1, 2], "valor": [100, 200]})
    >>> caminho = exportar_para_csv(df, "vendas", "2025_01_20", "/tmp/dados")

    Extração e exportação:

    >>> from nia_etl_utils import extrair_e_exportar_csv
    >>> def extrair_clientes():
    ...     return pd.DataFrame({"id": [1, 2], "nome": ["Ana", "João"]})
    >>> resultado = extrair_e_exportar_csv(
    ...     nome_extracao="clientes",
    ...     funcao_extracao=extrair_clientes,
    ...     data_extracao="2025_01_20",
    ...     diretorio_base="/tmp/dados"
    ... )

    Múltiplas extrações:

    >>> extractions = [
    ...     {"nome": "clientes", "funcao": extrair_clientes},
    ...     {"nome": "vendas", "funcao": extrair_vendas},
    ... ]
    >>> resultados = exportar_multiplos_csv(extractions, "2025_01_20", "/tmp")
"""

from collections.abc import Callable
from pathlib import Path

import pandas as pd
from loguru import logger

from .exceptions import (
    EscritaArquivoError,
    ExtracaoError,
    ExtracaoVaziaError,
    ValidacaoError,
)
from .results import ResultadoExtracao, ResultadoLote


def exportar_para_csv(
    df: pd.DataFrame,
    nome_arquivo: str,
    data_extracao: str,
    diretorio_base: str
) -> str:
    """Salva um DataFrame como arquivo CSV.

    Cria o diretório de destino se não existir e salva o DataFrame
    com nomenclatura padronizada: {nome_arquivo}_{data_extracao}.csv

    Args:
        df: DataFrame a ser salvo. Não pode ser None ou vazio.
        nome_arquivo: Nome base do arquivo (sem extensão e sem data).
        data_extracao: Data no formato string para compor o nome
            do arquivo (ex: "2025_01_19").
        diretorio_base: Caminho do diretório onde o arquivo será salvo.
            Será criado se não existir.

    Returns:
        Caminho absoluto do arquivo CSV salvo.

    Raises:
        ExtracaoVaziaError: Se df for None ou vazio.
        ValidacaoError: Se nome_arquivo for vazio ou apenas espaços.
        EscritaArquivoError: Se houver erro de permissão ou sistema
            ao salvar o arquivo.

    Examples:
        Exportação básica:

        >>> import pandas as pd
        >>> df = pd.DataFrame({"id": [1, 2], "valor": [100, 200]})
        >>> caminho = exportar_para_csv(
        ...     df=df,
        ...     nome_arquivo="vendas",
        ...     data_extracao="2025_01_19",
        ...     diretorio_base="/tmp/dados"
        ... )
        >>> print(caminho)
        /tmp/dados/vendas_2025_01_19.csv

        Com tratamento de erro:

        >>> from nia_etl_utils.exceptions import ExtracaoVaziaError
        >>> try:
        ...     exportar_para_csv(pd.DataFrame(), "vazio", "2025_01_19", "/tmp")
        ... except ExtracaoVaziaError:
        ...     print("DataFrame estava vazio")
    """
    # Validações
    if df is None or df.empty:
        raise ExtracaoVaziaError(nome_arquivo)

    if not nome_arquivo or not nome_arquivo.strip():
        raise ValidacaoError(
            "Nome do arquivo não pode ser vazio",
            details={"parametro": "nome_arquivo", "valor": nome_arquivo}
        )

    try:
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

    except PermissionError as e:
        raise EscritaArquivoError(
            f"Sem permissão para salvar arquivo em '{diretorio_base}'",
            details={"diretorio": diretorio_base, "erro": str(e)}
        ) from e
    except OSError as e:
        raise EscritaArquivoError(
            f"Erro do sistema ao salvar CSV em '{diretorio_base}'",
            details={"diretorio": diretorio_base, "erro": str(e)}
        ) from e


def extrair_e_exportar_csv(
    nome_extracao: str,
    funcao_extracao: Callable[[], pd.DataFrame],
    data_extracao: str,
    diretorio_base: str,
) -> ResultadoExtracao:
    """Executa função de extração e salva resultado como CSV.

    Orquestra o fluxo completo: executa a função fornecida, valida
    o DataFrame retornado e persiste como CSV no diretório especificado.

    Args:
        nome_extracao: Identificador da extração. Usado no nome do arquivo
            e nos logs.
        funcao_extracao: Callable sem argumentos que retorna pd.DataFrame.
            Será executada dentro de try/except para captura de erros.
        data_extracao: Data no formato string para compor o nome do arquivo
            (ex: "2025_01_19").
        diretorio_base: Caminho do diretório onde o arquivo será salvo.

    Returns:
        ResultadoExtracao contendo:
            - nome: Identificador da extração
            - caminho: Path do arquivo salvo
            - linhas: Quantidade de registros extraídos
            - sucesso: True se exportação completou
            - erro: None se sucesso, mensagem se falha
            - colunas: Quantidade de colunas
            - tamanho_bytes: Tamanho do arquivo

    Raises:
        ExtracaoVaziaError: Se a função retornar DataFrame vazio ou None.
        ExtracaoError: Se houver erro na execução da função de extração.
        ValidacaoError: Se parâmetros de exportação forem inválidos.
        EscritaArquivoError: Se houver erro ao persistir o arquivo.

    Examples:
        Extração simples:

        >>> def extrair_clientes():
        ...     return pd.DataFrame({"id": [1, 2], "nome": ["Ana", "João"]})
        ...
        >>> resultado = extrair_e_exportar_csv(
        ...     nome_extracao="clientes",
        ...     funcao_extracao=extrair_clientes,
        ...     data_extracao="2025_01_19",
        ...     diretorio_base="/tmp/dados"
        ... )
        >>> resultado.sucesso
        True
        >>> resultado.linhas
        2

        Tratando extração vazia:

        >>> from nia_etl_utils.exceptions import ExtracaoVaziaError
        >>> def extrair_vazia():
        ...     return pd.DataFrame()
        ...
        >>> try:
        ...     extrair_e_exportar_csv(
        ...         nome_extracao="vazia",
        ...         funcao_extracao=extrair_vazia,
        ...         data_extracao="2025_01_19",
        ...         diretorio_base="/tmp/dados"
        ...     )
        ... except ExtracaoVaziaError as e:
        ...     print(f"Esperado: {e.nome_extracao}")
        Esperado: vazia
    """
    logger.info(f"Iniciando extração: {nome_extracao}")

    # Executa função de extração
    try:
        df_extraido = funcao_extracao()
    except Exception as e:
        raise ExtracaoError(
            f"Erro ao executar extração '{nome_extracao}'",
            details={"extracao": nome_extracao, "erro": str(e)}
        ) from e

    # Valida resultado
    if df_extraido is None or df_extraido.empty:
        raise ExtracaoVaziaError(nome_extracao)

    # Exporta para CSV
    caminho = exportar_para_csv(
        df=df_extraido,
        nome_arquivo=nome_extracao,
        data_extracao=data_extracao,
        diretorio_base=diretorio_base,
    )

    # Coleta métricas
    tamanho_bytes = Path(caminho).stat().st_size

    logger.success(f"Extração concluída: {nome_extracao}")

    return ResultadoExtracao(
        nome=nome_extracao,
        caminho=caminho,
        linhas=len(df_extraido),
        sucesso=True,
        colunas=len(df_extraido.columns),
        tamanho_bytes=tamanho_bytes
    )


def exportar_multiplos_csv(
    extractions: list[dict],
    data_extracao: str,
    diretorio_base: str,
    ignorar_vazios: bool = True
) -> ResultadoLote:
    """Executa múltiplas extrações em lote e salva cada uma como CSV.

    Itera sobre a lista de extrações, executando cada uma sequencialmente.
    O comportamento ao encontrar extrações vazias é controlado pelo
    parâmetro ignorar_vazios.

    Args:
        extractions: Lista de dicionários, cada um contendo:
            - nome (str): Identificador da extração
            - funcao (Callable[[], pd.DataFrame]): Função de extração
        data_extracao: Data no formato string para compor os nomes dos
            arquivos (ex: "2025_01_19").
        diretorio_base: Caminho do diretório onde os arquivos serão salvos.
        ignorar_vazios: Comportamento quando uma extração retorna vazio.
            Se True (default), loga warning e continua com as próximas.
            Se False, levanta ExtracaoVaziaError imediatamente.

    Returns:
        ResultadoLote contendo lista de ResultadoExtracao e métricas
        consolidadas (total, sucesso, falhas, taxa de sucesso).

    Raises:
        ExtracaoVaziaError: Se ignorar_vazios=False e alguma extração
            retornar DataFrame vazio ou None.
        ExtracaoError: Se houver erro crítico em alguma extração
            (não relacionado a dados vazios).

    Examples:
        Múltiplas extrações tolerando vazios:

        >>> extractions = [
        ...     {"nome": "clientes", "funcao": extrair_clientes},
        ...     {"nome": "vendas", "funcao": extrair_vendas},
        ... ]
        >>> lote = exportar_multiplos_csv(
        ...     extractions=extractions,
        ...     data_extracao="2025_01_19",
        ...     diretorio_base="/tmp/dados"
        ... )
        >>> print(f"{lote.sucesso}/{lote.total} bem-sucedidas")
        >>> for r in lote.extracoes_sucesso:
        ...     print(f"{r.nome}: {r.linhas} linhas")

        Falhando na primeira extração vazia:

        >>> try:
        ...     exportar_multiplos_csv(
        ...         extractions=extractions,
        ...         data_extracao="2025_01_19",
        ...         diretorio_base="/tmp/dados",
        ...         ignorar_vazios=False
        ...     )
        ... except ExtracaoVaziaError:
        ...     print("Pipeline interrompido por extração vazia")

        Verificando falhas:

        >>> lote = exportar_multiplos_csv(extractions, "2025_01_19", "/tmp")
        >>> if not lote.todos_sucesso:
        ...     for falha in lote.extracoes_falhas:
        ...         logger.warning(f"{falha.nome}: {falha.erro}")
    """
    lote = ResultadoLote()
    logger.info(f"Iniciando {len(extractions)} extrações em lote")

    for extracao in extractions:
        nome = extracao["nome"]
        funcao = extracao["funcao"]

        try:
            resultado = extrair_e_exportar_csv(
                nome_extracao=nome,
                funcao_extracao=funcao,
                data_extracao=data_extracao,
                diretorio_base=diretorio_base,
            )
            lote.adicionar(resultado)

        except ExtracaoVaziaError as e:
            if ignorar_vazios:
                logger.warning(str(e))
                lote.adicionar(ResultadoExtracao(
                    nome=nome,
                    caminho=None,
                    linhas=0,
                    sucesso=False,
                    erro=str(e)
                ))
            else:
                raise

    logger.info(
        f"Extrações concluídas: {lote.sucesso}/{lote.total} bem-sucedidas "
        f"({lote.taxa_sucesso:.0%})"
    )

    return lote
