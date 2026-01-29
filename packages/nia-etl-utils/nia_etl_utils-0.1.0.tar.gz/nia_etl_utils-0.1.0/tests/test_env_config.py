"""Testes para o módulo env_config."""
import pytest

from nia_etl_utils.env_config import obter_variavel_env


class TestObterVariavelEnv:
    """Testes para a função obter_variavel_env."""

    def test_obter_variavel_existente(self, monkeypatch):
        """Testa obtenção de variável de ambiente que existe."""
        monkeypatch.setenv("TEST_VAR", "valor_teste")

        resultado = obter_variavel_env("TEST_VAR")

        assert resultado == "valor_teste"

    def test_obter_variavel_com_default(self, monkeypatch):
        """Testa obtenção com valor padrão quando variável não existe."""
        monkeypatch.delenv("TEST_VAR_INEXISTENTE", raising=False)

        resultado = obter_variavel_env("TEST_VAR_INEXISTENTE", default="valor_padrao")

        assert resultado == "valor_padrao"

    def test_obter_variavel_inexistente_sem_default(self, monkeypatch):
        """Testa que sys.exit(1) é chamado quando variável não existe e não há default."""
        monkeypatch.delenv("TEST_VAR_INEXISTENTE", raising=False)

        with pytest.raises(SystemExit) as exc_info:
            obter_variavel_env("TEST_VAR_INEXISTENTE")

        assert exc_info.value.code == 1

    def test_obter_variavel_vazia_com_default(self, monkeypatch):
        """Testa que variável vazia retorna string vazia (não usa default)."""
        monkeypatch.setenv("TEST_VAR_VAZIA", "")

        # Variável existe (mesmo vazia), então não usa default
        resultado = obter_variavel_env("TEST_VAR_VAZIA", default="valor_padrao")

        assert resultado == ""

    def test_obter_variavel_com_espacos(self, monkeypatch):
        """Testa que espaços em branco são preservados."""
        monkeypatch.setenv("TEST_VAR_ESPACOS", "  valor com espaços  ")

        resultado = obter_variavel_env("TEST_VAR_ESPACOS")

        assert resultado == "  valor com espaços  "

    def test_obter_variavel_numerica(self, monkeypatch):
        """Testa que valores numéricos são retornados como string."""
        monkeypatch.setenv("TEST_VAR_NUM", "12345")

        resultado = obter_variavel_env("TEST_VAR_NUM")

        assert resultado == "12345"
        assert isinstance(resultado, str)

    def test_obter_variavel_default_none_explicito(self, monkeypatch):
        """Testa comportamento quando default é explicitamente None."""
        monkeypatch.delenv("TEST_VAR_INEXISTENTE", raising=False)

        with pytest.raises(SystemExit) as exc_info:
            obter_variavel_env("TEST_VAR_INEXISTENTE", default=None)

        assert exc_info.value.code == 1
