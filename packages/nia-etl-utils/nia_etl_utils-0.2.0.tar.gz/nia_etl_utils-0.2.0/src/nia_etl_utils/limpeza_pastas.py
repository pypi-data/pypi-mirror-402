"""Funções utilitárias para manipulação de arquivos e diretórios.

Fornece operações comuns de sistema de arquivos com logging
apropriado e tratamento de erros consistente.

Examples:
    Limpar pasta antes de processamento:

    >>> from nia_etl_utils import limpar_pasta
    >>> limpar_pasta("/tmp/meu_pipeline")

    Criar estrutura de diretórios:

    >>> from nia_etl_utils import criar_pasta_se_nao_existir
    >>> criar_pasta_se_nao_existir("/dados/processados/2025/01")

    Remover pasta temporária:

    >>> from nia_etl_utils import remover_pasta_recursivamente
    >>> remover_pasta_recursivamente("/tmp/pasta_temporaria")
"""

import shutil
from pathlib import Path

from loguru import logger

from .exceptions import DiretorioError


def limpar_pasta(pasta: str, log: bool = True) -> int:
    """Remove todos os arquivos de uma pasta, preservando subdiretórios.

    Se a pasta não existir, ela será criada. Se existir, todos os arquivos
    dentro dela serão removidos (subdiretórios são preservados).

    Args:
        pasta: Caminho da pasta que será limpa.
        log: Se True, emite logs com Loguru. Defaults to True.

    Returns:
        Número de arquivos removidos.

    Raises:
        DiretorioError: Se houver erro ao criar ou limpar a pasta.

    Examples:
        Limpar pasta de saída antes de processamento:

        >>> from nia_etl_utils import limpar_pasta
        >>> removidos = limpar_pasta("/tmp/meu_pipeline")
        >>> print(f"{removidos} arquivo(s) removido(s)")

        Limpar sem logging:

        >>> limpar_pasta("/tmp/dados", log=False)
    """
    try:
        pasta_path = Path(pasta)

        if not pasta_path.exists():
            pasta_path.mkdir(parents=True, exist_ok=True)
            if log:
                logger.info(f"Pasta criada: {pasta}")
            return 0

        arquivos_removidos = 0

        for item in pasta_path.iterdir():
            if item.is_file():
                item.unlink()
                arquivos_removidos += 1
                if log:
                    logger.debug(f"Arquivo removido: {item}")

        if log:
            logger.info(
                f"Pasta '{pasta}' limpa com sucesso. "
                f"{arquivos_removidos} arquivo(s) removido(s)."
            )

        return arquivos_removidos

    except PermissionError as e:
        raise DiretorioError(
            f"Sem permissão para acessar/modificar a pasta '{pasta}'",
            details={"pasta": pasta, "erro": str(e)}
        ) from e
    except OSError as e:
        raise DiretorioError(
            f"Erro do sistema ao manipular a pasta '{pasta}'",
            details={"pasta": pasta, "erro": str(e)}
        ) from e


def remover_pasta_recursivamente(pasta: str, log: bool = True) -> bool:
    """Remove uma pasta e todo seu conteúdo (arquivos e subpastas).

    ATENÇÃO: Esta função remove TUDO dentro da pasta, incluindo
    subdiretórios. Use com cautela.

    Args:
        pasta: Caminho da pasta que será removida completamente.
        log: Se True, emite logs com Loguru. Defaults to True.

    Returns:
        True se a pasta foi removida, False se não existia.

    Raises:
        DiretorioError: Se o caminho não for um diretório ou
            houver erro ao remover.

    Examples:
        Remover pasta temporária:

        >>> from nia_etl_utils import remover_pasta_recursivamente
        >>> if remover_pasta_recursivamente("/tmp/pasta_temporaria"):
        ...     print("Pasta removida")
        ... else:
        ...     print("Pasta não existia")

        Remover sem logging:

        >>> remover_pasta_recursivamente("/tmp/dados", log=False)
    """
    try:
        pasta_path = Path(pasta)

        if not pasta_path.exists():
            if log:
                logger.warning(f"Pasta '{pasta}' não existe. Nada a remover.")
            return False

        if not pasta_path.is_dir():
            raise DiretorioError(
                f"'{pasta}' não é um diretório",
                details={"pasta": pasta, "tipo": "arquivo"}
            )

        shutil.rmtree(pasta_path)

        if log:
            logger.info(f"Pasta '{pasta}' removida completamente (incluindo subpastas).")

        return True

    except PermissionError as e:
        raise DiretorioError(
            f"Sem permissão para remover a pasta '{pasta}'",
            details={"pasta": pasta, "erro": str(e)}
        ) from e
    except OSError as e:
        raise DiretorioError(
            f"Erro do sistema ao remover a pasta '{pasta}'",
            details={"pasta": pasta, "erro": str(e)}
        ) from e


