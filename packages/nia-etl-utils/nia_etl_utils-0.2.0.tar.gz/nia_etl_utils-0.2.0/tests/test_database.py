"""Testes para o módulo database."""

from unittest.mock import MagicMock, patch

import cx_Oracle
import psycopg2
import pytest

from nia_etl_utils.config import OracleConfig, PostgresConfig
from nia_etl_utils.database import (
    conectar_oracle,
    conectar_oracle_ouvidorias,
    conectar_postgresql,
    conectar_postgresql_nia,
    conectar_postgresql_opengeo,
    obter_engine_postgresql,
    obter_engine_postgresql_nia,
)
from nia_etl_utils.exceptions import ConexaoError
from nia_etl_utils.results import Conexao


class TestConectarPostgresql:
    """Testes para funções de conexão PostgreSQL."""

    @patch('nia_etl_utils.database.psycopg2.connect')
    def test_conectar_postgresql_sucesso(self, mock_connect):
        """Testa conexão PostgreSQL bem-sucedida."""
        # Mock da conexão
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Configuração explícita
        config = PostgresConfig(
            host='localhost',
            port='5432',
            database='testdb',
            user='user',
            password='pass'
        )

        resultado = conectar_postgresql(config)

        assert isinstance(resultado, Conexao)
        assert resultado.cursor == mock_cursor
        assert resultado.connection == mock_conn
        assert resultado.database == 'testdb'
        mock_connect.assert_called_once_with(
            host='localhost',
            port='5432',
            database='testdb',
            user='user',
            password='pass'
        )

    @patch('nia_etl_utils.database.psycopg2.connect')
    def test_conectar_postgresql_context_manager(self, mock_connect):
        """Testa que Conexao funciona como context manager."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        config = PostgresConfig(
            host='localhost',
            port='5432',
            database='testdb',
            user='user',
            password='pass'
        )

        with conectar_postgresql(config) as conn:
            assert conn.cursor == mock_cursor

        # Verifica que close foi chamado ao sair do context
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('nia_etl_utils.database.PostgresConfig.from_env')
    @patch('nia_etl_utils.database.psycopg2.connect')
    def test_conectar_postgresql_nia_wrapper(self, mock_connect, mock_from_env):
        """Testa wrapper conectar_postgresql_nia."""
        mock_from_env.return_value = PostgresConfig(
            host='localhost',
            port='5432',
            database='nia',
            user='user',
            password='pass'
        )

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        resultado = conectar_postgresql_nia()

        assert isinstance(resultado, Conexao)
        mock_from_env.assert_called_once_with()

    @patch('nia_etl_utils.database.PostgresConfig.from_env')
    @patch('nia_etl_utils.database.psycopg2.connect')
    def test_conectar_postgresql_opengeo_wrapper(self, mock_connect, mock_from_env):
        """Testa wrapper conectar_postgresql_opengeo."""
        mock_from_env.return_value = PostgresConfig(
            host='localhost',
            port='5432',
            database='opengeo',
            user='user',
            password='pass'
        )

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        resultado = conectar_postgresql_opengeo()

        assert isinstance(resultado, Conexao)
        mock_from_env.assert_called_once_with("_OPENGEO")

    @patch('nia_etl_utils.database.psycopg2.connect')
    def test_conectar_postgresql_erro_operacional(self, mock_connect):
        """Testa que erro operacional levanta ConexaoError."""
        mock_connect.side_effect = psycopg2.OperationalError("Erro de conexão")

        config = PostgresConfig(
            host='localhost',
            port='5432',
            database='testdb',
            user='user',
            password='pass'
        )

        with pytest.raises(ConexaoError) as exc_info:
            conectar_postgresql(config)

        assert "operacional" in str(exc_info.value).lower()
        assert exc_info.value.details["host"] == "localhost"

    @patch('nia_etl_utils.database.psycopg2.connect')
    def test_conectar_postgresql_erro_generico(self, mock_connect):
        """Testa que erro genérico do psycopg2 levanta ConexaoError."""
        mock_connect.side_effect = psycopg2.Error("Erro genérico")

        config = PostgresConfig(
            host='localhost',
            port='5432',
            database='testdb',
            user='user',
            password='pass'
        )

        with pytest.raises(ConexaoError):
            conectar_postgresql(config)


class TestConectarOracle:
    """Testes para funções de conexão Oracle."""

    @patch('nia_etl_utils.database.cx_Oracle.connect')
    def test_conectar_oracle_sucesso(self, mock_connect):
        """Testa conexão Oracle bem-sucedida."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        config = OracleConfig(
            host='localhost',
            port='1521',
            service_name='ORCL',
            user='user',
            password='pass'
        )

        resultado = conectar_oracle(config)

        assert isinstance(resultado, Conexao)
        assert resultado.cursor == mock_cursor
        assert resultado.connection == mock_conn
        assert resultado.database == 'ORCL'
        mock_connect.assert_called_once()

    @patch('nia_etl_utils.database.OracleConfig.from_env')
    @patch('nia_etl_utils.database.cx_Oracle.connect')
    def test_conectar_oracle_ouvidorias_wrapper(self, mock_connect, mock_from_env):
        """Testa wrapper conectar_oracle_ouvidorias."""
        mock_from_env.return_value = OracleConfig(
            host='localhost',
            port='1521',
            service_name='ORCL',
            user='user',
            password='pass'
        )

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        resultado = conectar_oracle_ouvidorias()

        assert isinstance(resultado, Conexao)
        mock_from_env.assert_called_once_with()

    @patch('nia_etl_utils.database.cx_Oracle.connect')
    def test_conectar_oracle_database_error(self, mock_connect):
        """Testa que DatabaseError levanta ConexaoError."""
        mock_connect.side_effect = cx_Oracle.DatabaseError("Erro de banco")

        config = OracleConfig(
            host='localhost',
            port='1521',
            service_name='ORCL',
            user='user',
            password='pass'
        )

        with pytest.raises(ConexaoError) as exc_info:
            conectar_oracle(config)

        assert "Oracle" in str(exc_info.value)

    @patch('nia_etl_utils.database.cx_Oracle.connect')
    def test_conectar_oracle_interface_error(self, mock_connect):
        """Testa que InterfaceError levanta ConexaoError."""
        mock_connect.side_effect = cx_Oracle.InterfaceError("Erro de interface")

        config = OracleConfig(
            host='localhost',
            port='1521',
            service_name='ORCL',
            user='user',
            password='pass'
        )

        with pytest.raises(ConexaoError) as exc_info:
            conectar_oracle(config)

        assert "interface" in str(exc_info.value).lower()


