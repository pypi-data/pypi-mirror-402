"""Módulo responsável por enviar e-mails com ou sem anexo via SMTP."""
import os
import smtplib
import sys
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from loguru import logger

from .env_config import obter_variavel_env


def obter_destinatarios_padrao() -> list[str]:
    """Obtém lista de destinatários da variável de ambiente EMAIL_DESTINATARIOS.

    Returns:
        Lista de emails extraída da env var.

    Raises:
        SystemExit: Se EMAIL_DESTINATARIOS estiver vazia ou contiver apenas valores inválidos.
    """
    destinatarios_str = obter_variavel_env("EMAIL_DESTINATARIOS").strip()
    destinatarios = [email.strip() for email in destinatarios_str.split(',') if email.strip()]

    if not destinatarios:
        logger.error(
            "EMAIL_DESTINATARIOS está vazia ou contém apenas valores inválidos. "
            "Configure a variável com destinatários separados por vírgula."
        )
        sys.exit(1)

    return destinatarios


def enviar_email_smtp(
    corpo_do_email: str,
    assunto: str,
    destinatarios: list[str] | None = None,
    anexo: str | None = None
) -> None:
    """Envia um e-mail com ou sem anexo via SMTP.

    Args:
        corpo_do_email: Texto que será enviado no corpo do e-mail.
        assunto: Assunto da mensagem.
        destinatarios: Lista de endereços de e-mail. Se None, usa EMAIL_DESTINATARIOS da env var.
        anexo: Caminho para arquivo anexo. Defaults to None.

    Raises:
        SystemExit: Se destinatários não forem fornecidos e EMAIL_DESTINATARIOS não existir,
                   ou se ocorrer qualquer erro durante o envio do email.

    Examples:
        >>> # Uso padrão (destinatários da env var)
        >>> enviar_email_smtp(
        ...     corpo_do_email="Pipeline concluído",
        ...     assunto="[PROD] ETL Finalizado"
        ... )

        >>> # Com destinatários específicos
        >>> enviar_email_smtp(
        ...     corpo_do_email="Relatório executivo",
        ...     assunto="Relatório Mensal",
        ...     destinatarios=["diretor@mprj.mp.br"],
        ...     anexo="/tmp/relatorio.pdf"
        ... )
    """
    if destinatarios is None:
        destinatarios = obter_destinatarios_padrao()

    if not destinatarios:
        logger.error("Nenhum destinatário fornecido. E-mail não pode ser enviado.")
        sys.exit(1)

    try:
        email_msg = MIMEMultipart()
        email_msg['From'] = obter_variavel_env('MAIL_SENDER')
        email_msg['To'] = ", ".join(destinatarios)
        email_msg['Cc'] = 'gadg.etl@mprj.mp.br'
        email_msg['Subject'] = assunto

        corpo_da_mensagem = MIMEText(corpo_do_email, 'plain')
        email_msg.attach(corpo_da_mensagem)

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

        logger.info("Iniciando conexão com o servidor SMTP...")
        with smtplib.SMTP(
            obter_variavel_env('MAIL_SMTP_SERVER'),
            int(obter_variavel_env('MAIL_SMTP_PORT'))
        ) as server:
            server.sendmail(
                obter_variavel_env('MAIL_SENDER'),
                destinatarios,
                email_msg.as_string()
            )
            logger.info(f"E-mail enviado com sucesso para {destinatarios}")

    except smtplib.SMTPRecipientsRefused as error:
        logger.error(f"Destinatários recusaram o e-mail: {error}")
        sys.exit(1)
    except smtplib.SMTPDataError as error:
        logger.error(f"Erro durante a transferência de dados: {error}")
        sys.exit(1)
    except smtplib.SMTPException as error:
        logger.error(f"Erro ao enviar o e-mail: {error}")
        sys.exit(1)
    except ConnectionError as error:
        logger.error(f"Erro de conexão com servidor SMTP: {error}")
        sys.exit(1)
    except FileNotFoundError as error:
        logger.error(f"Arquivo de anexo não encontrado: {error}")
        sys.exit(1)
    except Exception as error:
        logger.error(f"Erro inesperado ao enviar e-mail: {error}")
        sys.exit(1)
