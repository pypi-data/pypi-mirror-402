"""Módulo de conexão com bancos de dados PostgreSQL e Oracle.

Fornece funções para estabelecer conexões com bancos de dados usando
configurações explícitas ou variáveis de ambiente.

Examples:
    Conexão com configuração explícita:

    >>> from nia_etl_utils import conectar_postgresql, PostgresConfig
    >>> config = PostgresConfig(
    ...     host="localhost",
    ...     port="5432",
    ...     database="meu_banco",
    ...     user="usuario",
    ...     password="senha"
    ... )
    >>> with conectar_postgresql(config) as conn:
    ...     conn.cursor.execute("SELECT * FROM tabela")
    ...     dados = conn.cursor.fetchall()

    Conexão com variáveis de ambiente:

    >>> config = PostgresConfig.from_env("_OPENGEO")
    >>> with conectar_postgresql(config) as conn:
    ...     conn.cursor.execute("SELECT 1")

    Wrappers de conveniência:

    >>> with conectar_postgresql_nia() as conn:
    ...     conn.cursor.execute("SELECT * FROM ouvidorias")
"""

import cx_Oracle
import psycopg2
from loguru import logger
from psycopg2 import Error, OperationalError
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import OracleConfig, PostgresConfig
from .exceptions import ConexaoError
from .results import Conexao


def conectar_postgresql(config: PostgresConfig) -> Conexao:
    """Estabelece conexão com banco PostgreSQL.

    Cria uma conexão usando psycopg2 com os parâmetros fornecidos
    na configuração. A conexão retornada suporta context manager
    para fechamento automático.

    Args:
        config: Configuração de conexão PostgreSQL contendo host,
            port, database, user e password.

    Returns:
        Conexao com cursor e connection ativos, pronta para uso.

    Raises:
        ConexaoError: Se houver falha ao estabelecer a conexão,
            seja por credenciais inválidas, host inacessível ou
            outros problemas de conectividade.

    Examples:
        Com configuração explícita:

        >>> config = PostgresConfig(
        ...     host="localhost",
        ...     port="5432",
        ...     database="teste",
        ...     user="user",
        ...     password="pass"
        ... )
        >>> with conectar_postgresql(config) as conn:
        ...     conn.cursor.execute("SELECT 1")
        ...     resultado = conn.cursor.fetchone()
        ...     print(resultado)
        (1,)

        Com variáveis de ambiente:

        >>> config = PostgresConfig.from_env("_OPENGEO")
        >>> with conectar_postgresql(config) as conn:
        ...     conn.cursor.execute("SELECT COUNT(*) FROM tabela")

        Sem context manager (requer fechamento manual):

        >>> conn = conectar_postgresql(config)
        >>> try:
        ...     conn.cursor.execute("SELECT * FROM usuarios")
        ...     usuarios = conn.cursor.fetchall()
        ... finally:
        ...     conn.fechar()
    """
    logger.info(
        f"Conectando PostgreSQL em {config.host}:{config.port}, "
        f"database '{config.database}'..."
    )

    try:
        connection = psycopg2.connect(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.user,
            password=config.password
        )
        cursor = connection.cursor()

        logger.success(
            f"Conexão PostgreSQL estabelecida: '{config.database}' "
            f"em '{config.host}:{config.port}'"
        )

        return Conexao(cursor=cursor, connection=connection, database=config.database)

    except OperationalError as e:
        raise ConexaoError(
            f"Erro operacional PostgreSQL ({config.database})",
            details={"host": config.host, "port": config.port, "erro": str(e)}
        ) from e
    except Error as e:
        raise ConexaoError(
            f"Erro PostgreSQL ({config.database})",
            details={"host": config.host, "port": config.port, "erro": str(e)}
        ) from e


def conectar_oracle(config: OracleConfig) -> Conexao:
    """Estabelece conexão com banco Oracle.

    Cria uma conexão usando cx_Oracle com os parâmetros fornecidos
    na configuração. A conexão retornada suporta context manager
    para fechamento automático.

    Args:
        config: Configuração de conexão Oracle contendo host,
            port, service_name, user e password.

    Returns:
        Conexao com cursor e connection ativos, pronta para uso.

    Raises:
        ConexaoError: Se houver falha ao estabelecer a conexão.

    Examples:
        Com configuração explícita:

        >>> config = OracleConfig(
        ...     host="oracle.empresa.com",
        ...     port="1521",
        ...     service_name="PROD",
        ...     user="user",
        ...     password="pass"
        ... )
        >>> with conectar_oracle(config) as conn:
        ...     conn.cursor.execute("SELECT * FROM tabela WHERE ROWNUM <= 10")

        Com variáveis de ambiente:

        >>> config = OracleConfig.from_env()
        >>> with conectar_oracle(config) as conn:
        ...     conn.cursor.execute("SELECT SYSDATE FROM DUAL")
    """
    logger.info(
        f"Conectando Oracle em {config.host}:{config.port}, "
        f"service '{config.service_name}'..."
    )

    try:
        connection = cx_Oracle.connect(
            user=config.user,
            password=config.password,
            dsn=config.dsn
        )
        cursor = connection.cursor()

        logger.success(
            f"Conexão Oracle estabelecida: '{config.service_name}' "
            f"em '{config.host}:{config.port}'"
        )

        return Conexao(cursor=cursor, connection=connection, database=config.service_name)

    except cx_Oracle.DatabaseError as e:
        raise ConexaoError(
            f"Erro de banco Oracle ({config.service_name})",
            details={"host": config.host, "port": config.port, "erro": str(e)}
        ) from e
    except cx_Oracle.InterfaceError as e:
        raise ConexaoError(
            f"Erro de interface Oracle ({config.service_name})",
            details={"host": config.host, "port": config.port, "erro": str(e)}
        ) from e


