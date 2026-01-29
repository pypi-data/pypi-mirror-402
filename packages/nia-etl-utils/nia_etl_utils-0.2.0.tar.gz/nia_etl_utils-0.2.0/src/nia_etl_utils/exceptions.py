"""Exceções customizadas para o pacote nia_etl_utils.

Este módulo define a hierarquia de exceções usada em todo o pacote,
permitindo tratamento granular de erros pelos consumidores da biblioteca.

Hierarquia:
    NiaEtlError (base)
    ├── ConfiguracaoError
    │   └── VariavelAmbienteError
    ├── DatabaseError
    │   └── ConexaoError
    ├── ArquivoError
    │   ├── EscritaArquivoError
    │   ├── LeituraArquivoError
    │   └── DiretorioError
    ├── ExtracaoError
    │   └── ExtracaoVaziaError
    ├── EmailError
    │   ├── DestinatarioError
    │   └── SmtpError
    └── ValidacaoError

Examples:
    Capturando erros específicos:

    >>> from nia_etl_utils.exceptions import ConexaoError, ExtracaoVaziaError
    >>>
    >>> try:
    ...     conn = conectar_postgresql(config)
    ... except ConexaoError as e:
    ...     logger.error(f"Falha na conexão: {e}")
    ...     # tratamento específico

    Capturando qualquer erro do pacote:

    >>> from nia_etl_utils.exceptions import NiaEtlError
    >>>
    >>> try:
    ...     executar_pipeline()
    ... except NiaEtlError as e:
    ...     logger.error(f"Erro no pipeline: {e}")
    ...     sys.exit(1)  # decisão do CHAMADOR
"""


class NiaEtlError(Exception):
    """Exceção base para todos os erros do pacote nia_etl_utils.

    Todas as exceções customizadas do pacote herdam desta classe,
    permitindo captura genérica quando necessário.

    Attributes:
        message: Descrição do erro.
        details: Informações adicionais opcionais sobre o erro.

    Examples:
        >>> try:
        ...     raise NiaEtlError("Algo deu errado", details={"codigo": 123})
        ... except NiaEtlError as e:
        ...     print(e.message)
        ...     print(e.details)
        Algo deu errado
        {'codigo': 123}
    """

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Detalhes: {self.details}"
        return self.message


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================


class ConfiguracaoError(NiaEtlError):
    """Erro de configuração do sistema.

    Levantado quando há problemas com configurações necessárias
    para o funcionamento do pacote.

    Examples:
        >>> raise ConfiguracaoError("Configuração inválida para conexão")
    """

    pass


class VariavelAmbienteError(ConfiguracaoError):
    """Variável de ambiente ausente ou inválida.

    Levantado quando uma variável de ambiente obrigatória não está
    definida e nenhum valor padrão foi fornecido.

    Attributes:
        nome_variavel: Nome da variável de ambiente que causou o erro.

    Examples:
        >>> raise VariavelAmbienteError("DB_HOST")
    """

    def __init__(self, nome_variavel: str):
        self.nome_variavel = nome_variavel
        super().__init__(
            f"Variável de ambiente '{nome_variavel}' não encontrada "
            f"e nenhum valor padrão foi fornecido",
            details={"variavel": nome_variavel}
        )


# =============================================================================
# DATABASE
# =============================================================================


class DatabaseError(NiaEtlError):
    """Erro base para operações de banco de dados.

    Examples:
        >>> raise DatabaseError("Falha na operação de banco de dados")
    """

    pass


class ConexaoError(DatabaseError):
    """Falha ao estabelecer conexão com banco de dados.

    Levantado quando não é possível conectar ao banco de dados,
    seja por credenciais inválidas, host inacessível ou outros
    problemas de conectividade.

    Examples:
        >>> raise ConexaoError(
        ...     "Timeout ao conectar",
        ...     details={"host": "localhost", "port": 5432}
        ... )
    """

    pass


# =============================================================================
# ARQUIVOS E DIRETÓRIOS
# =============================================================================


