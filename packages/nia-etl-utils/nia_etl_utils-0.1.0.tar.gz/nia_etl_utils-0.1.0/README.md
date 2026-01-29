# nia-etl-utils

## ✨ Visão Geral

Biblioteca Python centralizada contendo **utilitários compartilhados** para pipelines ETL do NIA/MPRJ. Consolida funções reutilizáveis para configuração de ambiente, notificações por email, conexões de banco de dados, logging padronizado e processamento de dados.

Desenvolvida para **eliminar duplicação de código**, **padronizar boas práticas** e **facilitar manutenção** em todos os projetos de engenharia de dados do NIA.

---

## 📂 Estrutura do Projeto

```plaintext
.
├── src/
│   └── nia_etl_utils/                          # Pacote principal
│       ├── __init__.py                         # Exporta funções principais
│       ├── env_config.py                       # Gerenciamento de variáveis de ambiente
│       ├── email_smtp.py                       # Envio de emails via SMTP
│       ├── database.py                         # Conexões PostgreSQL e Oracle
│       ├── logger_config.py                    # Configuração de logging com Loguru
│       ├── processa_csv.py                     # Processamento e exportação de CSV
│       ├── processa_csv_paralelo.py            # Processamento paralelo de CSV grandes
│       └── limpeza_pastas.py                   # Manipulação de arquivos e diretórios
│
├── tests/                                      # Testes unitários (~60+ testes)
│   ├── conftest.py                             # Fixtures compartilhadas
│   ├── test_env_config.py                      # Testes de variáveis de ambiente
│   ├── test_email_smtp.py                      # Testes de email (com mocks)
│   ├── test_database.py                        # Testes de conexões (com mocks)
│   ├── test_logger_config.py                   # Testes de logging
│   ├── test_processa_csv.py                    # Testes de processamento CSV
│   ├── test_processa_csv_paralelo.py           # Testes de processamento paralelo
│   ├── test_limpeza_pastas.py                  # Testes de manipulação de arquivos
│   └── README.md                               # Documentação dos testes
│
├── .env.example                                # Template de variáveis de ambiente
├── .gitignore                                  # Arquivos ignorados pelo Git
├── .gitlab-ci.yml                              # Pipeline CI/CD (testes + cobertura)
├── .python-version                             # Versão Python do projeto (3.13.3)
├── pyproject.toml                              # Configuração do pacote Python
├── requirements.txt                            # Dependências do projeto
├── run_tests.sh                                # Script helper para executar testes
└── README.md
```

---

## 🔧 Módulos Disponíveis

### 1️⃣ Configuração de Ambiente (`env_config.py`)

Gerenciamento robusto de variáveis de ambiente com validação e falha explícita.

```python
from nia_etl_utils import obter_variavel_env

# Variável obrigatória (falha com sys.exit(1) se não existir)
db_host = obter_variavel_env('DB_POSTGRESQL_HOST')

# Variável opcional com fallback
porta = obter_variavel_env('DB_PORT', default='5432')
```

**Características:**
- ✅ Falha rápida com `sys.exit(1)` quando variável obrigatória não existe
- ✅ Suporte a valores padrão opcionais
- ✅ Logs descritivos de erro

---

### 2️⃣ Email SMTP (`email_smtp.py`)

Envio de emails com ou sem anexo, suportando destinatários configuráveis via env var.

```python
from nia_etl_utils import enviar_email_smtp

# Uso padrão (destinatários da env var EMAIL_DESTINATARIOS)
enviar_email_smtp(
    corpo_do_email="Pipeline concluído com sucesso",
    assunto="[PROD] ETL Finalizado"
)

# Com destinatários específicos e anexo
enviar_email_smtp(
    destinatarios=["diretor@mprj.mp.br"],
    corpo_do_email="Relatório executivo anexo",
    assunto="Relatório Mensal",
    anexo="/tmp/relatorio.pdf"
)
```

**Características:**
- ✅ Destinatários configuráveis via `EMAIL_DESTINATARIOS`
- ✅ Suporte a anexos
- ✅ Falha explícita com `sys.exit(1)` em erros SMTP
- ✅ Validação de arquivos anexos

---

### 3️⃣ Conexões de Banco (`database.py`)

Conexões padronizadas para PostgreSQL (psycopg2 + SQLAlchemy) e Oracle (cx_Oracle).

#### PostgreSQL

```python
from nia_etl_utils import conectar_postgresql_nia, fechar_conexao

# Conecta no PostgreSQL do NIA
cur, conn = conectar_postgresql_nia()
cur.execute("SELECT * FROM tabela")
resultados = cur.fetchall()
fechar_conexao(cur, conn)

# Engine SQLAlchemy (para pandas)
from nia_etl_utils import obter_engine_postgresql_nia
import pandas as pd

engine = obter_engine_postgresql_nia()
df = pd.read_sql("SELECT * FROM tabela", engine)
```