def criar_pasta_se_nao_existir(pasta: str, log: bool = True) -> bool:
    """Cria uma pasta se ela não existir (incluindo pastas pai).

    Args:
        pasta: Caminho da pasta que será criada.
        log: Se True, emite logs com Loguru. Defaults to True.

    Returns:
        True se a pasta foi criada, False se já existia.

    Raises:
        DiretorioError: Se houver erro ao criar a pasta.

    Examples:
        Criar estrutura de diretórios:

        >>> from nia_etl_utils import criar_pasta_se_nao_existir
        >>> if criar_pasta_se_nao_existir("/tmp/dados/processados/2025"):
        ...     print("Estrutura criada")
        ... else:
        ...     print("Já existia")

        Criar sem logging:

        >>> criar_pasta_se_nao_existir("/tmp/dados", log=False)
    """
    try:
        pasta_path = Path(pasta)

        if pasta_path.exists():
            if log:
                logger.debug(f"Pasta '{pasta}' já existe.")
            return False

        pasta_path.mkdir(parents=True, exist_ok=True)

        if log:
            logger.info(f"Pasta criada: {pasta}")

        return True

    except PermissionError as e:
        raise DiretorioError(
            f"Sem permissão para criar a pasta '{pasta}'",
            details={"pasta": pasta, "erro": str(e)}
        ) from e
    except OSError as e:
        raise DiretorioError(
            f"Erro do sistema ao criar a pasta '{pasta}'",
            details={"pasta": pasta, "erro": str(e)}
        ) from e


def listar_arquivos(
    pasta: str,
    extensao: str | None = None,
    recursivo: bool = False
) -> list[Path]:
    """Lista arquivos em uma pasta.

    Args:
        pasta: Caminho da pasta a ser listada.
        extensao: Filtrar por extensão (ex: ".csv", ".json").
            Se None, lista todos os arquivos.
        recursivo: Se True, inclui arquivos em subpastas.

    Returns:
        Lista de objetos Path para cada arquivo encontrado.

    Raises:
        DiretorioError: Se a pasta não existir ou não for acessível.

    Examples:
        Listar todos os CSVs:

        >>> arquivos = listar_arquivos("/tmp/dados", extensao=".csv")
        >>> for arq in arquivos:
        ...     print(arq.name)

        Listar recursivamente:

        >>> arquivos = listar_arquivos("/tmp/dados", recursivo=True)
    """
    try:
        pasta_path = Path(pasta)

        if not pasta_path.exists():
            raise DiretorioError(
                f"Pasta '{pasta}' não existe",
                details={"pasta": pasta}
            )

        if not pasta_path.is_dir():
            raise DiretorioError(
                f"'{pasta}' não é um diretório",
                details={"pasta": pasta}
            )

        if recursivo:
            pattern = "**/*" if extensao is None else f"**/*{extensao}"
            arquivos = [p for p in pasta_path.glob(pattern) if p.is_file()]
        else:
            pattern = "*" if extensao is None else f"*{extensao}"
            arquivos = [p for p in pasta_path.glob(pattern) if p.is_file()]

        return sorted(arquivos)

    except PermissionError as e:
        raise DiretorioError(
            f"Sem permissão para acessar a pasta '{pasta}'",
            details={"pasta": pasta, "erro": str(e)}
        ) from e