class TestObterEnginePostgresql:
    """Testes para funções de engine SQLAlchemy."""

    @patch('nia_etl_utils.database.create_engine')
    def test_obter_engine_postgresql_sucesso(self, mock_create_engine):
        """Testa criação de engine SQLAlchemy bem-sucedida."""
        mock_engine = MagicMock()
        mock_conn_context = MagicMock()
        mock_conn_context.__enter__ = MagicMock(return_value=MagicMock())
        mock_conn_context.__exit__ = MagicMock(return_value=False)
        mock_engine.connect.return_value = mock_conn_context
        mock_create_engine.return_value = mock_engine

        config = PostgresConfig(
            host='localhost',
            port='5432',
            database='testdb',
            user='user',
            password='pass'
        )

        engine = obter_engine_postgresql(config)

        assert engine == mock_engine
        mock_create_engine.assert_called_once_with(config.connection_string)

    @patch('nia_etl_utils.database.PostgresConfig.from_env')
    @patch('nia_etl_utils.database.create_engine')
    def test_obter_engine_postgresql_nia_wrapper(self, mock_create_engine, mock_from_env):
        """Testa wrapper obter_engine_postgresql_nia."""
        mock_from_env.return_value = PostgresConfig(
            host='localhost',
            port='5432',
            database='nia',
            user='user',
            password='pass'
        )

        mock_engine = MagicMock()
        mock_conn_context = MagicMock()
        mock_conn_context.__enter__ = MagicMock(return_value=MagicMock())
        mock_conn_context.__exit__ = MagicMock(return_value=False)
        mock_engine.connect.return_value = mock_conn_context
        mock_create_engine.return_value = mock_engine

        engine = obter_engine_postgresql_nia()

        assert engine is not None
        mock_from_env.assert_called_once_with()

    @patch('nia_etl_utils.database.create_engine')
    def test_obter_engine_postgresql_erro_conexao(self, mock_create_engine):
        """Testa que erro de conexão levanta ConexaoError."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = psycopg2.OperationalError("Erro")
        mock_create_engine.return_value = mock_engine

        config = PostgresConfig(
            host='localhost',
            port='5432',
            database='testdb',
            user='user',
            password='pass'
        )

        with pytest.raises(ConexaoError):
            obter_engine_postgresql(config)


class TestConexaoDataclass:
    """Testes para a dataclass Conexao."""

    def test_conexao_fechar_sucesso(self):
        """Testa fechamento de conexão bem-sucedido."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()

        conexao = Conexao(cursor=mock_cursor, connection=mock_conn, database='test')
        conexao.fechar()

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_conexao_fechar_cursor_none(self):
        """Testa fechamento quando cursor é None."""
        mock_conn = MagicMock()

        conexao = Conexao(cursor=None, connection=mock_conn, database='test')
        conexao.fechar()

        mock_conn.close.assert_called_once()

    def test_conexao_fechar_erro_nao_propaga(self):
        """Testa que erro ao fechar não propaga exceção."""
        mock_cursor = MagicMock()
        mock_cursor.close.side_effect = Exception("Erro ao fechar")
        mock_conn = MagicMock()

        conexao = Conexao(cursor=mock_cursor, connection=mock_conn, database='test')

        # Não deve lançar exceção
        conexao.fechar()

        # Se chegou aqui, não propagou exceção
        assert True

    def test_conexao_context_manager(self):
        """Testa uso como context manager."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()

        with Conexao(cursor=mock_cursor, connection=mock_conn, database='test') as conn:
            assert conn.cursor == mock_cursor

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()


class TestPostgresConfig:
    """Testes para a dataclass PostgresConfig."""

    def test_connection_string(self):
        """Testa geração da connection string."""
        config = PostgresConfig(
            host='localhost',
            port='5432',
            database='testdb',
            user='user',
            password='pass'
        )

        expected = "postgresql+psycopg2://user:pass@localhost:5432/testdb"
        assert config.connection_string == expected

    def test_repr_oculta_senha(self):
        """Testa que __repr__ não expõe a senha."""
        config = PostgresConfig(
            host='localhost',
            port='5432',
            database='testdb',
            user='user',
            password='senha_secreta'
        )

        repr_str = repr(config)
        assert 'senha_secreta' not in repr_str
        assert '***' in repr_str

    @patch('nia_etl_utils.env_config.obter_variavel_env')
    def test_from_env(self, mock_obter_env):
        """Testa criação via from_env."""
        mock_obter_env.side_effect = lambda x: {
            'DB_POSTGRESQL_HOST': 'localhost',
            'DB_POSTGRESQL_PORT': '5432',
            'DB_POSTGRESQL_DATABASE': 'testdb',
            'DB_POSTGRESQL_USER': 'user',
            'DB_POSTGRESQL_PASSWORD': 'pass'
        }[x]
        config = PostgresConfig.from_env()
        assert config.host == 'localhost'
        assert config.database == 'testdb'

    @patch('nia_etl_utils.env_config.obter_variavel_env')
    def test_from_env_com_sufixo(self, mock_obter_env):
        """Testa criação via from_env com sufixo."""
        mock_obter_env.side_effect = lambda x: {
            'DB_POSTGRESQL_HOST_OPENGEO': 'opengeo-host',
            'DB_POSTGRESQL_PORT_OPENGEO': '5433',
            'DB_POSTGRESQL_DATABASE_OPENGEO': 'opengeo',
            'DB_POSTGRESQL_USER_OPENGEO': 'geo_user',
            'DB_POSTGRESQL_PASSWORD_OPENGEO': 'geo_pass'
        }[x]
        config = PostgresConfig.from_env("_OPENGEO")
        assert config.host == 'opengeo-host'
        assert config.port == '5433'
        assert config.database == 'opengeo'
