"""Testes para o módulo email_smtp."""
from unittest.mock import patch, MagicMock
import pytest
import smtplib

from nia_etl_utils.email_smtp import (
    obter_destinatarios_padrao,
    enviar_email_smtp
)


class TestObterDestinatariosPadrao:
    """Testes para a função obter_destinatarios_padrao."""

    def test_obter_destinatarios_validos(self, monkeypatch):
        """Testa obtenção de destinatários válidos."""
        monkeypatch.setenv("EMAIL_DESTINATARIOS", "email1@example.com,email2@example.com")

        destinatarios = obter_destinatarios_padrao()

        assert destinatarios == ["email1@example.com", "email2@example.com"]

    def test_obter_destinatarios_com_espacos(self, monkeypatch):
        """Testa que espaços extras são removidos."""
        monkeypatch.setenv("EMAIL_DESTINATARIOS", " email1@example.com , email2@example.com ")

        destinatarios = obter_destinatarios_padrao()

        assert destinatarios == ["email1@example.com", "email2@example.com"]

    def test_obter_destinatarios_vazio(self, monkeypatch):
        """Testa que string vazia causa sys.exit(1)."""
        monkeypatch.setenv("EMAIL_DESTINATARIOS", "")

        with pytest.raises(SystemExit) as exc_info:
            obter_destinatarios_padrao()

        assert exc_info.value.code == 1

    def test_obter_destinatarios_apenas_virgulas(self, monkeypatch):
        """Testa que apenas vírgulas causa sys.exit(1)."""
        monkeypatch.setenv("EMAIL_DESTINATARIOS", ",,,")

        with pytest.raises(SystemExit) as exc_info:
            obter_destinatarios_padrao()

        assert exc_info.value.code == 1

    def test_obter_destinatarios_unico(self, monkeypatch):
        """Testa destinatário único (sem vírgulas)."""
        monkeypatch.setenv("EMAIL_DESTINATARIOS", "email@example.com")

        destinatarios = obter_destinatarios_padrao()

        assert destinatarios == ["email@example.com"]


class TestEnviarEmailSmtp:
    """Testes para a função enviar_email_smtp."""

    @patch('nia_etl_utils.email_smtp.smtplib.SMTP')
    @patch('nia_etl_utils.email_smtp.obter_variavel_env')
    def test_enviar_email_sucesso(self, mock_obter_env, mock_smtp):
        """Testa envio de email bem-sucedido."""
        # Mock das variáveis de ambiente
        mock_obter_env.side_effect = lambda x: {
            'MAIL_SMTP_SERVER': 'smtp.example.com',
            'MAIL_SMTP_PORT': '587',
            'MAIL_SENDER': 'sender@example.com'
        }[x]

        # Mock do servidor SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Envia email
        enviar_email_smtp(
            corpo_do_email="Teste",
            assunto="Assunto Teste",
            destinatarios=["dest@example.com"]
        )

        # Verifica que sendmail foi chamado
        mock_server.sendmail.assert_called_once()

    @patch('nia_etl_utils.email_smtp.smtplib.SMTP')
    @patch('nia_etl_utils.email_smtp.obter_variavel_env')
    def test_enviar_email_com_anexo(self, mock_obter_env, mock_smtp, tmp_path):
        """Testa envio de email com anexo."""
        # Mock das variáveis de ambiente
        mock_obter_env.side_effect = lambda x: {
            'MAIL_SMTP_SERVER': 'smtp.example.com',
            'MAIL_SMTP_PORT': '587',
            'MAIL_SENDER': 'sender@example.com'
        }[x]

        # Mock do servidor SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Cria arquivo de teste
        arquivo_anexo = tmp_path / "anexo.txt"
        arquivo_anexo.write_text("conteudo do anexo")

        # Envia email com anexo
        enviar_email_smtp(
            corpo_do_email="Teste",
            assunto="Assunto Teste",
            destinatarios=["dest@example.com"],
            anexo=str(arquivo_anexo)
        )

        # Verifica que sendmail foi chamado
        mock_server.sendmail.assert_called_once()

    @patch('nia_etl_utils.email_smtp.smtplib.SMTP')
    @patch('nia_etl_utils.email_smtp.obter_variavel_env')
    def test_enviar_email_erro_smtp(self, mock_obter_env, mock_smtp):
        """Testa que erro SMTP causa sys.exit(1)."""
        # Mock das variáveis de ambiente
        mock_obter_env.side_effect = lambda x: {
            'MAIL_SMTP_SERVER': 'smtp.example.com',
            'MAIL_SMTP_PORT': '587',
            'MAIL_SENDER': 'sender@example.com'
        }[x]

        # Mock que lança exceção
        mock_smtp.return_value.__enter__.side_effect = smtplib.SMTPException("Erro SMTP")

        with pytest.raises(SystemExit) as exc_info:
            enviar_email_smtp(
                corpo_do_email="Teste",
                assunto="Assunto Teste",
                destinatarios=["dest@example.com"]
            )

        assert exc_info.value.code == 1

    def test_enviar_email_sem_destinatarios(self):
        """Testa que falta de destinatários causa sys.exit(1)."""
        with pytest.raises(SystemExit) as exc_info:
            enviar_email_smtp(
                corpo_do_email="Teste",
                assunto="Assunto Teste",
                destinatarios=[]
            )

        assert exc_info.value.code == 1

    @patch('nia_etl_utils.email_smtp.smtplib.SMTP')
    @patch('nia_etl_utils.email_smtp.obter_variavel_env')
    def test_enviar_email_anexo_inexistente(self, mock_obter_env, mock_smtp):
        """Testa que anexo inexistente causa sys.exit(1)."""
        # Mock das variáveis de ambiente
        mock_obter_env.side_effect = lambda x: {
            'MAIL_SMTP_SERVER': 'smtp.example.com',
            'MAIL_SMTP_PORT': '587',
            'MAIL_SENDER': 'sender@example.com'
        }[x]

        with pytest.raises(SystemExit) as exc_info:
            enviar_email_smtp(
                corpo_do_email="Teste",
                assunto="Assunto Teste",
                destinatarios=["dest@example.com"],
                anexo="/caminho/inexistente/arquivo.txt"
            )

        assert exc_info.value.code == 1

    @patch('nia_etl_utils.email_smtp.obter_destinatarios_padrao')
    @patch('nia_etl_utils.email_smtp.smtplib.SMTP')
    @patch('nia_etl_utils.email_smtp.obter_variavel_env')
    def test_enviar_email_usa_destinatarios_padrao(self, mock_obter_env, mock_smtp, mock_destinatarios):
        """Testa que destinatários padrão são usados quando não fornecidos."""
        # Mock das variáveis de ambiente
        mock_obter_env.side_effect = lambda x: {
            'MAIL_SMTP_SERVER': 'smtp.example.com',
            'MAIL_SMTP_PORT': '587',
            'MAIL_SENDER': 'sender@example.com'
        }[x]

        # Mock destinatários padrão
        mock_destinatarios.return_value = ["padrao@example.com"]

        # Mock do servidor SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Envia sem especificar destinatários
        enviar_email_smtp(
            corpo_do_email="Teste",
            assunto="Assunto Teste"
        )

        # Verifica que obter_destinatarios_padrao foi chamado
        mock_destinatarios.assert_called_once()
