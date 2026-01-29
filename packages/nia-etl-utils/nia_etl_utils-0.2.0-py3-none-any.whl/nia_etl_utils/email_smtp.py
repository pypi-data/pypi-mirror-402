"""Módulo responsável por enviar e-mails via SMTP.

Fornece funções para envio de emails com suporte a anexos,
múltiplos destinatários e configuração via variáveis de ambiente.

Examples:
    Envio simples:

    >>> from nia_etl_utils import enviar_email_smtp
    >>> enviar_email_smtp(
    ...     corpo_do_email="Pipeline concluído com sucesso",
    ...     assunto="[PROD] ETL Finalizado"
    ... )

    Envio com configuração explícita:

    >>> from nia_etl_utils import enviar_email, SmtpConfig
    >>> config = SmtpConfig(
    ...     servidor="smtp.empresa.com",
    ...     porta=587,
    ...     remetente="sistema@empresa.com",
    ...     destinatarios_padrao=["admin@empresa.com"]
    ... )
    >>> resultado = enviar_email(
    ...     config=config,
    ...     corpo="Relatório em anexo",
    ...     assunto="Relatório Mensal",
    ...     anexo="/tmp/relatorio.pdf"
    ... )
"""

import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from loguru import logger

from .config import SmtpConfig
from .env_config import obter_variavel_env
from .exceptions import DestinatarioError, LeituraArquivoError, SmtpError
from .results import ResultadoEmail


def obter_destinatarios_padrao() -> list[str]:
    """Obtém lista de destinatários da variável de ambiente.

    Busca a variável EMAIL_DESTINATARIOS e faz parse dos emails
    separados por vírgula.

    Returns:
        Lista de endereços de email.

    Raises:
        DestinatarioError: Se EMAIL_DESTINATARIOS estiver vazia
            ou contiver apenas valores inválidos.

    Examples:
        >>> # Com EMAIL_DESTINATARIOS="admin@x.com,dev@x.com"
        >>> destinatarios = obter_destinatarios_padrao()
        >>> print(destinatarios)
        ['admin@x.com', 'dev@x.com']
    """
    destinatarios_str = obter_variavel_env("EMAIL_DESTINATARIOS").strip()
    destinatarios = [
        email.strip()
        for email in destinatarios_str.split(',')
        if email.strip()
    ]

    if not destinatarios:
        raise DestinatarioError(
            "EMAIL_DESTINATARIOS está vazia ou contém apenas valores inválidos. "
            "Configure a variável com destinatários separados por vírgula."
        )

    return destinatarios


