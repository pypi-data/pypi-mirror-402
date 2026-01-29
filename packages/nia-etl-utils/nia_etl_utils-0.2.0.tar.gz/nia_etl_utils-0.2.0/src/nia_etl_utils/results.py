"""Dataclasses de resultado para operações do pacote nia_etl_utils.

Este módulo define estruturas de dados para retorno de operações,
fornecendo informações estruturadas sobre o resultado de cada ação.

Examples:
    Resultado de extração:

    >>> resultado = ResultadoExtracao(
    ...     nome="clientes",
    ...     caminho="/tmp/clientes_2025_01_20.csv",
    ...     linhas=1500,
    ...     sucesso=True
    ... )
    >>> if resultado.sucesso:
    ...     print(f"Exportados {resultado.linhas} registros")

    Resultado com erro:

    >>> resultado = ResultadoExtracao(
    ...     nome="vendas",
    ...     caminho=None,
    ...     linhas=0,
    ...     sucesso=False,
    ...     erro="Nenhum dado retornado"
    ... )
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Conexao:
    """Wrapper para conexão de banco de dados.

    Encapsula cursor e connection, fornecendo interface consistente
    e suporte a context manager para fechamento automático.

    Attributes:
        cursor: Cursor ativo para execução de queries.
        connection: Objeto de conexão subjacente (psycopg2 ou cx_Oracle).
        database: Nome/identificador do banco conectado.

    Examples:
        Uso com context manager (recomendado):

        >>> with conectar_postgresql(config) as conn:
        ...     conn.cursor.execute("SELECT * FROM tabela")
        ...     dados = conn.cursor.fetchall()
        ... # conexão fechada automaticamente

        Uso manual:

        >>> conn = conectar_postgresql(config)
        >>> try:
        ...     conn.cursor.execute("SELECT 1")
        ...     resultado = conn.cursor.fetchone()
        ... finally:
        ...     conn.fechar()

        Acesso aos componentes:

        >>> conn = conectar_postgresql(config)
        >>> conn.cursor.execute("SELECT COUNT(*) FROM usuarios")
        >>> total = conn.cursor.fetchone()[0]
        >>> conn.connection.commit()  # se necessário
        >>> conn.fechar()
    """

    cursor: Any
    connection: Any
    database: str

    def fechar(self) -> None:
        """Encerra cursor e conexão de forma segura.

        Tenta fechar cursor e conexão, logando warnings em caso
        de erro mas nunca levantando exceções.

        Examples:
            >>> conn = conectar_postgresql(config)
            >>> # ... usar conexão ...
            >>> conn.fechar()  # sempre seguro
        """
        from loguru import logger

        try:
            if self.cursor:
                self.cursor.close()
                logger.debug("Cursor fechado com sucesso.")
        except Exception as e:
            logger.warning(f"Erro ao fechar cursor: {e}")

        try:
            if self.connection:
                self.connection.close()
                logger.debug("Conexão encerrada com sucesso.")
        except Exception as e:
            logger.warning(f"Erro ao fechar conexão: {e}")

    def __enter__(self) -> "Conexao":
        """Entrada do context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Saída do context manager - fecha conexão automaticamente."""
        self.fechar()


@dataclass
class ResultadoExtracao:
    """Resultado de uma operação de extração e exportação CSV.

    Fornece informações estruturadas sobre o resultado de uma
    extração, incluindo métricas e status de sucesso/erro.

    Attributes:
        nome: Identificador da extração.
        caminho: Caminho do arquivo CSV gerado (None se falhou).
        linhas: Quantidade de registros extraídos.
        sucesso: True se a operação completou com sucesso.
        erro: Mensagem de erro se sucesso=False, None caso contrário.
        colunas: Quantidade de colunas no DataFrame (opcional).
        tamanho_bytes: Tamanho do arquivo em bytes (opcional).

    Examples:
        Extração bem-sucedida:

        >>> resultado = ResultadoExtracao(
        ...     nome="clientes",
        ...     caminho="/tmp/clientes_2025_01_20.csv",
        ...     linhas=1500,
        ...     sucesso=True,
        ...     colunas=12,
        ...     tamanho_bytes=45000
        ... )
        >>> print(f"Exportados {resultado.linhas} registros para {resultado.caminho}")

        Extração com falha:

        >>> resultado = ResultadoExtracao(
        ...     nome="vendas",
        ...     caminho=None,
        ...     linhas=0,
        ...     sucesso=False,
        ...     erro="Nenhum dado retornado para extração 'vendas'"
        ... )
        >>> if not resultado.sucesso:
        ...     logger.warning(resultado.erro)

        Verificando resultados em lote:

        >>> resultados = exportar_multiplos_csv(extractions, ...)
        >>> sucesso = [r for r in resultados if r.sucesso]
        >>> falhas = [r for r in resultados if not r.sucesso]
        >>> print(f"{len(sucesso)} OK, {len(falhas)} falhas")
    """

    nome: str
    caminho: str | None
    linhas: int
    sucesso: bool
    erro: str | None = None
    colunas: int | None = None
    tamanho_bytes: int | None = None

    @property
    def tamanho_kb(self) -> float | None:
        """Tamanho do arquivo em kilobytes.

        Returns:
            Tamanho em KB ou None se tamanho_bytes não definido.

        Examples:
            >>> resultado.tamanho_bytes = 45000
            >>> resultado.tamanho_kb
            43.945...
        """
        if self.tamanho_bytes is None:
            return None
        return self.tamanho_bytes / 1024

    @property
    def tamanho_mb(self) -> float | None:
        """Tamanho do arquivo em megabytes.

        Returns:
            Tamanho em MB ou None se tamanho_bytes não definido.

        Examples:
            >>> resultado.tamanho_bytes = 1048576
            >>> resultado.tamanho_mb
            1.0
        """
        if self.tamanho_bytes is None:
            return None
        return self.tamanho_bytes / (1024 * 1024)


@dataclass
class ResultadoLote:
    """Resultado consolidado de operações em lote.

    Agrupa múltiplos ResultadoExtracao e fornece métricas
    consolidadas sobre o lote.

    Attributes:
        resultados: Lista de ResultadoExtracao individuais.
        total: Número total de extrações no lote.
        sucesso: Número de extrações bem-sucedidas.
        falhas: Número de extrações que falharam.

    Examples:
        >>> lote = ResultadoLote(resultados=[r1, r2, r3])
        >>> print(f"Taxa de sucesso: {lote.taxa_sucesso:.1%}")
        >>> if lote.todos_sucesso:
        ...     print("Todas extrações OK!")
        >>> for falha in lote.extrações_falhas:
        ...     print(f"Falhou: {falha.nome} - {falha.erro}")
    """

    resultados: list[ResultadoExtracao] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Número total de extrações no lote."""
        return len(self.resultados)

    @property
    def sucesso(self) -> int:
        """Número de extrações bem-sucedidas."""
        return sum(1 for r in self.resultados if r.sucesso)

    @property
    def falhas(self) -> int:
        """Número de extrações que falharam."""
        return sum(1 for r in self.resultados if not r.sucesso)

    @property
    def todos_sucesso(self) -> bool:
        """True se todas as extrações foram bem-sucedidas."""
        return self.falhas == 0

    @property
    def taxa_sucesso(self) -> float:
        """Taxa de sucesso (0.0 a 1.0)."""
        if self.total == 0:
            return 0.0
        return self.sucesso / self.total

    @property
    def extracoes_sucesso(self) -> list[ResultadoExtracao]:
        """Lista de extrações bem-sucedidas."""
        return [r for r in self.resultados if r.sucesso]

    @property
    def extracoes_falhas(self) -> list[ResultadoExtracao]:
        """Lista de extrações que falharam."""
        return [r for r in self.resultados if not r.sucesso]

    @property
    def total_linhas(self) -> int:
        """Total de linhas extraídas em todas as extrações."""
        return sum(r.linhas for r in self.resultados)

    def adicionar(self, resultado: ResultadoExtracao) -> None:
        """Adiciona um resultado ao lote.

        Args:
            resultado: ResultadoExtracao a ser adicionado.

        Examples:
            >>> lote = ResultadoLote()
            >>> lote.adicionar(resultado1)
            >>> lote.adicionar(resultado2)
        """
        self.resultados.append(resultado)


@dataclass
class ResultadoEmail:
    """Resultado de envio de email.

    Attributes:
        sucesso: True se o email foi enviado com sucesso.
        destinatarios: Lista de destinatários do email.
        assunto: Assunto do email enviado.
        erro: Mensagem de erro se sucesso=False.
        anexo: Caminho do anexo enviado (se houver).

    Examples:
        >>> resultado = ResultadoEmail(
        ...     sucesso=True,
        ...     destinatarios=["admin@empresa.com"],
        ...     assunto="Relatório Diário"
        ... )
    """

    sucesso: bool
    destinatarios: list[str]
    assunto: str
    erro: str | None = None
    anexo: str | None = None