class ArquivoError(NiaEtlError):
    """Erro base para operações de arquivo e diretório.

    Examples:
        >>> raise ArquivoError("Operação de arquivo falhou")
    """

    pass


class EscritaArquivoError(ArquivoError):
    """Falha ao escrever arquivo.

    Levantado quando não é possível criar ou escrever em um arquivo,
    seja por falta de permissão, disco cheio ou caminho inválido.

    Examples:
        >>> raise EscritaArquivoError(
        ...     "Sem permissão para escrita",
        ...     details={"caminho": "/etc/arquivo.csv"}
        ... )
    """

    pass


class LeituraArquivoError(ArquivoError):
    """Falha ao ler arquivo.

    Levantado quando não é possível ler um arquivo, seja porque
    ele não existe, não há permissão ou está corrompido.

    Examples:
        >>> raise LeituraArquivoError(
        ...     "Arquivo não encontrado",
        ...     details={"caminho": "/tmp/dados.csv"}
        ... )
    """

    pass


class DiretorioError(ArquivoError):
    """Falha em operação de diretório.

    Levantado quando não é possível criar, limpar ou remover
    um diretório.

    Examples:
        >>> raise DiretorioError(
        ...     "Sem permissão para criar diretório",
        ...     details={"caminho": "/root/dados"}
        ... )
    """

    pass


# =============================================================================
# EXTRAÇÃO E PROCESSAMENTO
# =============================================================================


class ExtracaoError(NiaEtlError):
    """Erro base para operações de extração de dados.

    Examples:
        >>> raise ExtracaoError("Falha na extração de dados")
    """

    pass


class ExtracaoVaziaError(ExtracaoError):
    """Extração retornou DataFrame vazio ou None.

    Levantado quando uma função de extração não retorna dados.
    Pode ser esperado em alguns contextos (extração incremental
    sem novos dados) ou indicar um problema.

    Attributes:
        nome_extracao: Identificador da extração que falhou.

    Examples:
        >>> raise ExtracaoVaziaError("clientes_novos")
    """

    def __init__(self, nome_extracao: str):
        self.nome_extracao = nome_extracao
        super().__init__(
            f"Nenhum dado retornado para extração '{nome_extracao}'",
            details={"extracao": nome_extracao}
        )


class ProcessamentoError(ExtracaoError):
    """Erro durante processamento de dados.

    Levantado quando há falha durante transformação ou
    processamento de dados.

    Examples:
        >>> raise ProcessamentoError(
        ...     "Falha ao processar chunk",
        ...     details={"chunk": 5, "erro": "memória insuficiente"}
        ... )
    """

    pass


# =============================================================================
# EMAIL
# =============================================================================


class EmailError(NiaEtlError):
    """Erro base para operações de email.

    Examples:
        >>> raise EmailError("Falha no envio de email")
    """

    pass


class DestinatarioError(EmailError):
    """Erro relacionado a destinatários de email.

    Levantado quando não há destinatários configurados ou
    quando os destinatários são inválidos.

    Examples:
        >>> raise DestinatarioError("Nenhum destinatário configurado")
    """

    pass


class SmtpError(EmailError):
    """Erro de comunicação com servidor SMTP.

    Levantado quando há falha na conexão ou comunicação
    com o servidor de email.

    Examples:
        >>> raise SmtpError(
        ...     "Conexão recusada",
        ...     details={"servidor": "smtp.empresa.com", "porta": 587}
        ... )
    """

    pass


# =============================================================================
# VALIDAÇÃO
# =============================================================================


class ValidacaoError(NiaEtlError):
    """Erro de validação de parâmetros ou dados.

    Levantado quando parâmetros fornecidos são inválidos
    ou não atendem aos requisitos esperados.

    Examples:
        >>> raise ValidacaoError(
        ...     "Nome do arquivo não pode ser vazio",
        ...     details={"parametro": "nome_arquivo", "valor": ""}
        ... )
    """

    pass
