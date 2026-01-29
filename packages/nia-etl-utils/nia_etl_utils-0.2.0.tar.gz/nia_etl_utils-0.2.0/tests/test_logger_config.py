"""Testes para o módulo logger_config."""

from pathlib import Path

import pytest
from loguru import logger

from nia_etl_utils.exceptions import ValidacaoError
from nia_etl_utils.logger_config import (
    configurar_logger,
    configurar_logger_padrao_nia,
    remover_handlers_existentes,
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
        """Testa que prefixo vazio levanta ValidacaoError."""
        with pytest.raises(ValidacaoError) as exc_info:
            configurar_logger(
                prefixo="",
                data_extracao="2025_01_19",
                pasta_logs=str(tmp_path)
            )

        assert "prefixo" in str(exc_info.value).lower()
        assert exc_info.value.details["parametro"] == "prefixo"

    def test_configurar_logger_prefixo_espacos(self, tmp_path):
        """Testa que prefixo com apenas espaços levanta ValidacaoError."""
        with pytest.raises(ValidacaoError) as exc_info:
            configurar_logger(
                prefixo="   ",
                data_extracao="2025_01_19",
                pasta_logs=str(tmp_path)
            )

        assert "prefixo" in str(exc_info.value).lower()

    def test_configurar_logger_data_vazia(self, tmp_path):
        """Testa que data vazia levanta ValidacaoError."""
        with pytest.raises(ValidacaoError) as exc_info:
            configurar_logger(
                prefixo="teste",
                data_extracao="",
                pasta_logs=str(tmp_path)
            )

        assert "data" in str(exc_info.value).lower()
        assert exc_info.value.details["parametro"] == "data_extracao"

    def test_configurar_logger_data_espacos(self, tmp_path):
        """Testa que data com apenas espaços levanta ValidacaoError."""
        with pytest.raises(ValidacaoError) as exc_info:
            configurar_logger(
                prefixo="teste",
                data_extracao="   ",
                pasta_logs=str(tmp_path)
            )

        assert "data" in str(exc_info.value).lower()

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

    def test_configurar_logger_retorna_caminho_correto(self, tmp_path):
        """Testa que retorna caminho no formato esperado."""
        caminho = configurar_logger(
            prefixo="meu_pipeline",
            data_extracao="2025_01_20",
            pasta_logs=str(tmp_path)
        )

        esperado = tmp_path / "meu_pipeline" / "meu_pipeline_2025_01_20.log"
        assert caminho == str(esperado)

    def test_configurar_logger_niveis_diferentes(self, tmp_path):
        """Testa configuração com diferentes níveis de log."""
        for nivel in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            logger.remove()
            caminho = configurar_logger(
                prefixo=f"teste_{nivel.lower()}",
                data_extracao="2025_01_19",
                pasta_logs=str(tmp_path),
                level=nivel
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

    def test_configurar_logger_padrao_usa_data_hoje(self, tmp_path, monkeypatch):
        """Testa que usa a data de hoje no nome do arquivo."""
        from datetime import datetime

        monkeypatch.chdir(tmp_path)

        caminho = configurar_logger_padrao_nia("teste")

        # Verifica que contém data de hoje
        data_hoje = datetime.now().strftime("%Y_%m_%d")
        assert data_hoje in caminho

    def test_configurar_logger_padrao_prefixo_vazio(self, tmp_path, monkeypatch):
        """Testa que prefixo vazio levanta ValidacaoError."""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(ValidacaoError):
            configurar_logger_padrao_nia("")


class TestRemoverHandlersExistentes:
    """Testes para a função remover_handlers_existentes."""

    def test_remover_handlers(self, tmp_path):
        """Testa remoção de handlers existentes."""
        # Adiciona handler
        logger.add(str(tmp_path / "teste.log"))

        # Remove
        remover_handlers_existentes()

        # Se chegou aqui sem erro, funcionou
        assert True

    def test_remover_handlers_multiplos(self, tmp_path):
        """Testa remoção de múltiplos handlers."""
        # Adiciona vários handlers
        logger.add(str(tmp_path / "teste1.log"))
        logger.add(str(tmp_path / "teste2.log"))
        logger.add(str(tmp_path / "teste3.log"))

        # Remove todos
        remover_handlers_existentes()

        # Se chegou aqui sem erro, funcionou
        assert True

    def test_remover_handlers_sem_handlers(self):
        """Testa remoção quando não há handlers customizados."""
        logger.remove()

        # Não deve dar erro
        remover_handlers_existentes()

        assert True
