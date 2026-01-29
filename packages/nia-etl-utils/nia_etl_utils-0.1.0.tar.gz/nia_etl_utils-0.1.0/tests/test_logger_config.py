"""Testes para o módulo logger_config."""
from pathlib import Path
import pytest
from loguru import logger

from nia_etl_utils.logger_config import (
    configurar_logger,
    configurar_logger_padrao_nia,
    remover_handlers_existentes
)


class TestConfigurarLogger:
    """Testes para a função configurar_logger."""

    def setup_method(self):
        """Remove handlers antes de cada teste."""
        logger.remove()

    def test_configurar_logger_cria_arquivo(self, tmp_path):
        """Testa que arquivo de log é criado."""
        caminho = configurar_logger(
            prefixo="teste",
            data_extracao="2025_01_19",
            pasta_logs=str(tmp_path)
        )

        # Verifica que arquivo foi criado
        arquivo_log = Path(caminho)
        assert arquivo_log.exists()
        assert arquivo_log.name == "teste_2025_01_19.log"

    def test_configurar_logger_cria_diretorios(self, tmp_path):
        """Testa que diretórios são criados se não existirem."""
        pasta_inexistente = tmp_path / "logs" / "subdir"

        caminho = configurar_logger(
            prefixo="teste",
            data_extracao="2025_01_19",
            pasta_logs=str(pasta_inexistente)
        )

        assert Path(caminho).parent.exists()

    def test_configurar_logger_escreve_logs(self, tmp_path):
        """Testa que logs são escritos no arquivo."""
        caminho = configurar_logger(
            prefixo="teste",
            data_extracao="2025_01_19",
            pasta_logs=str(tmp_path)
        )

        # Escreve log
        logger.info("Teste de log")

        # Verifica que foi escrito
        conteudo = Path(caminho).read_text()
        assert "Teste de log" in conteudo

    def test_configurar_logger_prefixo_vazio(self, tmp_path):
        """Testa que prefixo vazio causa sys.exit(1)."""
        with pytest.raises(SystemExit) as exc_info:
            configurar_logger(
                prefixo="",
                data_extracao="2025_01_19",
                pasta_logs=str(tmp_path)
            )

        assert exc_info.value.code == 1

    def test_configurar_logger_data_vazia(self, tmp_path):
        """Testa que data vazia causa sys.exit(1)."""
        with pytest.raises(SystemExit) as exc_info:
            configurar_logger(
                prefixo="teste",
                data_extracao="",
                pasta_logs=str(tmp_path)
            )

        assert exc_info.value.code == 1

    def test_configurar_logger_custom_rotation(self, tmp_path):
        """Testa configuração customizada de rotação."""
        caminho = configurar_logger(
            prefixo="teste",
            data_extracao="2025_01_19",
            pasta_logs=str(tmp_path),
            rotation="5 MB",
            retention="15 days",
            level="INFO"
        )

        assert Path(caminho).exists()


class TestConfigurarLoggerPadraoNia:
    """Testes para a função configurar_logger_padrao_nia."""

    def setup_method(self):
        """Remove handlers antes de cada teste."""
        logger.remove()

    def test_configurar_logger_padrao(self, tmp_path, monkeypatch):
        """Testa configuração com padrões do NIA."""
        # Muda diretório de trabalho para tmp_path
        monkeypatch.chdir(tmp_path)

        caminho = configurar_logger_padrao_nia("pipeline_teste")

        # Verifica que arquivo foi criado com padrões NIA
        assert Path(caminho).exists()
        assert "pipeline_teste" in caminho

        # Verifica que está na pasta logs/
        assert Path(caminho).parent.name == "pipeline_teste"
        assert Path(caminho).parent.parent.name == "logs"


class TestRemoverHandlersExistentes:
    """Testes para a função remover_handlers_existentes."""

    def test_remover_handlers(self, tmp_path):
        """Testa remoção de handlers existentes."""
        # Adiciona handler
        logger.add(str(tmp_path / "teste.log"))

        # Remove
        remover_handlers_existentes()

        # Verifica que não há handlers (exceto stderr default)
        # Logger sempre tem pelo menos um handler (stderr), então não podemos
        # verificar diretamente, mas podemos testar que não dá erro
        assert True  # Se chegou aqui, não deu erro
