"""Testes para o módulo processa_csv."""

from pathlib import Path

import pandas as pd
import pytest

from nia_etl_utils.exceptions import ExtracaoError, ExtracaoVaziaError, ValidacaoError
from nia_etl_utils.processa_csv import (
    exportar_multiplos_csv,
    exportar_para_csv,
    extrair_e_exportar_csv,
)
from nia_etl_utils.results import ResultadoExtracao, ResultadoLote


class TestExportarParaCsv:
    """Testes para a função exportar_para_csv."""

    def test_exportar_dataframe_simples(self, tmp_path):
        """Testa exportação básica de DataFrame."""
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"]
        })

        caminho = exportar_para_csv(
            df=df,
            nome_arquivo="teste",
            data_extracao="2025_01_19",
            diretorio_base=str(tmp_path)
        )

        # Verifica que arquivo foi criado
        assert Path(caminho).exists()
        assert caminho == str(tmp_path / "teste_2025_01_19.csv")

        # Verifica conteúdo
        df_lido = pd.read_csv(caminho)
        pd.testing.assert_frame_equal(df, df_lido)

    def test_exportar_cria_diretorio(self, tmp_path):
        """Testa que diretório é criado se não existir."""
        diretorio_inexistente = tmp_path / "novo_dir" / "subdir"
        df = pd.DataFrame({"col": [1, 2]})

        caminho = exportar_para_csv(
            df=df,
            nome_arquivo="teste",
            data_extracao="2025_01_19",
            diretorio_base=str(diretorio_inexistente)
        )

        assert Path(caminho).exists()
        assert diretorio_inexistente.exists()

    def test_exportar_dataframe_vazio_levanta_erro(self, tmp_path):
        """Testa que DataFrame vazio levanta ExtracaoVaziaError."""
        df = pd.DataFrame()

        with pytest.raises(ExtracaoVaziaError) as exc_info:
            exportar_para_csv(
                df=df,
                nome_arquivo="vazio",
                data_extracao="2025_01_19",
                diretorio_base=str(tmp_path)
            )

        assert exc_info.value.nome_extracao == "vazio"

    def test_exportar_dataframe_none_levanta_erro(self, tmp_path):
        """Testa que DataFrame None levanta ExtracaoVaziaError."""
        with pytest.raises(ExtracaoVaziaError):
            exportar_para_csv(
                df=None, # type: ignore
                nome_arquivo="none",
                data_extracao="2025_01_19",
                diretorio_base=str(tmp_path)
            )

    def test_exportar_nome_arquivo_vazio(self, tmp_path):
        """Testa que nome vazio levanta ValidacaoError."""
        df = pd.DataFrame({"col": [1, 2]})

        with pytest.raises(ValidacaoError) as exc_info:
            exportar_para_csv(
                df=df,
                nome_arquivo="",
                data_extracao="2025_01_19",
                diretorio_base=str(tmp_path)
            )

        assert "nome" in str(exc_info.value).lower()
        assert exc_info.value.details["parametro"] == "nome_arquivo"

    def test_exportar_nome_arquivo_espacos(self, tmp_path):
        """Testa que nome com apenas espaços levanta ValidacaoError."""
        df = pd.DataFrame({"col": [1, 2]})

        with pytest.raises(ValidacaoError):
            exportar_para_csv(
                df=df,
                nome_arquivo="   ",
                data_extracao="2025_01_19",
                diretorio_base=str(tmp_path)
            )

    def test_exportar_com_caracteres_especiais(self, tmp_path):
        """Testa exportação com caracteres especiais no DataFrame."""
        df = pd.DataFrame({
            "nome": ["José", "María", "François"],
            "valor": [100.50, 200.75, 300.25]
        })

        caminho = exportar_para_csv(
            df=df,
            nome_arquivo="especiais",
            data_extracao="2025_01_19",
            diretorio_base=str(tmp_path)
        )

        # Verifica que arquivo foi criado e pode ser lido
        df_lido = pd.read_csv(caminho)
        pd.testing.assert_frame_equal(df, df_lido)


