"""Módulo utilitário para buscar variáveis de ambiente com suporte a valor padrão e log de erro."""
import os
import sys
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


def obter_variavel_env(nome_env: str, default=None):
    """Retorna o valor de uma variável de ambiente, com fallback opcional.

    Se a variável não existir e nenhum valor padrão for fornecido, o processo
    é encerrado com código de saída 1 (falha), garantindo que pipelines no
    Airflow detectem o erro corretamente.

    Args:
        nome_env: Nome da variável de ambiente a ser buscada.
        default: Valor a ser retornado caso a variável não esteja definida. Defaults to None.

    Returns:
        str: Valor da variável de ambiente ou valor padrão.

    Raises:
        SystemExit: Se a variável não for encontrada e nenhum valor padrão for fornecido.

    Examples:
        >>> # Variável obrigatória (falha se não existir)
        >>> db_host = obter_variavel_env('DB_HOST')

        >>> # Variável opcional com fallback
        >>> porta = obter_variavel_env('DB_PORT', default='5432')
    """
    value = os.getenv(nome_env, default)

    if value is None:
        logger.error(
            f"Variável de ambiente '{nome_env}' não encontrada e nenhum valor padrão foi fornecido. "
            f"Configure esta variável antes de executar o script."
        )
        sys.exit(1)

    return value
