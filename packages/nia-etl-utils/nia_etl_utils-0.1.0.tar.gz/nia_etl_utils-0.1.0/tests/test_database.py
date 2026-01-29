"""Testes para o módulo database."""
from unittest.mock import patch, MagicMock
import pytest
import psycopg2
import cx_Oracle

from nia_etl_utils.database import (
    conectar_postgresql,
    conectar_postgresql_nia,
    conectar_postgresql_opengeo,
    conectar_oracle,
    conectar_oracle_ouvidorias,
    fechar_conexao,
    obter_engine_postgresql,
    obter_engine_postgresql_nia
)


class TestConectarPostgresql:
    """Testes para funções de conexão PostgreSQL."""

    @patch('nia_etl_utils.database.psycopg2.connect')
    @patch('nia_etl_utils.database.obter_variavel_env')
    def test_conectar_postgresql_sucesso(self, mock_obter_env, mock_connect):
        """Testa conexão PostgreSQL bem-sucedida."""
        # Mock das variáveis de ambiente
        mock_obter_env.side_effect = lambda x: {
            'DB_POSTGRESQL_HOST': 'localhost',
            'DB_POSTGRESQL_PORT': '5432',
            'DB_POSTGRESQL_DATABASE': 'testdb',
            'DB_POSTGRESQL_USER': 'user',
            'DB_POSTGRESQL_PASSWORD': 'pass'
        }[x]

        # Mock da conexão
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        cursor, conn = conectar_postgresql("")

        assert cursor == mock_cursor
        assert conn == mock_conn
        mock_connect.assert_called_once()

    @patch('nia_etl_utils.database.psycopg2.connect')
    @patch('nia_etl_utils.database.obter_variavel_env')
    def test_conectar_postgresql_nia_wrapper(self, mock_obter_env, mock_connect):
        """Testa wrapper conectar_postgresql_nia."""
        mock_obter_env.side_effect = lambda x: {
            'DB_POSTGRESQL_HOST': 'localhost',
            'DB_POSTGRESQL_PORT': '5432',
            'DB_POSTGRESQL_DATABASE': 'nia',
            'DB_POSTGRESQL_USER': 'user',
            'DB_POSTGRESQL_PASSWORD': 'pass'
        }[x]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        cursor, conn = conectar_postgresql_nia()

        assert cursor is not None
        assert conn is not None

    @patch('nia_etl_utils.database.psycopg2.connect')
    @patch('nia_etl_utils.database.obter_variavel_env')
    def test_conectar_postgresql_opengeo_wrapper(self, mock_obter_env, mock_connect):
        """Testa wrapper conectar_postgresql_opengeo."""
        mock_obter_env.side_effect = lambda x: {
            'DB_POSTGRESQL_HOST_OPENGEO': 'localhost',
            'DB_POSTGRESQL_PORT_OPENGEO': '5432',
            'DB_POSTGRESQL_DATABASE_OPENGEO': 'opengeo',
            'DB_POSTGRESQL_USER_OPENGEO': 'user',
            'DB_POSTGRESQL_PASSWORD_OPENGEO': 'pass'
        }[x]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        cursor, conn = conectar_postgresql_opengeo()

        assert cursor is not None
        assert conn is not None

    @patch('nia_etl_utils.database.psycopg2.connect')
    @patch('nia_etl_utils.database.obter_variavel_env')
    def test_conectar_postgresql_erro_operacional(self, mock_obter_env, mock_connect):
        """Testa que erro operacional causa sys.exit(1)."""
        mock_obter_env.side_effect = lambda x: {
            'DB_POSTGRESQL_HOST': 'localhost',
            'DB_POSTGRESQL_PORT': '5432',
            'DB_POSTGRESQL_DATABASE': 'testdb',
            'DB_POSTGRESQL_USER': 'user',
            'DB_POSTGRESQL_PASSWORD': 'pass'
        }[x]

        # Mock que lança erro operacional
        mock_connect.side_effect = psycopg2.OperationalError("Erro de conexão")

        with pytest.raises(SystemExit) as exc_info:
            conectar_postgresql("")

        assert exc_info.value.code == 1


