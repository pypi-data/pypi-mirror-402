"""Módulo de conexão com bancos de dados PostgreSQL e Oracle.

Fornece funções genéricas e wrappers de conveniência para estabelecer conexões
com diferentes bancos de dados usando credenciais de variáveis de ambiente.
"""
import sys
import cx_Oracle
import psycopg2
from loguru import logger
from psycopg2 import Error, OperationalError
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from .env_config import obter_variavel_env


def conectar_postgresql(sufixo_env: str = "") -> tuple:
    """Estabelece conexão genérica com banco de dados PostgreSQL usando psycopg2.

    Args:
        sufixo_env: Sufixo das variáveis de ambiente para conexão.
                   Vazio ("") para banco padrão (DB_POSTGRESQL_*).
                   "_OPENGEO" para OpenGeo (DB_POSTGRESQL_HOST_OPENGEO, etc).

    Returns:
        tuple: (cursor, connection) — cursor e objeto de conexão ativa.

    Raises:
        SystemExit: Se houver erro ao estabelecer a conexão.

    Examples:
        >>> # Conecta usando variáveis DB_POSTGRESQL_HOST, DB_POSTGRESQL_PORT, etc
        >>> cur, conn = conectar_postgresql()
        >>> cur.execute("SELECT * FROM tabela")
        >>> resultados = cur.fetchall()
        >>> cur.close()
        >>> conn.close()

        >>> # Conecta em OpenGeo usando DB_POSTGRESQL_HOST_OPENGEO, etc
        >>> cur, conn = conectar_postgresql("_OPENGEO")
    """
    try:
        host = obter_variavel_env(f"DB_POSTGRESQL_HOST{sufixo_env}")
        port = obter_variavel_env(f"DB_POSTGRESQL_PORT{sufixo_env}")
        database = obter_variavel_env(f"DB_POSTGRESQL_DATABASE{sufixo_env}")
        user = obter_variavel_env(f"DB_POSTGRESQL_USER{sufixo_env}")
        password = obter_variavel_env(f"DB_POSTGRESQL_PASSWORD{sufixo_env}")

        logger.info(f"Iniciando conexão PostgreSQL em {host}:{port}, database '{database}'...")

        connection = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        cursor = connection.cursor()

        logger.success(f"Conexão PostgreSQL estabelecida: '{database}' em '{host}:{port}'")
        return cursor, connection

    except OperationalError as error:
        logger.error(f"Erro operacional PostgreSQL (sufixo: '{sufixo_env}'): {error}")
        sys.exit(1)
    except Error as error:
        logger.error(f"Erro PostgreSQL (sufixo: '{sufixo_env}'): {error}")
        sys.exit(1)
    except Exception as error:
        logger.error(f"Erro inesperado PostgreSQL (sufixo: '{sufixo_env}'): {error}")
        sys.exit(1)


def obter_engine_postgresql(sufixo_env: str = "") -> Engine:
    """Cria uma engine SQLAlchemy genérica para PostgreSQL.

    Args:
        sufixo_env: Sufixo das variáveis de ambiente para conexão.
                   Vazio ("") para banco padrão, "_OPENGEO" para OpenGeo.

    Returns:
        Engine configurada para PostgreSQL.

    Raises:
        SystemExit: Se houver erro na criação da conexão.

    Examples:
        >>> import pandas as pd
        >>> engine = obter_engine_postgresql()
        >>> df = pd.read_sql("SELECT * FROM tabela", engine)

        >>> # Engine para OpenGeo
        >>> engine = obter_engine_postgresql("_OPENGEO")
    """
    try:
        host = obter_variavel_env(f"DB_POSTGRESQL_HOST{sufixo_env}")
        port = obter_variavel_env(f"DB_POSTGRESQL_PORT{sufixo_env}")
        database = obter_variavel_env(f"DB_POSTGRESQL_DATABASE{sufixo_env}")
        user = obter_variavel_env(f"DB_POSTGRESQL_USER{sufixo_env}")
        password = obter_variavel_env(f"DB_POSTGRESQL_PASSWORD{sufixo_env}")

        connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
        engine = create_engine(connection_string)

        # Testa a conexão
        with engine.connect() as conn:
            conn.execute("SELECT 1") # type: ignore

        logger.success(f"Engine PostgreSQL criada: '{database}' em '{host}:{port}'")
        return engine

    except OperationalError as error:
        logger.error(f"Erro operacional ao criar engine PostgreSQL (sufixo: '{sufixo_env}'): {error}")
        sys.exit(1)
    except Exception as error:
        logger.error(f"Erro inesperado ao criar engine PostgreSQL (sufixo: '{sufixo_env}'): {error}")
        sys.exit(1)


