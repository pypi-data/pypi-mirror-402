"""Módulo utilitário para configuração de logging com Loguru.

Fornece funções para configurar o logger com rotação automática,
retenção configurável e estrutura de diretórios organizada.

Examples:
    Configuração básica:

    >>> from nia_etl_utils import configurar_logger
    >>> caminho = configurar_logger("extract", "2025_01_20")
    >>> logger.info("Pipeline iniciado")

    Configuração com padrões NIA:

    >>> from nia_etl_utils import configurar_logger_padrao_nia
    >>> caminho = configurar_logger_padrao_nia("ouvidorias_etl")

    Configuração customizada:

    >>> caminho = configurar_logger(
    ...     prefixo="etl_vendas",
    ...     data_extracao="2025_01_20",
    ...     pasta_logs="/var/log/nia",
    ...     rotation="50 MB",
    ...     retention="30 days",
    ...     level="INFO"
    ... )
"""

from datetime import datetime
from pathlib import Path

from loguru import logger

from .exceptions import DiretorioError, ValidacaoError


def configurar_logger(
    prefixo: str,
    data_extracao: str,
    pasta_logs: str = "logs",
    rotation: str = "10 MB",
    retention: str = "7 days",
    level: str = "DEBUG"
) -> str:
    """Configura o logger da aplicação com Loguru.

    Cria um handler de arquivo para o logger com rotação automática
    e retenção configurável. O arquivo de log é criado em uma estrutura
    de diretórios organizada por prefixo.

    Args:
        prefixo: Nome do módulo/pipeline (ex: 'extract', 'transform', 'load').
            Usado para criar subdiretório e nomear arquivo.
        data_extracao: Data usada no nome do arquivo de log (ex: '2025_01_19').
        pasta_logs: Diretório raiz onde os logs serão armazenados.
            Defaults to "logs".
        rotation: Critério de rotação do arquivo. Pode ser tamanho
            ("10 MB", "500 KB") ou tempo ("1 day", "1 week").
            Defaults to "10 MB".
        retention: Tempo de retenção dos logs antigos antes de serem
            removidos. Defaults to "7 days".
        level: Nível mínimo de log a ser registrado. Opções: DEBUG,
            INFO, WARNING, ERROR, CRITICAL. Defaults to "DEBUG".

    Returns:
        Caminho completo do arquivo de log criado.

    Raises:
        ValidacaoError: Se prefixo ou data_extracao forem vazios.
        DiretorioError: Se houver erro ao criar diretórios de log.

    Examples:
        Configuração básica:

        >>> from nia_etl_utils import configurar_logger
        >>> from loguru import logger
        >>> caminho = configurar_logger("extract", "2025_01_19")
        >>> logger.info("Pipeline iniciado")
        >>> # Log salvo em: logs/extract/extract_2025_01_19.log

        Com configurações customizadas:

        >>> caminho = configurar_logger(
        ...     prefixo="etl_ouvidorias",
        ...     data_extracao="2025_01_19",
        ...     pasta_logs="/var/logs/nia",
        ...     rotation="50 MB",
        ...     retention="30 days",
        ...     level="INFO"
        ... )
    """
    # Validações
    if not prefixo or not prefixo.strip():
        raise ValidacaoError(
            "Prefixo não pode ser vazio",
            details={"parametro": "prefixo", "valor": prefixo}
        )

    if not data_extracao or not data_extracao.strip():
        raise ValidacaoError(
            "Data de extração não pode ser vazia",
            details={"parametro": "data_extracao", "valor": data_extracao}
        )

    try:
        # Cria estrutura de diretórios
        diretorio_log = Path(pasta_logs) / prefixo
        diretorio_log.mkdir(parents=True, exist_ok=True)

        # Define caminho do arquivo de log
        caminho_log = diretorio_log / f"{prefixo}_{data_extracao}.log"

        # Configura handler do Loguru
        logger.add(
            str(caminho_log),
            rotation=rotation,
            retention=retention,
            level=level,
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
        )

        logger.info(f"Logger configurado com sucesso. Arquivo de log: {caminho_log}")

        return str(caminho_log)

    except PermissionError as e:
        raise DiretorioError(
            f"Sem permissão para criar diretório de logs '{pasta_logs}'",
            details={"pasta": pasta_logs, "erro": str(e)}
        ) from e
    except OSError as e:
        raise DiretorioError(
            f"Erro do sistema ao configurar logger em '{pasta_logs}'",
            details={"pasta": pasta_logs, "erro": str(e)}
        ) from e


def configurar_logger_padrao_nia(nome_pipeline: str) -> str:
    """Configura logger com padrões do NIA para pipelines de produção.

    Esta é uma função de conveniência que aplica as configurações padrão
    usadas pelos pipelines ETL do NIA:
    - Rotação: 50 MB
    - Retenção: 30 dias
    - Nível: INFO (menos verboso que DEBUG)
    - Pasta: logs/ (relativa ao diretório de execução)

    Args:
        nome_pipeline: Nome do pipeline (será usado como prefixo e na data).

    Returns:
        Caminho completo do arquivo de log criado.

    Raises:
        ValidacaoError: Se nome_pipeline for vazio.
        DiretorioError: Se houver erro ao criar diretórios.

    Examples:
        >>> from nia_etl_utils import configurar_logger_padrao_nia
        >>> from loguru import logger
        >>>
        >>> caminho = configurar_logger_padrao_nia("ouvidorias_etl")
        >>> logger.info("Pipeline iniciado com configurações padrão NIA")
    """
    data_hoje = datetime.now().strftime("%Y_%m_%d")

    return configurar_logger(
        prefixo=nome_pipeline,
        data_extracao=data_hoje,
        pasta_logs="logs",
        rotation="50 MB",
        retention="30 days",
        level="INFO"
    )


def remover_handlers_existentes() -> None:
    """Remove todos os handlers existentes do logger.

    Útil quando você precisa reconfigurar o logger do zero ou quando está
    rodando múltiplos scripts em sequência que configuram o logger.

    Note:
        Após chamar esta função, apenas o handler padrão (stderr) estará
        ativo. Chame configurar_logger() para adicionar novos handlers.

    Examples:
        >>> from nia_etl_utils import remover_handlers_existentes, configurar_logger
        >>>
        >>> # Remove handlers anteriores
        >>> remover_handlers_existentes()
        >>>
        >>> # Configura novo logger
        >>> configurar_logger("novo_pipeline", "2025_01_19")
    """
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
    )
    logger.debug("Handlers do logger foram resetados.")
