"""Testes para o módulo processa_csv."""
from pathlib import Path
import pytest
import pandas as pd

from nia_etl_utils.processa_csv import (
    exportar_para_csv,
    extrair_e_exportar_csv,
    exportar_multiplos_csv
)


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

    def test_exportar_dataframe_vazio(self, tmp_path):
        """Testa exportação de DataFrame vazio."""
        df = pd.DataFrame()

        caminho = exportar_para_csv(
            df=df,
            nome_arquivo="vazio",
            data_extracao="2025_01_19",
            diretorio_base=str(tmp_path)
        )

        # Retorna string vazia quando DataFrame é vazio
        assert caminho == ""

    def test_exportar_nome_arquivo_vazio(self, tmp_path):
        """Testa que nome vazio causa sys.exit(1)."""
        df = pd.DataFrame({"col": [1, 2]})

        with pytest.raises(SystemExit) as exc_info:
            exportar_para_csv(
                df=df,
                nome_arquivo="",
                data_extracao="2025_01_19",
                diretorio_base=str(tmp_path)
            )

        assert exc_info.value.code == 1

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

        caminho = extrair_e_exportar_csv(
            nome_extracao="dados",
            funcao_extracao=funcao_extracao,
            data_extracao="2025_01_19",
            diretorio_base=str(tmp_path)
        )

        assert caminho is not None
        assert Path(caminho).exists()

    def test_extrair_retorna_vazio_sem_falhar(self, tmp_path):
        """Testa que DataFrame vazio retorna None sem falhar."""
        def funcao_extracao_vazia():
            return pd.DataFrame()

        caminho = extrair_e_exportar_csv(
            nome_extracao="vazio",
            funcao_extracao=funcao_extracao_vazia,
            data_extracao="2025_01_19",
            diretorio_base=str(tmp_path),
            falhar_se_vazio=False
        )

        assert caminho is None

    def test_extrair_retorna_vazio_com_falha(self, tmp_path):
        """Testa que DataFrame vazio causa sys.exit(1) quando falhar_se_vazio=True."""
        def funcao_extracao_vazia():
            return pd.DataFrame()

        with pytest.raises(SystemExit) as exc_info:
            extrair_e_exportar_csv(
                nome_extracao="vazio",
                funcao_extracao=funcao_extracao_vazia,
                data_extracao="2025_01_19",
                diretorio_base=str(tmp_path),
                falhar_se_vazio=True
            )

        assert exc_info.value.code == 1

    def test_extrair_com_erro_na_funcao(self, tmp_path):
        """Testa que erro na função de extração causa sys.exit(1)."""
        def funcao_com_erro():
            raise ValueError("Erro proposital")

        with pytest.raises(SystemExit) as exc_info:
            extrair_e_exportar_csv(
                nome_extracao="com_erro",
                funcao_extracao=funcao_com_erro,
                data_extracao="2025_01_19",
                diretorio_base=str(tmp_path)
            )

        assert exc_info.value.code == 1


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

        resultados = exportar_multiplos_csv(
            extractions=extractions,
            data_extracao="2025_01_19",
            diretorio_base=str(tmp_path)
        )

        assert len(resultados) == 2
        assert resultados["dados1"] is not None
        assert resultados["dados2"] is not None
        assert Path(resultados["dados1"]).exists()
        assert Path(resultados["dados2"]).exists()

    def test_exportar_multiplas_com_vazio(self, tmp_path):
        """Testa exportação com uma extração vazia."""
        def extrair_ok():
            return pd.DataFrame({"a": [1, 2]})

        def extrair_vazio():
            return pd.DataFrame()

        extractions = [
            {"nome": "dados_ok", "funcao": extrair_ok},
            {"nome": "dados_vazio", "funcao": extrair_vazio}
        ]

        resultados = exportar_multiplos_csv(
            extractions=extractions,
            data_extracao="2025_01_19",
            diretorio_base=str(tmp_path),
            falhar_se_vazio=False
        )

        assert resultados["dados_ok"] is not None
        assert resultados["dados_vazio"] is None
