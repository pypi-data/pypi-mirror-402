"""Utilitários compartilhados para pipelines ETL do NIA/MPRJ.

Este pacote fornece funções reutilizáveis para:
- Configuração de ambiente (env_config)
- Envio de emails via SMTP (email_smtp)
- Conexões com bancos de dados Oracle e PostgreSQL (database)
- Configuração de logging padronizado (logger_config)
- Processamento e exportação de CSV (processa_csv)
- Manipulação de arquivos e diretórios (limpeza_pastas)

Exemplo de uso:
    from nia_etl_utils import obter_variavel_env, configurar_logger_padrao_nia
    from nia_etl_utils import conectar_postgresql_nia, exportar_para_csv

    # Configuração
    configurar_logger_padrao_nia("meu_pipeline")
    db_host = obter_variavel_env('DB_POSTGRESQL_HOST')

    # Conexão e processamento
    cur, conn = conectar_postgresql_nia()
    # ... processar dados ...
    exportar_para_csv(df, "resultado", "2025_01_19", "/dados")
"""

__version__ = "0.1.0"
__author__ = "Nícolas Galdino Esmael"

# ============================================================================
# IMPORTS PRINCIPAIS - Funções mais usadas exportadas diretamente
# ============================================================================

# Configuração de ambiente
from .env_config import obter_variavel_env

# Email
from .email_smtp import enviar_email_smtp, obter_destinatarios_padrao

# Database - PostgreSQL
from .database import (
    conectar_postgresql,
    conectar_postgresql_nia,
    conectar_postgresql_opengeo,
    obter_engine_postgresql,
    obter_engine_postgresql_nia,
    obter_engine_postgresql_opengeo,
)

# Database - Oracle
from .database import (
    conectar_oracle,
    conectar_oracle_ouvidorias,
    fechar_conexao,
)

# Logging
from .logger_config import (
    configurar_logger,
    configurar_logger_padrao_nia,
    remover_handlers_existentes,
)

# Processamento CSV
from .processa_csv import (
    exportar_para_csv,
    extrair_e_exportar_csv,
    exportar_multiplos_csv,
)

# Processamento CSV Paralelo
from .processa_csv_paralelo import (
    processar_csv_paralelo,
    calcular_chunksize,
)

# Manipulação de arquivos
from .limpeza_pastas import (
    limpar_pasta,
    remover_pasta_recursivamente,
    criar_pasta_se_nao_existir,
)


__all__ = [
    # Metadata
    "__version__",
    "__author__",

    # Env config
    "obter_variavel_env",

    # Email
    "enviar_email_smtp",
    "obter_destinatarios_padrao",

    # Database - PostgreSQL
    "conectar_postgresql",
    "conectar_postgresql_nia",
    "conectar_postgresql_opengeo",
    "obter_engine_postgresql",
    "obter_engine_postgresql_nia",
    "obter_engine_postgresql_opengeo",

    # Database - Oracle
    "conectar_oracle",
    "conectar_oracle_ouvidorias",
    "fechar_conexao",

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
]
