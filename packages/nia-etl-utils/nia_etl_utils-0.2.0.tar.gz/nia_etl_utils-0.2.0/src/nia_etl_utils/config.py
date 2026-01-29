"""Dataclasses de configuração para o pacote nia_etl_utils.

Este módulo define estruturas de dados imutáveis para configuração
de conexões, email e outras operações do pacote.

As configurações podem ser criadas de três formas:
1. Instanciação direta com valores explícitos
2. Factory method `from_env()` para carregar de variáveis de ambiente
3. Wrappers de conveniência para casos comuns

Examples:
    Configuração explícita (recomendado para testes):

    >>> config = PostgresConfig(
    ...     host="localhost",
    ...     port="5432",
    ...     database="teste",
    ...     user="user",
    ...     password="pass"
    ... )

    Configuração via ambiente (recomendado para produção):

    >>> config = PostgresConfig.from_env()  # usa variáveis padrão
    >>> config = PostgresConfig.from_env("_OPENGEO")  # usa sufixo

    Uso com funções de conexão:

    >>> from nia_etl_utils import conectar_postgresql
    >>> with conectar_postgresql(config) as conn:
    ...     conn.cursor.execute("SELECT 1")
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

import cx_Oracle

from .exceptions import ConfiguracaoError

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class PostgresConfig:
    """Configuração de conexão PostgreSQL.

    Dataclass imutável contendo todos os parâmetros necessários
    para estabelecer conexão com um banco PostgreSQL.

    Attributes:
        host: Endereço do servidor PostgreSQL.
        port: Porta de conexão (geralmente 5432).
        database: Nome do banco de dados.
        user: Usuário de autenticação.
        password: Senha de autenticação.

    Examples:
        Criação direta:

        >>> config = PostgresConfig(
        ...     host="localhost",
        ...     port="5432",
        ...     database="meu_banco",
        ...     user="usuario",
        ...     password="senha"
        ... )

        A partir de variáveis de ambiente:

        >>> config = PostgresConfig.from_env()
        >>> config = PostgresConfig.from_env("_OPENGEO")

        Acessando connection string:

        >>> config.connection_string
        'postgresql+psycopg2://usuario:senha@localhost:5432/meu_banco'
    """

    host: str
    port: str
    database: str
    user: str
    password: str

    @classmethod
    def from_env(cls, sufixo: str = "") -> "PostgresConfig":
        """Cria configuração a partir de variáveis de ambiente.

        Busca as seguintes variáveis (com sufixo opcional):
        - DB_POSTGRESQL_HOST{sufixo}
        - DB_POSTGRESQL_PORT{sufixo}
        - DB_POSTGRESQL_DATABASE{sufixo}
        - DB_POSTGRESQL_USER{sufixo}
        - DB_POSTGRESQL_PASSWORD{sufixo}

        Args:
            sufixo: Sufixo das variáveis de ambiente. Use "" para
                variáveis padrão ou "_OPENGEO", "_PROD", etc para
                ambientes específicos.

        Returns:
            PostgresConfig com valores das variáveis de ambiente.

        Raises:
            ConfiguracaoError: Se alguma variável obrigatória não existir.

        Examples:
            >>> config = PostgresConfig.from_env()
            >>> config = PostgresConfig.from_env("_OPENGEO")
        """
        from .env_config import obter_variavel_env

        try:
            return cls(
                host=obter_variavel_env(f"DB_POSTGRESQL_HOST{sufixo}"),
                port=obter_variavel_env(f"DB_POSTGRESQL_PORT{sufixo}"),
                database=obter_variavel_env(f"DB_POSTGRESQL_DATABASE{sufixo}"),
                user=obter_variavel_env(f"DB_POSTGRESQL_USER{sufixo}"),
                password=obter_variavel_env(f"DB_POSTGRESQL_PASSWORD{sufixo}"),
            )
        except Exception as e:
            raise ConfiguracaoError(
                f"Variáveis de ambiente PostgreSQL incompletas (sufixo='{sufixo}')",
                details={"sufixo": sufixo, "erro_original": str(e)}
            ) from e

    @property
    def connection_string(self) -> str:
        """String de conexão SQLAlchemy.

        Returns:
            String formatada para uso com SQLAlchemy create_engine().

        Examples:
            >>> config = PostgresConfig(
            ...     host="localhost",
            ...     port="5432",
            ...     database="teste",
            ...     user="user",
            ...     password="pass"
            ... )
            >>> config.connection_string
            'postgresql+psycopg2://user:pass@localhost:5432/teste'
        """
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    def __repr__(self) -> str:
        """Representação segura (sem expor senha)."""
        return (
            f"PostgresConfig(host='{self.host}', port='{self.port}', "
            f"database='{self.database}', user='{self.user}', password='***')"
        )


@dataclass(frozen=True)
class OracleConfig:
    """Configuração de conexão Oracle.

    Dataclass imutável contendo todos os parâmetros necessários
    para estabelecer conexão com um banco Oracle.

    Attributes:
        host: Endereço do servidor Oracle.
        port: Porta de conexão (geralmente 1521).
        service_name: Nome do serviço Oracle.
        user: Usuário de autenticação.
        password: Senha de autenticação.

    Examples:
        Criação direta:

        >>> config = OracleConfig(
        ...     host="oracle.empresa.com",
        ...     port="1521",
        ...     service_name="PROD",
        ...     user="usuario",
        ...     password="senha"
        ... )

        A partir de variáveis de ambiente:

        >>> config = OracleConfig.from_env()
    """

    host: str
    port: str
    service_name: str
    user: str
    password: str

    @classmethod
    def from_env(cls, sufixo: str = "") -> "OracleConfig":
        """Cria configuração a partir de variáveis de ambiente.

        Busca as seguintes variáveis (com sufixo opcional):
        - DB_ORACLE_HOST{sufixo}
        - DB_ORACLE_PORT{sufixo}
        - DB_ORACLE_SERVICE_NAME{sufixo}
        - DB_ORACLE_USER{sufixo}
        - DB_ORACLE_PASSWORD{sufixo}

        Args:
            sufixo: Sufixo das variáveis de ambiente.

        Returns:
            OracleConfig com valores das variáveis de ambiente.

        Raises:
            ConfiguracaoError: Se alguma variável obrigatória não existir.

        Examples:
            >>> config = OracleConfig.from_env()
            >>> config = OracleConfig.from_env("_PROD")
        """
        from .env_config import obter_variavel_env

        try:
            return cls(
                host=obter_variavel_env(f"DB_ORACLE_HOST{sufixo}"),
                port=obter_variavel_env(f"DB_ORACLE_PORT{sufixo}"),
                service_name=obter_variavel_env(f"DB_ORACLE_SERVICE_NAME{sufixo}"),
                user=obter_variavel_env(f"DB_ORACLE_USER{sufixo}"),
                password=obter_variavel_env(f"DB_ORACLE_PASSWORD{sufixo}"),
            )
        except Exception as e:
            raise ConfiguracaoError(
                f"Variáveis de ambiente Oracle incompletas (sufixo='{sufixo}')",
                details={"sufixo": sufixo, "erro_original": str(e)}
            ) from e

    @property
    def dsn(self) -> str:
        """DSN para conexão cx_Oracle.

        Returns:
            DSN formatado para uso com cx_Oracle.connect().

        Examples:
            >>> config = OracleConfig(
            ...     host="oracle.empresa.com",
            ...     port="1521",
            ...     service_name="PROD",
            ...     user="user",
            ...     password="pass"
            ... )
            >>> # dsn é gerado internamente por cx_Oracle.makedsn()
        """
        return cx_Oracle.makedsn(self.host, self.port, service_name=self.service_name)

    def __repr__(self) -> str:
        """Representação segura (sem expor senha)."""
        return (
            f"OracleConfig(host='{self.host}', port='{self.port}', "
            f"service_name='{self.service_name}', user='{self.user}', password='***')"
        )


@dataclass(frozen=True)
class SmtpConfig:
    """Configuração de servidor SMTP para envio de emails.

    Attributes:
        servidor: Endereço do servidor SMTP.
        porta: Porta de conexão (geralmente 25, 465 ou 587).
        remetente: Endereço de email do remetente.
        destinatarios_padrao: Lista de destinatários padrão.
        cc: Endereço para cópia (opcional).

    Examples:
        Criação direta:

        >>> config = SmtpConfig(
        ...     servidor="smtp.empresa.com",
        ...     porta=587,
        ...     remetente="sistema@empresa.com",
        ...     destinatarios_padrao=["admin@empresa.com"]
        ... )

        A partir de variáveis de ambiente:

        >>> config = SmtpConfig.from_env()
    """

    servidor: str
    porta: int
    remetente: str
    destinatarios_padrao: list[str]
    cc: str | None = None

    @classmethod
    def from_env(cls) -> "SmtpConfig":
        """Cria configuração a partir de variáveis de ambiente.

        Busca as seguintes variáveis:
        - MAIL_SMTP_SERVER
        - MAIL_SMTP_PORT
        - MAIL_SENDER
        - EMAIL_DESTINATARIOS (separados por vírgula)
        - MAIL_CC (opcional)

        Returns:
            SmtpConfig com valores das variáveis de ambiente.

        Raises:
            ConfiguracaoError: Se alguma variável obrigatória não existir.

        Examples:
            >>> config = SmtpConfig.from_env()
        """
        from .env_config import obter_variavel_env

        try:
            destinatarios_str = obter_variavel_env("EMAIL_DESTINATARIOS").strip()
            destinatarios = [
                email.strip()
                for email in destinatarios_str.split(',')
                if email.strip()
            ]

            import os
            cc = os.getenv("MAIL_CC")

            return cls(
                servidor=obter_variavel_env("MAIL_SMTP_SERVER"),
                porta=int(obter_variavel_env("MAIL_SMTP_PORT")),
                remetente=obter_variavel_env("MAIL_SENDER"),
                destinatarios_padrao=destinatarios,
                cc=cc,
            )
        except Exception as e:
            raise ConfiguracaoError(
                "Variáveis de ambiente SMTP incompletas",
                details={"erro_original": str(e)}
            ) from e


@dataclass(frozen=True)
class LogConfig:
    """Configuração de logging.

    Attributes:
        prefixo: Nome do módulo/pipeline para identificação.
        pasta_logs: Diretório onde os logs serão salvos.
        rotation: Critério de rotação (tamanho ou tempo).
        retention: Tempo de retenção dos logs.
        level: Nível mínimo de log.

    Examples:
        >>> config = LogConfig(
        ...     prefixo="etl_ouvidorias",
        ...     pasta_logs="/var/log/nia",
        ...     rotation="50 MB",
        ...     retention="30 days",
        ...     level="INFO"
        ... )
    """

    prefixo: str
    pasta_logs: str = "logs"
    rotation: str = "10 MB"
    retention: str = "7 days"
    level: str = "DEBUG"

    @classmethod
    def padrao_nia(cls, prefixo: str) -> "LogConfig":
        """Cria configuração com padrões do NIA.

        Args:
            prefixo: Nome do pipeline.

        Returns:
            LogConfig com configurações padrão NIA:
            - Rotação: 50 MB
            - Retenção: 30 dias
            - Nível: INFO

        Examples:
            >>> config = LogConfig.padrao_nia("ouvidorias_etl")
        """
        return cls(
            prefixo=prefixo,
            pasta_logs="logs",
            rotation="50 MB",
            retention="30 days",
            level="INFO"
        )