def enviar_email(
    config: SmtpConfig,
    corpo: str,
    assunto: str,
    destinatarios: list[str] | None = None,
    anexo: str | None = None
) -> ResultadoEmail:
    """Envia email via SMTP usando configuração explícita.

    Args:
        config: Configuração do servidor SMTP.
        corpo: Texto do corpo do email.
        assunto: Assunto da mensagem.
        destinatarios: Lista de destinatários. Se None, usa
            config.destinatarios_padrao.
        anexo: Caminho para arquivo anexo (opcional).

    Returns:
        ResultadoEmail com status do envio.

    Raises:
        DestinatarioError: Se nenhum destinatário for fornecido.
        LeituraArquivoError: Se arquivo de anexo não existir.
        SmtpError: Se houver erro na comunicação com servidor SMTP.

    Examples:
        >>> config = SmtpConfig.from_env()
        >>> resultado = enviar_email(
        ...     config=config,
        ...     corpo="Relatório em anexo",
        ...     assunto="Relatório Diário",
        ...     anexo="/tmp/relatorio.pdf"
        ... )
        >>> if resultado.sucesso:
        ...     print("Email enviado!")
    """
    # Define destinatários
    dest = destinatarios or config.destinatarios_padrao

    if not dest:
        raise DestinatarioError("Nenhum destinatário fornecido para envio do email")

    # Valida anexo se fornecido
    if anexo and not Path(anexo).exists():
        raise LeituraArquivoError(
            f"Arquivo de anexo não encontrado: {anexo}",
            details={"caminho": anexo}
        )

    try:
        # Monta mensagem
        email_msg = MIMEMultipart()
        email_msg['From'] = config.remetente
        email_msg['To'] = ", ".join(dest)
        if config.cc:
            email_msg['Cc'] = config.cc
        email_msg['Subject'] = assunto

        corpo_da_mensagem = MIMEText(corpo, 'plain')
        email_msg.attach(corpo_da_mensagem)

        # Anexa arquivo se fornecido
        if anexo:
            attachment = MIMEBase('application', 'octet-stream')
            with open(anexo, 'rb') as attachment_file:
                attachment.set_payload(attachment_file.read())
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename={os.path.basename(anexo)}'
            )
            email_msg.attach(attachment)

        # Envia
        logger.info(f"Conectando ao servidor SMTP {config.servidor}:{config.porta}...")

        with smtplib.SMTP(config.servidor, config.porta) as server:
            server.sendmail(config.remetente, dest, email_msg.as_string())
            logger.success(f"Email enviado com sucesso para {dest}")

        return ResultadoEmail(
            sucesso=True,
            destinatarios=dest,
            assunto=assunto,
            anexo=anexo
        )

    except smtplib.SMTPRecipientsRefused as e:
        raise SmtpError(
            "Destinatários recusaram o email",
            details={"destinatarios": dest, "erro": str(e)}
        ) from e
    except smtplib.SMTPDataError as e:
        raise SmtpError(
            "Erro durante transferência de dados SMTP",
            details={"erro": str(e)}
        ) from e
    except smtplib.SMTPException as e:
        raise SmtpError(
            "Erro SMTP ao enviar email",
            details={"servidor": config.servidor, "erro": str(e)}
        ) from e
    except ConnectionError as e:
        raise SmtpError(
            f"Erro de conexão com servidor SMTP {config.servidor}",
            details={"servidor": config.servidor, "porta": config.porta, "erro": str(e)}
        ) from e


def enviar_email_smtp(
    corpo_do_email: str,
    assunto: str,
    destinatarios: list[str] | None = None,
    anexo: str | None = None
) -> ResultadoEmail:
    """Envia email via SMTP usando variáveis de ambiente.

    Função de conveniência que carrega configuração de variáveis
    de ambiente automaticamente.

    Variáveis utilizadas:
        - MAIL_SMTP_SERVER: Endereço do servidor SMTP
        - MAIL_SMTP_PORT: Porta do servidor
        - MAIL_SENDER: Endereço do remetente
        - EMAIL_DESTINATARIOS: Destinatários padrão (separados por vírgula)
        - MAIL_CC: Endereço para cópia (opcional)

    Args:
        corpo_do_email: Texto que será enviado no corpo do email.
        assunto: Assunto da mensagem.
        destinatarios: Lista de endereços de email. Se None, usa
            EMAIL_DESTINATARIOS da variável de ambiente.
        anexo: Caminho para arquivo anexo (opcional).

    Returns:
        ResultadoEmail com status do envio.

    Raises:
        DestinatarioError: Se nenhum destinatário for fornecido e
            EMAIL_DESTINATARIOS não existir.
        LeituraArquivoError: Se arquivo de anexo não existir.
        SmtpError: Se houver erro na comunicação com servidor SMTP.
        ConfiguracaoError: Se variáveis de ambiente estiverem ausentes.

    Examples:
        Uso padrão (destinatários da variável de ambiente):

        >>> enviar_email_smtp(
        ...     corpo_do_email="Pipeline concluído",
        ...     assunto="[PROD] ETL Finalizado"
        ... )

        Com destinatários específicos:

        >>> enviar_email_smtp(
        ...     corpo_do_email="Relatório executivo",
        ...     assunto="Relatório Mensal",
        ...     destinatarios=["diretor@mprj.mp.br"],
        ...     anexo="/tmp/relatorio.pdf"
        ... )

        Com tratamento de erro:

        >>> from nia_etl_utils.exceptions import SmtpError
        >>> try:
        ...     enviar_email_smtp("Teste", "Assunto Teste")
        ... except SmtpError as e:
        ...     logger.error(f"Falha no envio: {e}")
    """
    config = SmtpConfig.from_env()

    return enviar_email(
        config=config,
        corpo=corpo_do_email,
        assunto=assunto,
        destinatarios=destinatarios,
        anexo=anexo
    )