class TestExtrairEExportarCsv:
    """Testes para a função extrair_e_exportar_csv."""

    def test_extrair_e_exportar_sucesso(self, tmp_path):
        """Testa extração e exportação bem-sucedida."""
        def funcao_extracao():
            return pd.DataFrame({"col": [1, 2, 3]})

        resultado = extrair_e_exportar_csv(
            nome_extracao="dados",
            funcao_extracao=funcao_extracao,
            data_extracao="2025_01_19",
            diretorio_base=str(tmp_path)
        )

        assert isinstance(resultado, ResultadoExtracao)
        assert resultado.sucesso is True
        assert resultado.nome == "dados"
        assert resultado.linhas == 3
        assert resultado.colunas == 1
        assert resultado.caminho is not None
        assert Path(resultado.caminho).exists()

    def test_extrair_retorna_vazio_levanta_erro(self, tmp_path):
        """Testa que DataFrame vazio levanta ExtracaoVaziaError."""
        def funcao_extracao_vazia():
            return pd.DataFrame()

        with pytest.raises(ExtracaoVaziaError) as exc_info:
            extrair_e_exportar_csv(
                nome_extracao="vazio",
                funcao_extracao=funcao_extracao_vazia,
                data_extracao="2025_01_19",
                diretorio_base=str(tmp_path)
            )

        assert exc_info.value.nome_extracao == "vazio"

    def test_extrair_com_erro_na_funcao(self, tmp_path):
        """Testa que erro na função de extração levanta ExtracaoError."""
        def funcao_com_erro():
            raise ValueError("Erro proposital")

        with pytest.raises(ExtracaoError) as exc_info:
            extrair_e_exportar_csv(
                nome_extracao="com_erro",
                funcao_extracao=funcao_com_erro,
                data_extracao="2025_01_19",
                diretorio_base=str(tmp_path)
            )

        assert "com_erro" in str(exc_info.value)
        assert exc_info.value.details["extracao"] == "com_erro"

    def test_extrair_resultado_contem_metricas(self, tmp_path):
        """Testa que resultado contém métricas do arquivo."""
        def funcao_extracao():
            return pd.DataFrame({
                "col1": [1, 2, 3, 4, 5],
                "col2": ["a", "b", "c", "d", "e"],
                "col3": [1.1, 2.2, 3.3, 4.4, 5.5]
            })

        resultado = extrair_e_exportar_csv(
            nome_extracao="metricas",
            funcao_extracao=funcao_extracao,
            data_extracao="2025_01_19",
            diretorio_base=str(tmp_path)
        )

        assert resultado.linhas == 5
        assert resultado.colunas == 3
        assert resultado.tamanho_bytes is not None
        assert resultado.tamanho_bytes > 0
        assert resultado.tamanho_kb is not None
        assert resultado.tamanho_kb > 0