#### Oracle

```python
from nia_etl_utils import conectar_oracle, fechar_conexao

# Conecta no Oracle
cur, conn = conectar_oracle()
cur.execute("SELECT * FROM tabela WHERE ROWNUM <= 10")
resultados = cur.fetchall()
fechar_conexao(cur, conn)
```

#### Bancos Adicionais (Genérico)

```python
from nia_etl_utils import conectar_postgresql

# Conecta em qualquer PostgreSQL configurado com sufixo customizado
# Requer: DB_POSTGRESQL_HOST_SUFIXO, DB_POSTGRESQL_PORT_SUFIXO, etc
cur, conn = conectar_postgresql("_SUFIXO")
```

**Características:**
- ✅ Funções genéricas + wrappers de conveniência
- ✅ Suporte a múltiplos bancos PostgreSQL (via sufixos)
- ✅ Logs informativos de conexão
- ✅ Falha explícita com `sys.exit(1)` em erros de conexão
- ✅ `fechar_conexao()` segura (não falha se erro ao fechar)

---

### 4️⃣ Logging (`logger_config.py`)

Configuração padronizada do Loguru com rotação, retenção e níveis customizáveis.

```python
from nia_etl_utils import configurar_logger_padrao_nia
from loguru import logger

# Configuração rápida com padrões do NIA
caminho_log = configurar_logger_padrao_nia("ouvidorias_etl")
logger.info("Pipeline iniciado")

# Configuração customizada
from nia_etl_utils import configurar_logger

caminho_log = configurar_logger(
    prefixo="meu_pipeline",
    data_extracao="2025_01_19",
    pasta_logs="/var/logs/nia",
    rotation="50 MB",
    retention="30 days",
    level="INFO"
)
```

**Características:**
- ✅ Rotação automática de arquivos por tamanho
- ✅ Retenção configurável (padrão: 7 dias em DEV, 30 dias em PROD)
- ✅ Formato padronizado com timestamp, nível, módulo, função e linha
- ✅ Logs organizados por pipeline e data

---

### 5️⃣ Processamento CSV (`processa_csv.py`)

Exportação de DataFrames para CSV com nomenclatura padronizada e validações.

```python
from nia_etl_utils import exportar_para_csv, extrair_e_exportar_csv
import pandas as pd

# Exportação simples
df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
caminho = exportar_para_csv(
    df=df,
    nome_arquivo="dados_clientes",
    data_extracao="2025_01_19",
    diretorio_base="/tmp/dados"
)

# Extração + Exportação
def extrair_dados():
    # ... lógica de extração ...
    return pd.DataFrame({"dados": [1, 2, 3]})

caminho = extrair_e_exportar_csv(
    nome_extracao="dados_vendas",
    funcao_extracao=extrair_dados,
    data_extracao="2025_01_19",
    diretorio_base="/tmp/dados",
    falhar_se_vazio=True  # sys.exit(1) se DataFrame vazio
)

# Múltiplas extrações em lote
from nia_etl_utils import exportar_multiplos_csv

extractions = [
    {"nome": "clientes", "funcao": extrair_clientes},
    {"nome": "vendas", "funcao": extrair_vendas}
]

resultados = exportar_multiplos_csv(
    extractions=extractions,
    data_extracao="2025_01_19",
    diretorio_base="/tmp/dados"
)
```

**Características:**
- ✅ Nomenclatura padronizada: `{nome}_{data}.csv`
- ✅ Criação automática de diretórios
- ✅ Logs com informações úteis (linhas, colunas, tamanho)
- ✅ Controle de falha em DataFrames vazios

---

### 6️⃣ Manipulação de Arquivos (`limpeza_pastas.py`)

Utilitários para limpeza e criação de diretórios.

```python
from nia_etl_utils import limpar_pasta, remover_pasta_recursivamente, criar_pasta_se_nao_existir

# Limpa pasta (remove arquivos, mantém subdiretórios)
limpar_pasta("/tmp/dados")

# Remove pasta completa (arquivos + subdiretórios)
remover_pasta_recursivamente("/tmp/temporario")

# Cria pasta se não existir (incluindo pais)
criar_pasta_se_nao_existir("/dados/processados/2025/01")
```

**Características:**
- ✅ Uso de `pathlib.Path` (moderno e seguro)
- ✅ Validações de permissão
- ✅ Falha explícita com `sys.exit(1)` em erros

---