def obter_engine_postgresql(config: PostgresConfig) -> Engine:
    """Cria engine SQLAlchemy para PostgreSQL.

    Cria e testa uma engine SQLAlchemy usando a configuração fornecida.
    A engine é útil para operações com pandas (read_sql, to_sql).

    Args:
        config: Configuração de conexão PostgreSQL.

    Returns:
        Engine SQLAlchemy configurada e testada.

    Raises:
        ConexaoError: Se houver falha ao criar ou testar a engine.

    Examples:
        Leitura com pandas:

        >>> import pandas as pd
        >>> config = PostgresConfig.from_env()
        >>> engine = obter_engine_postgresql(config)
        >>> df = pd.read_sql("SELECT * FROM tabela", engine)

        Escrita com pandas:

        >>> df.to_sql("nova_tabela", engine, if_exists="replace", index=False)
    """
    try:
        engine = create_engine(config.connection_string)

        # Testa a conexão
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        logger.success(
            f"Engine PostgreSQL criada: '{config.database}' "
            f"em '{config.host}:{config.port}'"
        )
        return engine

    except OperationalError as e:
        raise ConexaoError(
            f"Erro ao criar engine PostgreSQL ({config.database})",
            details={"host": config.host, "port": config.port, "erro": str(e)}
        ) from e


# =============================================================================
# WRAPPERS DE CONVENIÊNCIA
# =============================================================================


def conectar_postgresql_nia() -> Conexao:
    """Conecta no PostgreSQL do NIA usando variáveis de ambiente padrão.

    Usa as variáveis: DB_POSTGRESQL_HOST, DB_POSTGRESQL_PORT,
    DB_POSTGRESQL_DATABASE, DB_POSTGRESQL_USER, DB_POSTGRESQL_PASSWORD.

    Returns:
        Conexao configurada para o banco NIA.

    Raises:
        ConexaoError: Se houver falha ao conectar.
        ConfiguracaoError: Se variáveis de ambiente estiverem ausentes.

    Examples:
        >>> with conectar_postgresql_nia() as conn:
        ...     conn.cursor.execute("SELECT * FROM ouvidorias LIMIT 10")
        ...     dados = conn.cursor.fetchall()
    """
    return conectar_postgresql(PostgresConfig.from_env())


def conectar_postgresql_opengeo() -> Conexao:
    """Conecta no PostgreSQL OpenGeo usando variáveis de ambiente.

    Usa as variáveis com sufixo _OPENGEO: DB_POSTGRESQL_HOST_OPENGEO, etc.

    Returns:
        Conexao configurada para o banco OpenGeo.

    Raises:
        ConexaoError: Se houver falha ao conectar.
        ConfiguracaoError: Se variáveis de ambiente estiverem ausentes.

    Examples:
        >>> with conectar_postgresql_opengeo() as conn:
        ...     conn.cursor.execute("SELECT * FROM geo_data")
    """
    return conectar_postgresql(PostgresConfig.from_env("_OPENGEO"))


def conectar_oracle_ouvidorias() -> Conexao:
    """Conecta no Oracle de Ouvidorias usando variáveis de ambiente.

    Usa as variáveis: DB_ORACLE_HOST, DB_ORACLE_PORT,
    DB_ORACLE_SERVICE_NAME, DB_ORACLE_USER, DB_ORACLE_PASSWORD.

    Returns:
        Conexao configurada para o Oracle.

    Raises:
        ConexaoError: Se houver falha ao conectar.
        ConfiguracaoError: Se variáveis de ambiente estiverem ausentes.

    Examples:
        >>> with conectar_oracle_ouvidorias() as conn:
        ...     conn.cursor.execute("SELECT * FROM SGOV.OUVIDORIAS")
    """
    return conectar_oracle(OracleConfig.from_env())


def obter_engine_postgresql_nia() -> Engine:
    """Cria engine SQLAlchemy para PostgreSQL do NIA.

    Returns:
        Engine configurada para o banco NIA.

    Raises:
        ConexaoError: Se houver falha ao criar engine.
        ConfiguracaoError: Se variáveis de ambiente estiverem ausentes.

    Examples:
        >>> import pandas as pd
        >>> engine = obter_engine_postgresql_nia()
        >>> df = pd.read_sql("SELECT * FROM tabela", engine)
    """
    return obter_engine_postgresql(PostgresConfig.from_env())


def obter_engine_postgresql_opengeo() -> Engine:
    """Cria engine SQLAlchemy para PostgreSQL OpenGeo.

    Returns:
        Engine configurada para o banco OpenGeo.

    Raises:
        ConexaoError: Se houver falha ao criar engine.
        ConfiguracaoError: Se variáveis de ambiente estiverem ausentes.

    Examples:
        >>> import pandas as pd
        >>> engine = obter_engine_postgresql_opengeo()
        >>> df = pd.read_sql("SELECT * FROM geo_tabela", engine)
    """
    return obter_engine_postgresql(PostgresConfig.from_env("_OPENGEO"))
