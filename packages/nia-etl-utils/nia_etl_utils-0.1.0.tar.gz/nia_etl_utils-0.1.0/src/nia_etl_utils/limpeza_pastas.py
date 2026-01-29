"""Funções utilitárias para manipulação de arquivos e diretórios."""
import sys
import shutil
from pathlib import Path
from loguru import logger


def limpar_pasta(pasta: str, log: bool = True) -> None:
    """Remove todos os arquivos de uma pasta, recriando-a se necessário.

    Se a pasta não existir, ela será criada. Se existir, todos os arquivos
    dentro dela serão removidos (subdiretórios são preservados).

    Args:
        pasta: Caminho da pasta que será limpa.
        log: Se True, emite logs com Loguru. Defaults to True.

    Raises:
        SystemExit: Se houver erro ao criar ou limpar a pasta.

    Examples:
        >>> from nia_etl_utils.limpeza_pastas import limpar_pasta
        >>> limpar_pasta("/tmp/meu_pipeline")
        >>> # Pasta criada ou limpa com sucesso
    """
    try:
        pasta_path = Path(pasta)

        if not pasta_path.exists():
            pasta_path.mkdir(parents=True, exist_ok=True)
            if log:
                logger.info(f"Pasta criada: {pasta}")
        else:
            arquivos_removidos = 0

            for item in pasta_path.iterdir():
                if item.is_file():
                    item.unlink()
                    arquivos_removidos += 1
                    if log:
                        logger.debug(f"Arquivo removido: {item}")

            if log:
                logger.info(f"Pasta '{pasta}' limpa com sucesso. {arquivos_removidos} arquivo(s) removido(s).")

    except PermissionError as error:
        logger.error(f"Sem permissão para acessar/modificar a pasta '{pasta}': {error}")
        sys.exit(1)
    except OSError as error:
        logger.error(f"Erro do sistema ao manipular a pasta '{pasta}': {error}")
        sys.exit(1)
    except Exception as error:
        logger.error(f"Erro inesperado ao limpar a pasta '{pasta}': {error}")
        sys.exit(1)


def remover_pasta_recursivamente(pasta: str, log: bool = True) -> None:
    """Remove uma pasta e todo seu conteúdo (arquivos e subpastas).

    ATENÇÃO: Esta função remove TUDO dentro da pasta, incluindo subdiretórios.
    Use com cautela.

    Args:
        pasta: Caminho da pasta que será removida completamente.
        log: Se True, emite logs com Loguru. Defaults to True.

    Raises:
        SystemExit: Se houver erro ao remover a pasta.

    Examples:
        >>> from nia_etl_utils.limpeza_pastas import remover_pasta_recursivamente
        >>> remover_pasta_recursivamente("/tmp/pasta_temporaria")
    """
    try:
        pasta_path = Path(pasta)

        if not pasta_path.exists():
            if log:
                logger.warning(f"Pasta '{pasta}' não existe. Nada a remover.")
            return

        if not pasta_path.is_dir():
            logger.error(f"'{pasta}' não é um diretório.")
            sys.exit(1)

        shutil.rmtree(pasta_path)

        if log:
            logger.info(f"Pasta '{pasta}' removida completamente (incluindo subpastas).")

    except PermissionError as error:
        logger.error(f"Sem permissão para remover a pasta '{pasta}': {error}")
        sys.exit(1)
    except OSError as error:
        logger.error(f"Erro do sistema ao remover a pasta '{pasta}': {error}")
        sys.exit(1)
    except Exception as error:
        logger.error(f"Erro inesperado ao remover a pasta '{pasta}': {error}")
        sys.exit(1)


def criar_pasta_se_nao_existir(pasta: str, log: bool = True) -> None:
    """Cria uma pasta se ela não existir (incluindo pastas pai).

    Args:
        pasta: Caminho da pasta que será criada.
        log: Se True, emite logs com Loguru. Defaults to True.

    Raises:
        SystemExit: Se houver erro ao criar a pasta.

    Examples:
        >>> from nia_etl_utils.limpeza_pastas import criar_pasta_se_nao_existir
        >>> criar_pasta_se_nao_existir("/tmp/dados/processados/2025")
    """
    try:
        pasta_path = Path(pasta)

        if pasta_path.exists():
            if log:
                logger.debug(f"Pasta '{pasta}' já existe.")
            return

        pasta_path.mkdir(parents=True, exist_ok=True)

        if log:
            logger.info(f"Pasta criada: {pasta}")

    except PermissionError as error:
        logger.error(f"Sem permissão para criar a pasta '{pasta}': {error}")
        sys.exit(1)
    except OSError as error:
        logger.error(f"Erro do sistema ao criar a pasta '{pasta}': {error}")
        sys.exit(1)
    except Exception as error:
        logger.error(f"Erro inesperado ao criar a pasta '{pasta}': {error}")
        sys.exit(1)