### 7️⃣ Processamento Paralelo de CSV (`processa_csv_paralelo.py`)

Processa arquivos CSV grandes em paralelo usando multiprocessing com chunks otimizados.

```python
from nia_etl_utils import processar_csv_paralelo

# Função de transformação customizada
def limpar_texto(texto):
    return texto.strip().upper()

# Processa CSV grande em paralelo
processar_csv_paralelo(
    caminho_entrada="dados_brutos.csv",
    caminho_saida="dados_limpos.csv",
    colunas_para_tratar=["nome", "descricao", "observacao"],
    funcao_transformacao=limpar_texto,
    remover_entrada=True  # Remove arquivo original após processar
)

# Com configurações customizadas
processar_csv_paralelo(
    caminho_entrada="dados_gigantes.csv",
    caminho_saida="dados_processados.csv",
    colunas_para_tratar=["texto"],
    funcao_transformacao=limpar_texto,
    chunksize=5000,              # Tamanho customizado de chunk
    num_processos=4,             # Número de processos paralelos
    normalizar_colunas=False,    # Mantém case original das colunas
    remover_entrada=False        # Preserva arquivo de entrada
)
```

**Características:**
- ✅ Processamento paralelo automático usando `multiprocessing.Pool`
- ✅ Chunksize calculado automaticamente baseado no tamanho do arquivo
- ✅ Heurística inteligente:
  - Arquivos < 500MB: chunks de 10.000 linhas
  - Arquivos 500MB-2GB: chunks de 5.000 linhas
  - Arquivos 2-5GB: chunks de 2.000 linhas
  - Arquivos > 5GB: chunks de 1.000 linhas
- ✅ Normalização opcional de nomes de colunas (lowercase)
- ✅ Remoção opcional do arquivo de entrada
- ✅ Logs informativos de progresso
- ✅ Suporta qualquer função de transformação customizada

**Quando usar:**
- 📊 Arquivos CSV com milhões de linhas
- 🔄 Transformações pesadas em texto (limpeza, normalização)
- ⚡ Necessidade de processar múltiplas colunas rapidamente
- 💾 Arquivos que não cabem confortavelmente na memória

---

## 📦 Instalação

### Via GitLab (Recomendado)

```bash
# Instalar versão específica
pip install git+https://gitlab-dti.mprj.mp.br/nia/etl-nia/nia-etl-utils.git@v0.1.0

# Ou no requirements.txt
nia-etl-utils @ git+https://gitlab-dti.mprj.mp.br/nia/etl-nia/nia-etl-utils.git@v0.1.0
```

### Modo Desenvolvimento

```bash
git clone https://gitlab-dti.mprj.mp.br/nia/etl-nia/nia-etl-utils.git
cd nia-etl-utils
pip install -e ".[dev]"
```

---

## ⚙️ Configuração

### 1. Criar arquivo `.env`

```bash
cp .env.example .env
```

### 2. Configurar variáveis de ambiente

```env
# Email SMTP
MAIL_SMTP_SERVER=smtp.mprj.mp.br
MAIL_SMTP_PORT=587
MAIL_SENDER=etl@mprj.mp.br
EMAIL_DESTINATARIOS=equipe@mprj.mp.br,gestor@mprj.mp.br

# PostgreSQL - NIA
DB_POSTGRESQL_HOST=postgres-nia.mprj.mp.br
DB_POSTGRESQL_PORT=5432
DB_POSTGRESQL_DATABASE=nia_database
DB_POSTGRESQL_USER=usuario
DB_POSTGRESQL_PASSWORD=senha

# PostgreSQL - OpenGeo
DB_POSTGRESQL_HOST_OPENGEO=postgres-opengeo.mprj.mp.br
DB_POSTGRESQL_PORT_OPENGEO=5432
DB_POSTGRESQL_DATABASE_OPENGEO=opengeo_database
DB_POSTGRESQL_USER_OPENGEO=usuario
DB_POSTGRESQL_PASSWORD_OPENGEO=senha

# Oracle
DB_ORACLE_HOST=oracle.mprj.mp.br
DB_ORACLE_PORT=1521
DB_ORACLE_SERVICE_NAME=ORCL
DB_ORACLE_USER=usuario
DB_ORACLE_PASSWORD=senha
```

---

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=src/nia_etl_utils --cov-report=term-missing

# Ou usar o script helper
./run_tests.sh --coverage --verbose
```

### Cobertura Atual

- **~70 testes unitários** (incluindo testes de processamento paralelo)
- **~90% de cobertura** de código
- Testes com mocks (sem dependência de banco/SMTP real)

Veja `tests/README.md` para documentação completa dos testes.

---

## 🚀 Exemplo de Uso Completo

```python
from nia_etl_utils import (
    configurar_logger_padrao_nia,
    obter_variavel_env,
    conectar_postgresql_nia,
    exportar_para_csv,
    processar_csv_paralelo,
    fechar_conexao
)
from loguru import logger
import pandas as pd