class TestConectarOracle:
    """Testes para funções de conexão Oracle."""

    @patch('nia_etl_utils.database.cx_Oracle.connect')
    @patch('nia_etl_utils.database.cx_Oracle.makedsn')
    @patch('nia_etl_utils.database.obter_variavel_env')
    def test_conectar_oracle_sucesso(self, mock_obter_env, mock_makedsn, mock_connect):
        """Testa conexão Oracle bem-sucedida."""
        # Mock das variáveis de ambiente
        mock_obter_env.side_effect = lambda x: {
            'DB_ORACLE_HOST': 'localhost',
            'DB_ORACLE_PORT': '1521',
            'DB_ORACLE_SERVICE_NAME': 'ORCL',
            'DB_ORACLE_USER': 'user',
            'DB_ORACLE_PASSWORD': 'pass'
        }[x]

        # Mock do DSN
        mock_makedsn.return_value = "mock_dsn"

        # Mock da conexão
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        cursor, conn = conectar_oracle()

        assert cursor == mock_cursor
        assert conn == mock_conn
        mock_makedsn.assert_called_once()
        mock_connect.assert_called_once()

    @patch('nia_etl_utils.database.cx_Oracle.connect')
    @patch('nia_etl_utils.database.cx_Oracle.makedsn')
    @patch('nia_etl_utils.database.obter_variavel_env')
    def test_conectar_oracle_ouvidorias_wrapper(self, mock_obter_env, mock_makedsn, mock_connect):
        """Testa wrapper conectar_oracle_ouvidorias."""
        mock_obter_env.side_effect = lambda x: {
            'DB_ORACLE_HOST': 'localhost',
            'DB_ORACLE_PORT': '1521',
            'DB_ORACLE_SERVICE_NAME': 'ORCL',
            'DB_ORACLE_USER': 'user',
            'DB_ORACLE_PASSWORD': 'pass'
        }[x]

        mock_makedsn.return_value = "mock_dsn"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        cursor, conn = conectar_oracle_ouvidorias()

        assert cursor is not None
        assert conn is not None

    @patch('nia_etl_utils.database.cx_Oracle.connect')
    @patch('nia_etl_utils.database.cx_Oracle.makedsn')
    @patch('nia_etl_utils.database.obter_variavel_env')
    def test_conectar_oracle_database_error(self, mock_obter_env, mock_makedsn, mock_connect):
        """Testa que DatabaseError causa sys.exit(1)."""
        mock_obter_env.side_effect = lambda x: {
            'DB_ORACLE_HOST': 'localhost',
            'DB_ORACLE_PORT': '1521',
            'DB_ORACLE_SERVICE_NAME': 'ORCL',
            'DB_ORACLE_USER': 'user',
            'DB_ORACLE_PASSWORD': 'pass'
        }[x]

        mock_makedsn.return_value = "mock_dsn"
        mock_connect.side_effect = cx_Oracle.DatabaseError("Erro de banco")

        with pytest.raises(SystemExit) as exc_info:
            conectar_oracle()

        assert exc_info.value.code == 1


class TestObterEnginePostgresql:
    """Testes para funções de engine SQLAlchemy."""

    @patch('nia_etl_utils.database.create_engine')
    @patch('nia_etl_utils.database.obter_variavel_env')
    def test_obter_engine_postgresql_sucesso(self, mock_obter_env, mock_create_engine):
        """Testa criação de engine SQLAlchemy bem-sucedida."""
        mock_obter_env.side_effect = lambda x: {
            'DB_POSTGRESQL_HOST': 'localhost',
            'DB_POSTGRESQL_PORT': '5432',
            'DB_POSTGRESQL_DATABASE': 'testdb',
            'DB_POSTGRESQL_USER': 'user',
            'DB_POSTGRESQL_PASSWORD': 'pass'
        }[x]

        # Mock da engine
        mock_engine = MagicMock()
        mock_conn_context = MagicMock()
        mock_conn_context.__enter__ = MagicMock(return_value=MagicMock())
        mock_conn_context.__exit__ = MagicMock(return_value=False)
        mock_engine.connect.return_value = mock_conn_context
        mock_create_engine.return_value = mock_engine

        engine = obter_engine_postgresql("")

        assert engine == mock_engine
        mock_create_engine.assert_called_once()

    @patch('nia_etl_utils.database.create_engine')
    @patch('nia_etl_utils.database.obter_variavel_env')
    def test_obter_engine_postgresql_nia_wrapper(self, mock_obter_env, mock_create_engine):
        """Testa wrapper obter_engine_postgresql_nia."""
        mock_obter_env.side_effect = lambda x: {
            'DB_POSTGRESQL_HOST': 'localhost',
            'DB_POSTGRESQL_PORT': '5432',
            'DB_POSTGRESQL_DATABASE': 'nia',
            'DB_POSTGRESQL_USER': 'user',
            'DB_POSTGRESQL_PASSWORD': 'pass'
        }[x]

        mock_engine = MagicMock()
        mock_conn_context = MagicMock()
        mock_conn_context.__enter__ = MagicMock(return_value=MagicMock())
        mock_conn_context.__exit__ = MagicMock(return_value=False)
        mock_engine.connect.return_value = mock_conn_context
        mock_create_engine.return_value = mock_engine

        engine = obter_engine_postgresql_nia()

        assert engine is not None


class TestFecharConexao:
    """Testes para a função fechar_conexao."""

    def test_fechar_conexao_sucesso(self):
        """Testa fechamento de conexão bem-sucedido."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()

        # Não deve lançar exceção
        fechar_conexao(mock_cursor, mock_conn)

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_fechar_conexao_cursor_none(self):
        """Testa fechamento quando cursor é None."""
        mock_conn = MagicMock()

        # Não deve lançar exceção
        fechar_conexao(None, mock_conn)

        mock_conn.close.assert_called_once()

    def test_fechar_conexao_erro_nao_falha(self):
        """Testa que erro ao fechar não causa sys.exit (apenas warning)."""
        mock_cursor = MagicMock()
        mock_cursor.close.side_effect = Exception("Erro ao fechar")
        mock_conn = MagicMock()

        # Não deve lançar SystemExit, apenas warning
        fechar_conexao(mock_cursor, mock_conn)

        # Se chegou aqui, não deu sys.exit(1)
        assert True
