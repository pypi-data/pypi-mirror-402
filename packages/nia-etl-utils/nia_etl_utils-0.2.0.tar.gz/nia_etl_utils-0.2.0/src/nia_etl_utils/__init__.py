"""Utilitários compartilhados para pipelines ETL do NIA/MPRJ.

Este pacote fornece funções reutilizáveis para:
- Configuração de ambiente (env_config)
- Configurações de conexão e email (config)
- Exceções customizadas (exceptions)
- Resultados estruturados (results)
- Envio de emails via SMTP (email_smtp)
- Conexões com bancos de dados Oracle e PostgreSQL (database)
- Configuração de logging padronizado (logger_config)
- Processamento e exportação de CSV (processa_csv)
- Processamento paralelo de CSV grandes (processa_csv_paralelo)
- Manipulação de arquivos e diretórios (limpeza_pastas)

Exemplo de uso:

    from nia_etl_utils import (
        configurar_logger_padrao_nia,
        conectar_postgresql_nia,
        exportar_para_csv,
        PostgresConfig,
    )
    from nia_etl_utils.exceptions import ConexaoError, ExtracaoVaziaError

    # Configuração
    configurar_logger_padrao_nia("meu_pipeline")

    # Conexão com context manager
    try:
        with conectar_postgresql_nia() as conn:
            conn.cursor.execute("SELECT * FROM tabela")
            dados = conn.cursor.fetchall()
    except ConexaoError as e:
        logger.error(f"Falha na conexão: {e}")
        sys.exit(1)  # decisão do CHAMADOR

    # Ou com configuração explícita (para testes)
    config = PostgresConfig(
        host="localhost",
        port="5432",
        database="teste",
        user="user",
        password="pass"
    )
    with conectar_postgresql(config) as conn:
        # ...
"""

__version__ = "0.2.0"
__author__ = "Nícolas Galdino Esmael"

# =============================================================================
# EXCEÇÕES - Importar primeiro para uso em type hints
# =============================================================================

# =============================================================================
# CONFIGURAÇÕES (Dataclasses)
# =============================================================================
from .config import (
    LogConfig,
    OracleConfig,
    PostgresConfig,
    SmtpConfig,
)

# Database - Funções core
# Database - Wrappers de conveniência
from .database import (
    conectar_oracle,
    conectar_oracle_ouvidorias,
    conectar_postgresql,
    conectar_postgresql_nia,
    conectar_postgresql_opengeo,
    obter_engine_postgresql,
    obter_engine_postgresql_nia,
    obter_engine_postgresql_opengeo,
)

# Email
from .email_smtp import (
    enviar_email,
    enviar_email_smtp,
    obter_destinatarios_padrao,
)

# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================
# Configuração de ambiente
from .env_config import (
    obter_variavel_env,
    obter_variavel_env_bool,
    obter_variavel_env_int,
    obter_variavel_env_lista,
)
from .exceptions import (
    # Arquivos
    ArquivoError,
    ConexaoError,
    # Configuração
    ConfiguracaoError,
    # Database
    DatabaseError,
    DestinatarioError,
    DiretorioError,
    # Email
    EmailError,
    EscritaArquivoError,
    # Extração
    ExtracaoError,
    ExtracaoVaziaError,
    LeituraArquivoError,
    # Base
    NiaEtlError,
    ProcessamentoError,
    SmtpError,
    # Validação
    ValidacaoError,
    VariavelAmbienteError,
)

# Manipulação de arquivos
from .limpeza_pastas import (
    criar_pasta_se_nao_existir,
    limpar_pasta,
    listar_arquivos,
    remover_pasta_recursivamente,
)

# Logging
from .logger_config import (
    configurar_logger,
    configurar_logger_padrao_nia,
    remover_handlers_existentes,
)

# Processamento CSV
from .processa_csv import (
    exportar_multiplos_csv,
    exportar_para_csv,
    extrair_e_exportar_csv,
)

# Processamento CSV Paralelo
from .processa_csv_paralelo import (
    calcular_chunksize,
    processar_csv_paralelo,
)

# =============================================================================
# RESULTADOS (Dataclasses)
# =============================================================================
from .results import (
    Conexao,
    ResultadoEmail,
    ResultadoExtracao,
    ResultadoLote,
)

# =============================================================================
# __all__ - Exportações públicas
# =============================================================================

__all__ = [
    # Metadata
    "__version__",
    "__author__",
    # Exceções - Base
    "NiaEtlError",
    # Exceções - Configuração
    "ConfiguracaoError",
    "VariavelAmbienteError",
    # Exceções - Database
    "DatabaseError",
    "ConexaoError",
    # Exceções - Arquivos
    "ArquivoError",
    "DiretorioError",
    "EscritaArquivoError",
    "LeituraArquivoError",
    # Exceções - Extração
    "ExtracaoError",
    "ExtracaoVaziaError",
    "ProcessamentoError",
    # Exceções - Email
    "EmailError",
    "DestinatarioError",
    "SmtpError",
    # Exceções - Validação
    "ValidacaoError",
    # Configurações
    "PostgresConfig",
    "OracleConfig",
    "SmtpConfig",
    "LogConfig",
    # Resultados
    "Conexao",
    "ResultadoExtracao",
    "ResultadoLote",
    "ResultadoEmail",
    # Env config
    "obter_variavel_env",
    "obter_variavel_env_int",
    "obter_variavel_env_bool",
    "obter_variavel_env_lista",
    # Email
    "enviar_email",
    "enviar_email_smtp",
    "obter_destinatarios_padrao",
    # Database - Core
    "conectar_postgresql",
    "conectar_oracle",
    "obter_engine_postgresql",
    # Database - Wrappers
    "conectar_postgresql_nia",
    "conectar_postgresql_opengeo",
    "conectar_oracle_ouvidorias",
    "obter_engine_postgresql_nia",
    "obter_engine_postgresql_opengeo",
    # Logging
    "configurar_logger",
    "configurar_logger_padrao_nia",
    "remover_handlers_existentes",
    # CSV
    "exportar_para_csv",
    "extrair_e_exportar_csv",
    "exportar_multiplos_csv",
    # CSV Paralelo
    "processar_csv_paralelo",
    "calcular_chunksize",
    # Arquivos
    "limpar_pasta",
    "remover_pasta_recursivamente",
    "criar_pasta_se_nao_existir",
    "listar_arquivos",
]
