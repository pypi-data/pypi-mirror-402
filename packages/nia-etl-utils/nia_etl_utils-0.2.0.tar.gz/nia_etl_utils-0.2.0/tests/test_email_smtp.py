"""Testes para o módulo email_smtp."""

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from nia_etl_utils.email_smtp import enviar_email_smtp, obter_destinatarios_padrao
from nia_etl_utils.exceptions import DestinatarioError, LeituraArquivoError, SmtpError


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
        """Testa que string vazia levanta DestinatarioError."""
        monkeypatch.setenv("EMAIL_DESTINATARIOS", "")

        with pytest.raises(DestinatarioError) as exc_info:
            obter_destinatarios_padrao()

        assert "EMAIL_DESTINATARIOS" in str(exc_info.value)

    def test_obter_destinatarios_apenas_virgulas(self, monkeypatch):
        """Testa que apenas vírgulas levanta DestinatarioError."""
        monkeypatch.setenv("EMAIL_DESTINATARIOS", ",,,")

        with pytest.raises(DestinatarioError):
            obter_destinatarios_padrao()

    def test_obter_destinatarios_unico(self, monkeypatch):
        """Testa destinatário único (sem vírgulas)."""
        monkeypatch.setenv("EMAIL_DESTINATARIOS", "email@example.com")

        destinatarios = obter_destinatarios_padrao()

        assert destinatarios == ["email@example.com"]


