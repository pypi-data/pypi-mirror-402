"""Testes para o módulo env_config."""

import pytest

from nia_etl_utils.env_config import (
    obter_variavel_env,
    obter_variavel_env_bool,
    obter_variavel_env_int,
    obter_variavel_env_lista,
)
from nia_etl_utils.exceptions import VariavelAmbienteError


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
        """Testa que VariavelAmbienteError é levantada quando variável não existe."""
        monkeypatch.delenv("TEST_VAR_INEXISTENTE", raising=False)

        with pytest.raises(VariavelAmbienteError) as exc_info:
            obter_variavel_env("TEST_VAR_INEXISTENTE")

        assert exc_info.value.nome_variavel == "TEST_VAR_INEXISTENTE"
        assert "TEST_VAR_INEXISTENTE" in str(exc_info.value)

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

        with pytest.raises(VariavelAmbienteError) as exc_info:
            obter_variavel_env("TEST_VAR_INEXISTENTE", default=None)

        assert exc_info.value.nome_variavel == "TEST_VAR_INEXISTENTE"


class TestObterVariavelEnvInt:
    """Testes para a função obter_variavel_env_int."""

    def test_obter_int_existente(self, monkeypatch):
        """Testa obtenção de variável inteira."""
        monkeypatch.setenv("TEST_PORT", "5432")
        resultado = obter_variavel_env_int("TEST_PORT")
        assert resultado == 5432
        assert isinstance(resultado, int)

    def test_obter_int_com_default(self, monkeypatch):
        """Testa obtenção de inteiro com valor padrão."""
        monkeypatch.delenv("TEST_PORT_INEXISTENTE", raising=False)
        resultado = obter_variavel_env_int("TEST_PORT_INEXISTENTE", default=3306)
        assert resultado == 3306

    def test_obter_int_inexistente_sem_default(self, monkeypatch):
        """Testa que VariavelAmbienteError é levantada para int inexistente."""
        monkeypatch.delenv("TEST_PORT_INEXISTENTE", raising=False)

        with pytest.raises(VariavelAmbienteError):
            obter_variavel_env_int("TEST_PORT_INEXISTENTE")

    def test_obter_int_valor_invalido(self, monkeypatch):
        """Testa que ValueError é levantada para valor não numérico."""
        monkeypatch.setenv("TEST_PORT_INVALIDO", "abc")

        with pytest.raises(ValueError):
            obter_variavel_env_int("TEST_PORT_INVALIDO")


class TestObterVariavelEnvBool:
    """Testes para a função obter_variavel_env_bool."""

    @pytest.mark.parametrize("valor", ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON"])
    def test_obter_bool_true(self, monkeypatch, valor):
        """Testa valores que devem retornar True."""
        monkeypatch.setenv("TEST_BOOL", valor)
        resultado = obter_variavel_env_bool("TEST_BOOL")
        assert resultado is True

    @pytest.mark.parametrize("valor", ["false", "False", "FALSE", "0", "no", "NO", "off", "OFF", "qualquer"])
    def test_obter_bool_false(self, monkeypatch, valor):
        """Testa valores que devem retornar False."""
        monkeypatch.setenv("TEST_BOOL", valor)
        resultado = obter_variavel_env_bool("TEST_BOOL")
        assert resultado is False

    def test_obter_bool_default_false(self, monkeypatch):
        """Testa que default é False quando variável não existe."""
        monkeypatch.delenv("TEST_BOOL_INEXISTENTE", raising=False)
        resultado = obter_variavel_env_bool("TEST_BOOL_INEXISTENTE")
        assert resultado is False

    def test_obter_bool_default_true(self, monkeypatch):
        """Testa que default True funciona."""
        monkeypatch.delenv("TEST_BOOL_INEXISTENTE", raising=False)
        resultado = obter_variavel_env_bool("TEST_BOOL_INEXISTENTE", default=True)
        assert resultado is True


class TestObterVariavelEnvLista:
    """Testes para a função obter_variavel_env_lista."""

    def test_obter_lista_virgula(self, monkeypatch):
        """Testa obtenção de lista separada por vírgula."""
        monkeypatch.setenv("TEST_EMAILS", "a@x.com, b@x.com, c@x.com")
        resultado = obter_variavel_env_lista("TEST_EMAILS")
        assert resultado == ["a@x.com", "b@x.com", "c@x.com"]

    def test_obter_lista_separador_custom(self, monkeypatch):
        """Testa obtenção de lista com separador customizado."""
        monkeypatch.setenv("TEST_HOSTS", "host1;host2;host3")
        resultado = obter_variavel_env_lista("TEST_HOSTS", separador=";")
        assert resultado == ["host1", "host2", "host3"]

    def test_obter_lista_com_default(self, monkeypatch):
        """Testa obtenção de lista com valor padrão."""
        monkeypatch.delenv("TEST_LISTA_INEXISTENTE", raising=False)
        resultado = obter_variavel_env_lista(
            "TEST_LISTA_INEXISTENTE",
            default=["default1", "default2"]
        )
        assert resultado == ["default1", "default2"]

    def test_obter_lista_inexistente_sem_default(self, monkeypatch):
        """Testa que VariavelAmbienteError é levantada para lista inexistente."""
        monkeypatch.delenv("TEST_LISTA_INEXISTENTE", raising=False)

        with pytest.raises(VariavelAmbienteError):
            obter_variavel_env_lista("TEST_LISTA_INEXISTENTE")

    def test_obter_lista_valores_vazios_ignorados(self, monkeypatch):
        """Testa que valores vazios são filtrados."""
        monkeypatch.setenv("TEST_LISTA", "a,,b,  ,c")
        resultado = obter_variavel_env_lista("TEST_LISTA")
        assert resultado == ["a", "b", "c"]

    def test_obter_lista_unico_elemento(self, monkeypatch):
        """Testa lista com único elemento."""
        monkeypatch.setenv("TEST_LISTA_UNICO", "unico")
        resultado = obter_variavel_env_lista("TEST_LISTA_UNICO")
        assert resultado == ["unico"]
