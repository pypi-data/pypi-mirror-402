"""Módulo utilitário para configuração de logging com Loguru."""
import sys
from pathlib import Path
from loguru import logger


def configurar_logger(
    prefixo: str,
    data_extracao: str,
    pasta_logs: str = "logs",
    rotation: str = "10 MB",
    retention: str = "7 days",
    level: str = "DEBUG"
) -> str:
    """Configura o logger da aplicação com Loguru.

    Cria um handler de arquivo para o logger com rotação automática e retenção
    configurável. O arquivo de log é criado em uma estrutura de diretórios
    organizada por prefixo.

    Args:
        prefixo: Nome do módulo/pipeline (ex: 'extract', 'transform', 'load').
        data_extracao: Data usada no nome do arquivo de log (ex: '2025_01_19').
        pasta_logs: Diretório raiz onde os logs serão armazenados. Defaults to "logs".
        rotation: Critério de rotação do arquivo (tamanho ou tempo). Defaults to "10 MB".
        retention: Tempo de retenção dos logs antigos. Defaults to "7 days".
        level: Nível mínimo de log a ser registrado. Defaults to "DEBUG".

    Returns:
        str: Caminho completo do arquivo de log criado.

    Raises:
        SystemExit: Se houver erro ao criar diretórios ou configurar o logger.

    Examples:
        >>> from nia_etl_utils.logger_config import configurar_logger
        >>> caminho_log = configurar_logger("extract", "2025_01_19")
        >>> logger.info("Pipeline iniciado")
        >>> # Log salvo em: logs/extract/extract_2025_01_19.log

        >>> # Com configurações customizadas
        >>> caminho_log = configurar_logger(
        ...     prefixo="etl_ouvidorias",
        ...     data_extracao="2025_01_19",
        ...     pasta_logs="/var/logs/nia",
        ...     rotation="50 MB",
        ...     retention="30 days",
        ...     level="INFO"
        ... )
    """
    try:
        # Valida inputs
        if not prefixo or not prefixo.strip():
            logger.error("Prefixo não pode ser vazio.")
            sys.exit(1)

        if not data_extracao or not data_extracao.strip():
            logger.error("Data de extração não pode ser vazia.")
            sys.exit(1)

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

    except PermissionError as error:
        logger.error(f"Sem permissão para criar diretório de logs '{pasta_logs}': {error}")
        sys.exit(1)
    except OSError as error:
        logger.error(f"Erro do sistema ao configurar logger em '{pasta_logs}': {error}")
        sys.exit(1)
    except Exception as error:
        logger.error(f"Erro inesperado ao configurar logger: {error}")
        sys.exit(1)


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
        str: Caminho completo do arquivo de log criado.

    Examples:
        >>> from nia_etl_utils.logger_config import configurar_logger_padrao_nia
        >>> from datetime import datetime
        >>>
        >>> caminho_log = configurar_logger_padrao_nia("ouvidorias_etl")
        >>> logger.info("Pipeline iniciado com configurações padrão NIA")
    """
    from datetime import datetime

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

    Examples:
        >>> from nia_etl_utils.logger_config import remover_handlers_existentes, configurar_logger
        >>>
        >>> # Remove handlers anteriores
        >>> remover_handlers_existentes()
        >>>
        >>> # Configura novo logger
        >>> configurar_logger("novo_pipeline", "2025_01_19")
    """
    logger.remove()
    logger.info("Todos os handlers do logger foram removidos.")