class TestEnviarEmailSmtp:
    """Testes para a função enviar_email_smtp."""

    @patch('nia_etl_utils.email_smtp.SmtpConfig.from_env')
    @patch('nia_etl_utils.email_smtp.smtplib.SMTP')
    def test_enviar_email_sucesso(self, mock_smtp, mock_config):
        """Testa envio de email bem-sucedido."""
        # Mock da configuração
        mock_config.return_value = MagicMock(
            servidor='smtp.example.com',
            porta=587,
            remetente='sender@example.com',
            destinatarios_padrao=['default@example.com'],
            cc=None
        )

        # Mock do servidor SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Envia email
        resultado = enviar_email_smtp(
            corpo_do_email="Teste",
            assunto="Assunto Teste",
            destinatarios=["dest@example.com"]
        )

        # Verifica resultado
        assert resultado.sucesso is True
        assert resultado.destinatarios == ["dest@example.com"]
        assert resultado.assunto == "Assunto Teste"

        # Verifica que sendmail foi chamado
        mock_server.sendmail.assert_called_once()

    @patch('nia_etl_utils.email_smtp.SmtpConfig.from_env')
    @patch('nia_etl_utils.email_smtp.smtplib.SMTP')
    def test_enviar_email_com_anexo(self, mock_smtp, mock_config, tmp_path):
        """Testa envio de email com anexo."""
        # Mock da configuração
        mock_config.return_value = MagicMock(
            servidor='smtp.example.com',
            porta=587,
            remetente='sender@example.com',
            destinatarios_padrao=['default@example.com'],
            cc=None
        )

        # Mock do servidor SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Cria arquivo de teste
        arquivo_anexo = tmp_path / "anexo.txt"
        arquivo_anexo.write_text("conteudo do anexo")

        # Envia email com anexo
        resultado = enviar_email_smtp(
            corpo_do_email="Teste",
            assunto="Assunto Teste",
            destinatarios=["dest@example.com"],
            anexo=str(arquivo_anexo)
        )

        # Verifica resultado
        assert resultado.sucesso is True
        assert resultado.anexo == str(arquivo_anexo)

        # Verifica que sendmail foi chamado
        mock_server.sendmail.assert_called_once()

    @patch('nia_etl_utils.email_smtp.SmtpConfig.from_env')
    @patch('nia_etl_utils.email_smtp.smtplib.SMTP')
    def test_enviar_email_erro_smtp(self, mock_smtp, mock_config):
        """Testa que erro SMTP levanta SmtpError."""
        # Mock da configuração
        mock_config.return_value = MagicMock(
            servidor='smtp.example.com',
            porta=587,
            remetente='sender@example.com',
            destinatarios_padrao=['default@example.com'],
            cc=None
        )

        # Mock que lança exceção
        mock_smtp.return_value.__enter__.side_effect = smtplib.SMTPException("Erro SMTP")

        with pytest.raises(SmtpError) as exc_info:
            enviar_email_smtp(
                corpo_do_email="Teste",
                assunto="Assunto Teste",
                destinatarios=["dest@example.com"]
            )

        assert "SMTP" in str(exc_info.value)

    @patch('nia_etl_utils.email_smtp.SmtpConfig.from_env')
    def test_enviar_email_sem_destinatarios(self, mock_config):
        """Testa que falta de destinatários levanta DestinatarioError."""
        # Mock da configuração com destinatários padrão vazio
        mock_config.return_value = MagicMock(
            servidor='smtp.example.com',
            porta=587,
            remetente='sender@example.com',
            destinatarios_padrao=[],
            cc=None
        )

        with pytest.raises(DestinatarioError) as exc_info:
            enviar_email_smtp(
                corpo_do_email="Teste",
                assunto="Assunto Teste",
                destinatarios=[]
            )

        assert "destinatário" in str(exc_info.value).lower()

    @patch('nia_etl_utils.email_smtp.SmtpConfig.from_env')
    def test_enviar_email_anexo_inexistente(self, mock_config):
        """Testa que anexo inexistente levanta LeituraArquivoError."""
        # Mock da configuração
        mock_config.return_value = MagicMock(
            servidor='smtp.example.com',
            porta=587,
            remetente='sender@example.com',
            destinatarios_padrao=['default@example.com'],
            cc=None
        )

        with pytest.raises(LeituraArquivoError) as exc_info:
            enviar_email_smtp(
                corpo_do_email="Teste",
                assunto="Assunto Teste",
                destinatarios=["dest@example.com"],
                anexo="/caminho/inexistente/arquivo.txt"
            )

        assert "inexistente" in str(exc_info.value).lower() or "não encontrado" in str(exc_info.value).lower()

    @patch('nia_etl_utils.email_smtp.SmtpConfig.from_env')
    @patch('nia_etl_utils.email_smtp.smtplib.SMTP')
    def test_enviar_email_usa_destinatarios_padrao(self, mock_smtp, mock_config):
        """Testa que destinatários padrão são usados quando não fornecidos."""
        # Mock da configuração
        mock_config.return_value = MagicMock(
            servidor='smtp.example.com',
            porta=587,
            remetente='sender@example.com',
            destinatarios_padrao=['padrao@example.com'],
            cc=None
        )

        # Mock do servidor SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Envia sem especificar destinatários
        resultado = enviar_email_smtp(
            corpo_do_email="Teste",
            assunto="Assunto Teste"
        )

        # Verifica que usou destinatários padrão
        assert resultado.destinatarios == ['padrao@example.com']

    @patch('nia_etl_utils.email_smtp.SmtpConfig.from_env')
    @patch('nia_etl_utils.email_smtp.smtplib.SMTP')
    def test_enviar_email_erro_conexao(self, mock_smtp, mock_config):
        """Testa que erro de conexão levanta SmtpError."""
        # Mock da configuração
        mock_config.return_value = MagicMock(
            servidor='smtp.example.com',
            porta=587,
            remetente='sender@example.com',
            destinatarios_padrao=['default@example.com'],
            cc=None
        )

        # Mock que lança exceção de conexão
        mock_smtp.return_value.__enter__.side_effect = ConnectionError("Conexão recusada")

        with pytest.raises(SmtpError) as exc_info:
            enviar_email_smtp(
                corpo_do_email="Teste",
                assunto="Assunto Teste",
                destinatarios=["dest@example.com"]
            )

        assert "conexão" in str(exc_info.value).lower() or "smtp" in str(exc_info.value).lower()

    @patch('nia_etl_utils.email_smtp.SmtpConfig.from_env')
    @patch('nia_etl_utils.email_smtp.smtplib.SMTP')
    def test_enviar_email_destinatarios_recusados(self, mock_smtp, mock_config):
        """Testa que destinatários recusados levanta SmtpError."""
        # Mock da configuração
        mock_config.return_value = MagicMock(
            servidor='smtp.example.com',
            porta=587,
            remetente='sender@example.com',
            destinatarios_padrao=['default@example.com'],
            cc=None
        )

        # Mock do servidor SMTP
        mock_server = MagicMock()
        mock_server.sendmail.side_effect = smtplib.SMTPRecipientsRefused(
            {"dest@example.com": (550, "User not found")} # type: ignore
        )
        mock_smtp.return_value.__enter__.return_value = mock_server

        with pytest.raises(SmtpError) as exc_info:
            enviar_email_smtp(
                corpo_do_email="Teste",
                assunto="Assunto Teste",
                destinatarios=["dest@example.com"]
            )

        assert "recusaram" in str(exc_info.value).lower() or "refused" in str(exc_info.value).lower()