def conectar_oracle() -> tuple:
    """Estabelece conexão com banco de dados Oracle.

    Usa variáveis de ambiente: DB_ORACLE_HOST, DB_ORACLE_PORT, DB_ORACLE_SERVICE_NAME,
    DB_ORACLE_USER, DB_ORACLE_PASSWORD.

    Returns:
        tuple: (cursor, connection) — cursor e objeto de conexão ativa.

    Raises:
        SystemExit: Se houver erro ao estabelecer a conexão.

    Examples:
        >>> cur, conn = conectar_oracle()
        >>> cur.execute("SELECT * FROM tabela WHERE ROWNUM <= 10")
        >>> resultados = cur.fetchall()
        >>> fechar_conexao(cur, conn)
    """
    try:
        host = obter_variavel_env("DB_ORACLE_HOST")
        port = obter_variavel_env("DB_ORACLE_PORT")
        service_name = obter_variavel_env("DB_ORACLE_SERVICE_NAME")
        user = obter_variavel_env("DB_ORACLE_USER")
        password = obter_variavel_env("DB_ORACLE_PASSWORD")

        logger.info(f"Iniciando conexão Oracle em {host}:{port}, service '{service_name}'...")

        dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
        connection = cx_Oracle.connect(user=user, password=password, dsn=dsn)
        cursor = connection.cursor()

        logger.success(f"Conexão Oracle estabelecida: '{service_name}' em '{host}:{port}'")
        return cursor, connection

    except cx_Oracle.DatabaseError as error:
        logger.error(f"Erro de banco Oracle: {error}")
        sys.exit(1)
    except cx_Oracle.InterfaceError as error:
        logger.error(f"Erro de interface Oracle: {error}")
        sys.exit(1)
    except Exception as error:
        logger.error(f"Erro inesperado Oracle: {error}")
        sys.exit(1)


def fechar_conexao(cursor, connection) -> None:
    """Encerra cursor e conexão de banco de dados de forma segura.

    Funciona para conexões PostgreSQL (psycopg2) e Oracle (cx_Oracle).

    Args:
        cursor: Cursor ativo que será fechado.
        connection: Conexão ativa que será encerrada.

    Examples:
        >>> cur, conn = conectar_postgresql()
        >>> # ... usar cursor ...
        >>> fechar_conexao(cur, conn)
    """
    try:
        if cursor:
            cursor.close()
            logger.debug("Cursor fechado com sucesso.")

        if connection:
            connection.close()
            logger.debug("Conexão encerrada com sucesso.")

    except Exception as error:
        logger.warning(f"Erro ao fechar conexão: {error}")
        # Não usa sys.exit(1) porque fechar conexão é cleanup


# =============================================================================
# WRAPPERS DE CONVENIÊNCIA - APIs específicas para bancos conhecidos
# =============================================================================

def conectar_postgresql_nia() -> tuple:
    """Conecta no PostgreSQL do NIA.

    Usa variáveis de ambiente: DB_POSTGRESQL_HOST, DB_POSTGRESQL_PORT, etc.

    Returns:
        tuple: (cursor, connection)
    """
    return conectar_postgresql("")


def obter_engine_postgresql_nia() -> Engine:
    """Cria engine SQLAlchemy para PostgreSQL do NIA.

    Returns:
        Engine configurada para o banco NIA.
    """
    return obter_engine_postgresql("")


def conectar_postgresql_opengeo() -> tuple:
    """Conecta no PostgreSQL OpenGeo.

    Usa variáveis de ambiente: DB_POSTGRESQL_HOST_OPENGEO, DB_POSTGRESQL_PORT_OPENGEO, etc.

    Returns:
        tuple: (cursor, connection)
    """
    return conectar_postgresql("_OPENGEO")


def obter_engine_postgresql_opengeo() -> Engine:
    """Cria engine SQLAlchemy para PostgreSQL OpenGeo.

    Returns:
        Engine configurada para o banco OpenGeo.
    """
    return obter_engine_postgresql("_OPENGEO")


def conectar_oracle_ouvidorias() -> tuple:
    """Conecta no Oracle de Ouvidorias.

    Alias para conectar_oracle() — mantido para compatibilidade semântica.
    Usa variáveis de ambiente: DB_ORACLE_HOST, DB_ORACLE_PORT, etc.

    Returns:
        tuple: (cursor, connection)
    """
    return conectar_oracle()
