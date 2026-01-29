"""Módulo utilitário para gerenciamento de variáveis de ambiente.

Fornece funções para buscar variáveis de ambiente com suporte a
valores padrão, validação e logging apropriado.

Examples:
    Variável obrigatória:

    >>> from nia_etl_utils import obter_variavel_env
    >>> db_host = obter_variavel_env('DB_HOST')  # levanta exceção se não existir

    Variável opcional com fallback:

    >>> porta = obter_variavel_env('DB_PORT', default='5432')

    Tratamento de erro:

    >>> from nia_etl_utils.exceptions import VariavelAmbienteError
    >>> try:
    ...     valor = obter_variavel_env('VARIAVEL_INEXISTENTE')
    ... except VariavelAmbienteError as e:
    ...     print(f"Variável não encontrada: {e.nome_variavel}")
"""

import os

from dotenv import load_dotenv
from loguru import logger

from .exceptions import VariavelAmbienteError

# Carrega variáveis do arquivo .env se existir
load_dotenv()


def obter_variavel_env(nome_env: str, default: str | None = None) -> str:
    """Retorna o valor de uma variável de ambiente.

    Busca uma variável de ambiente pelo nome. Se a variável não existir
    e nenhum valor padrão for fornecido, levanta VariavelAmbienteError.

    Args:
        nome_env: Nome da variável de ambiente a ser buscada.
        default: Valor a ser retornado caso a variável não esteja definida.
            Se None (padrão), a variável é considerada obrigatória.

    Returns:
        Valor da variável de ambiente ou valor padrão.

    Raises:
        VariavelAmbienteError: Se a variável não for encontrada e
            nenhum valor padrão for fornecido.

    Examples:
        Variável obrigatória (falha se não existir):

        >>> db_host = obter_variavel_env('DB_POSTGRESQL_HOST')
        >>> print(f"Conectando em {db_host}")

        Variável opcional com fallback:

        >>> porta = obter_variavel_env('DB_PORT', default='5432')
        >>> timeout = obter_variavel_env('DB_TIMEOUT', default='30')

        Tratando ausência de variável:

        >>> from nia_etl_utils.exceptions import VariavelAmbienteError
        >>> try:
        ...     api_key = obter_variavel_env('API_KEY_SECRETA')
        ... except VariavelAmbienteError as e:
        ...     logger.error(f"Configure a variável: {e.nome_variavel}")
        ...     raise
    """
    value = os.getenv(nome_env, default)

    if value is None:
        logger.error(
            f"Variável de ambiente '{nome_env}' não encontrada "
            f"e nenhum valor padrão foi fornecido. "
            f"Configure esta variável antes de executar o script."
        )
        raise VariavelAmbienteError(nome_env)

    return value


def obter_variavel_env_int(nome_env: str, default: int | None = None) -> int:
    """Retorna o valor de uma variável de ambiente como inteiro.

    Conveniência para variáveis numéricas como portas e timeouts.

    Args:
        nome_env: Nome da variável de ambiente.
        default: Valor inteiro padrão se variável não existir.

    Returns:
        Valor da variável convertido para inteiro.

    Raises:
        VariavelAmbienteError: Se a variável não existir e não houver default.
        ValueError: Se o valor não puder ser convertido para inteiro.

    Examples:
        >>> porta = obter_variavel_env_int('DB_PORT', default=5432)
        >>> timeout = obter_variavel_env_int('TIMEOUT_SEGUNDOS', default=30)
    """
    default_str = str(default) if default is not None else None
    valor = obter_variavel_env(nome_env, default=default_str)
    return int(valor)


def obter_variavel_env_bool(nome_env: str, default: bool = False) -> bool:
    """Retorna o valor de uma variável de ambiente como booleano.

    Valores considerados True: 'true', '1', 'yes', 'on' (case insensitive).
    Qualquer outro valor é considerado False.

    Args:
        nome_env: Nome da variável de ambiente.
        default: Valor booleano padrão se variável não existir.

    Returns:
        Valor da variável interpretado como booleano.

    Examples:
        >>> debug = obter_variavel_env_bool('DEBUG_MODE', default=False)
        >>> verbose = obter_variavel_env_bool('VERBOSE_LOGGING')
    """
    default_str = str(default).lower()
    valor = obter_variavel_env(nome_env, default=default_str)
    return valor.lower() in ('true', '1', 'yes', 'on')


def obter_variavel_env_lista(
    nome_env: str,
    separador: str = ',',
    default: list[str] | None = None
) -> list[str]:
    """Retorna o valor de uma variável de ambiente como lista.

    Útil para variáveis que contêm múltiplos valores separados
    por um delimitador.

    Args:
        nome_env: Nome da variável de ambiente.
        separador: Caractere separador dos valores. Padrão: vírgula.
        default: Lista padrão se variável não existir.

    Returns:
        Lista de strings extraída da variável.

    Raises:
        VariavelAmbienteError: Se a variável não existir e não houver default.

    Examples:
        >>> # EMAIL_DESTINATARIOS="admin@x.com,dev@x.com"
        >>> emails = obter_variavel_env_lista('EMAIL_DESTINATARIOS')
        >>> # ['admin@x.com', 'dev@x.com']

        >>> # HOSTS="host1;host2;host3"
        >>> hosts = obter_variavel_env_lista('HOSTS', separador=';')
    """
    default_str = separador.join(default) if default is not None else None
    valor = obter_variavel_env(nome_env, default=default_str)
    return [item.strip() for item in valor.split(separador) if item.strip()]