# 1. Configura logging
configurar_logger_padrao_nia("meu_pipeline")

# 2. Conecta no banco
logger.info("Iniciando conexão com banco de dados...")
cur, conn = conectar_postgresql_nia()

# 3. Extrai dados
logger.info("Extraindo dados...")
cur.execute("SELECT * FROM tabela WHERE data >= CURRENT_DATE - 7")
resultados = cur.fetchall()
colunas = [desc[0] for desc in cur.description]
df = pd.DataFrame(resultados, columns=colunas)

# 4. Fecha conexão
fechar_conexao(cur, conn)
logger.info(f"Extração concluída: {len(df)} registros")

# 5. Exporta CSV
from datetime import datetime
data_hoje = datetime.now().strftime("%Y_%m_%d")

caminho = exportar_para_csv(
    df=df,
    nome_arquivo="dados_extraidos",
    data_extracao=data_hoje,
    diretorio_base="/dados/processados"
)

# 6. Processa CSV em paralelo (se necessário)
if len(df) > 100000:  # Só paraleliza arquivos grandes
    def limpar_descricao(texto):
        return texto.strip().upper() if texto else ""

    processar_csv_paralelo(
        caminho_entrada=caminho,
        caminho_saida=f"/dados/processados/dados_limpos_{data_hoje}.csv",
        colunas_para_tratar=["descricao", "observacao"],
        funcao_transformacao=limpar_descricao,
        remover_entrada=True
    )
    logger.success("Processamento paralelo concluído!")

logger.success(f"Pipeline concluído! Arquivo: {caminho}")
```

---

## ☁️ Integração com Airflow

### Usando em KubernetesPodOperator

```python
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

task = KubernetesPodOperator(
    task_id="meu_etl",
    name="meu-etl-pod",
    namespace="airflow-nia-stage",
    image="python:3.13.3",
    cmds=[
        "sh", "-c",
        "pip install git+https://gitlab-dti.mprj.mp.br/nia/etl-nia/nia-etl-utils.git@v0.1.0 && "
        "python src/extract.py"
    ],
    env_vars={
        "DB_POSTGRESQL_HOST": "...",
        "EMAIL_DESTINATARIOS": "equipe@mprj.mp.br"
    },
    # ... outras configs
)
```

---

## ⚙️ Tecnologias Utilizadas

- Python 3.13.3
- Loguru (logging)
- python-dotenv (env vars)
- cx_Oracle (Oracle)
- psycopg2 (PostgreSQL)
- SQLAlchemy (engines)
- pandas (processamento de dados)
- pytest + pytest-cov (testes)
- ruff (linting)

---

## 📋 Versionamento

Este projeto usa [Semantic Versioning](https://semver.org/):

- **MAJOR**: Mudanças incompatíveis na API
- **MINOR**: Novas funcionalidades (retrocompatíveis)
- **PATCH**: Correções de bugs

**Versão atual:** `v0.1.0`

---

## 🔔 Monitoramento e Logs

- Logging estruturado via Loguru
- Logs organizados por pipeline e data em `/logs`
- Scripts retornam `sys.exit(1)` em falhas para integração com Airflow
- Notificações via email em pipelines de produção

---

## 🔧 CI/CD

Pipeline automatizado no GitLab com:

- ✅ Testes unitários (pytest)
- ✅ Cobertura de código (>= 80%)
- ✅ Linting (ruff)
- ✅ Relatórios de cobertura (HTML + XML)
- ✅ Execução em branches e merge requests

---

## ✏️ Contribuição

Merge requests são bem-vindos. Sempre crie uma branch a partir de `main`.

### Checklist para Contribuir:

- [ ] Testes passam: `pytest`
- [ ] Cobertura >= 70%: `pytest --cov=src/nia_etl_utils --cov-fail-under=80`
- [ ] Lint OK: `ruff check src/ tests/`
- [ ] Commits semânticos: `feat:`, `fix:`, `refactor:`, etc.
- [ ] Documentação atualizada

---

## 🔐 Licença

Projeto de uso interno do MPRJ. Sem licença pública.

---

## ✨ Responsável Técnico

**Nícolas Galdino Esmael** | Engenheiro de Dados - NIA | MPRJ

---

## 📚 Documentação Adicional

- [Documentação de Testes](tests/README.md)
- [Template de Variáveis de Ambiente](.env.example)
- [Configuração do Projeto](pyproject.toml)