class TestExportarMultiplosCsv:
    """Testes para a função exportar_multiplos_csv."""

    def test_exportar_multiplas_extractions(self, tmp_path):
        """Testa exportação de múltiplas extrações."""
        def extrair1():
            return pd.DataFrame({"a": [1, 2]})

        def extrair2():
            return pd.DataFrame({"b": [3, 4]})

        extractions = [
            {"nome": "dados1", "funcao": extrair1},
            {"nome": "dados2", "funcao": extrair2}
        ]

        lote = exportar_multiplos_csv(
            extractions=extractions,
            data_extracao="2025_01_19",
            diretorio_base=str(tmp_path)
        )

        assert isinstance(lote, ResultadoLote)
        assert lote.total == 2
        assert lote.sucesso == 2
        assert lote.falhas == 0
        assert lote.todos_sucesso is True
        assert lote.taxa_sucesso == 1.0

        # Verifica resultados individuais
        assert len(lote.resultados) == 2
        assert all(r.sucesso for r in lote.resultados)
        assert all(Path(r.caminho).exists() for r in lote.resultados) # type: ignore

    def test_exportar_multiplas_com_vazio_ignorando(self, tmp_path):
        """Testa exportação com extração vazia quando ignorar_vazios=True."""
        def extrair_ok():
            return pd.DataFrame({"a": [1, 2]})

        def extrair_vazio():
            return pd.DataFrame()

        extractions = [
            {"nome": "dados_ok", "funcao": extrair_ok},
            {"nome": "dados_vazio", "funcao": extrair_vazio}
        ]

        lote = exportar_multiplos_csv(
            extractions=extractions,
            data_extracao="2025_01_19",
            diretorio_base=str(tmp_path),
            ignorar_vazios=True
        )

        assert lote.total == 2
        assert lote.sucesso == 1
        assert lote.falhas == 1
        assert lote.todos_sucesso is False
        assert lote.taxa_sucesso == 0.5

        # Verifica resultados
        sucesso = lote.extracoes_sucesso
        falhas = lote.extracoes_falhas

        assert len(sucesso) == 1
        assert sucesso[0].nome == "dados_ok"

        assert len(falhas) == 1
        assert falhas[0].nome == "dados_vazio"
        assert falhas[0].erro is not None

    def test_exportar_multiplas_com_vazio_falhando(self, tmp_path):
        """Testa exportação com extração vazia quando ignorar_vazios=False."""
        def extrair_ok():
            return pd.DataFrame({"a": [1, 2]})

        def extrair_vazio():
            return pd.DataFrame()

        extractions = [
            {"nome": "dados_ok", "funcao": extrair_ok},
            {"nome": "dados_vazio", "funcao": extrair_vazio}
        ]

        with pytest.raises(ExtracaoVaziaError) as exc_info:
            exportar_multiplos_csv(
                extractions=extractions,
                data_extracao="2025_01_19",
                diretorio_base=str(tmp_path),
                ignorar_vazios=False
            )

        assert exc_info.value.nome_extracao == "dados_vazio"

    def test_exportar_multiplas_todas_vazias(self, tmp_path):
        """Testa exportação quando todas extrações são vazias."""
        def extrair_vazio1():
            return pd.DataFrame()

        def extrair_vazio2():
            return pd.DataFrame()

        extractions = [
            {"nome": "vazio1", "funcao": extrair_vazio1},
            {"nome": "vazio2", "funcao": extrair_vazio2}
        ]

        lote = exportar_multiplos_csv(
            extractions=extractions,
            data_extracao="2025_01_19",
            diretorio_base=str(tmp_path),
            ignorar_vazios=True
        )

        assert lote.total == 2
        assert lote.sucesso == 0
        assert lote.falhas == 2
        assert lote.todos_sucesso is False
        assert lote.taxa_sucesso == 0.0

    def test_exportar_multiplas_total_linhas(self, tmp_path):
        """Testa que total_linhas soma todas as extrações."""
        def extrair1():
            return pd.DataFrame({"a": list(range(10))})

        def extrair2():
            return pd.DataFrame({"b": list(range(20))})

        def extrair3():
            return pd.DataFrame({"c": list(range(30))})

        extractions = [
            {"nome": "dados1", "funcao": extrair1},
            {"nome": "dados2", "funcao": extrair2},
            {"nome": "dados3", "funcao": extrair3}
        ]

        lote = exportar_multiplos_csv(
            extractions=extractions,
            data_extracao="2025_01_19",
            diretorio_base=str(tmp_path)
        )

        assert lote.total_linhas == 60  # 10 + 20 + 30

    def test_exportar_lista_vazia(self, tmp_path):
        """Testa exportação com lista vazia de extrações."""
        lote = exportar_multiplos_csv(
            extractions=[],
            data_extracao="2025_01_19",
            diretorio_base=str(tmp_path)
        )

        assert lote.total == 0
        assert lote.sucesso == 0
        assert lote.falhas == 0
        assert lote.todos_sucesso is True  # vacuamente verdadeiro
        assert lote.taxa_sucesso == 0.0
