"""Testes para o módulo processa_csv_paralelo."""
import pytest
import pandas as pd

from nia_etl_utils.processa_csv_paralelo import (
    calcular_chunksize,
    processar_csv_paralelo
)


# =============================================================================
# FUNÇÕES HELPER PARA TESTES (devem estar no nível do módulo para pickling)
# =============================================================================

def _limpar_texto(texto):
    """Remove espaços e converte para maiúsculas."""
    if pd.isna(texto):
        return texto
    return str(texto).strip().upper()


def _identidade(x):
    """Retorna valor sem modificação."""
    return x


# =============================================================================
# TESTES
# =============================================================================


class TestCalcularChunksize:
    """Testes para a função calcular_chunksize."""

    def test_arquivo_pequeno_menor_500mb(self, tmp_path):
        """Testa chunksize para arquivo < 500MB."""
        arquivo = tmp_path / "pequeno.csv"
        arquivo.write_text("a" * 1000)

        chunksize = calcular_chunksize(str(arquivo))

        assert chunksize == 10000

    def test_calculo_baseado_em_tamanho_real(self, tmp_path):
        """Testa que função calcula baseado no tamanho real do arquivo."""
        arquivo = tmp_path / "teste.csv"
        conteudo = "coluna1,coluna2\n" * 10000
        arquivo.write_text(conteudo)

        chunksize = calcular_chunksize(str(arquivo))

        assert chunksize in [1000, 2000, 5000, 10000]


class TestProcessarCsvParalelo:
    """Testes para a função processar_csv_paralelo."""

    def test_processamento_basico(self, tmp_path):
        """Testa processamento básico de CSV."""
        entrada = tmp_path / "entrada.csv"
        df_entrada = pd.DataFrame({
            "nome": ["  João  ", "  Maria  ", "  Pedro  "],
            "idade": [25, 30, 35]
        })
        df_entrada.to_csv(entrada, index=False)

        saida = tmp_path / "saida.csv"
        processar_csv_paralelo(
            caminho_entrada=str(entrada),
            caminho_saida=str(saida),
            colunas_para_tratar=["nome"],
            funcao_transformacao=_limpar_texto,
            chunksize=2
        )

        df_saida = pd.read_csv(saida)
        assert df_saida["nome"].tolist() == ["JOÃO", "MARIA", "PEDRO"]
        assert df_saida["idade"].tolist() == [25, 30, 35]

    def test_normalizacao_colunas(self, tmp_path):
        """Testa normalização de nomes de colunas para lowercase."""
        entrada = tmp_path / "entrada.csv"
        df_entrada = pd.DataFrame({
            "NOME": ["João", "Maria"],
            "IDADE": [25, 30]
        })
        df_entrada.to_csv(entrada, index=False)

        saida = tmp_path / "saida.csv"
        processar_csv_paralelo(
            caminho_entrada=str(entrada),
            caminho_saida=str(saida),
            colunas_para_tratar=["NOME"],
            funcao_transformacao=_identidade,
            normalizar_colunas=True
        )

        df_saida = pd.read_csv(saida)
        assert "nome" in df_saida.columns
        assert "idade" in df_saida.columns

    def test_sem_normalizacao_colunas(self, tmp_path):
        """Testa que normalização pode ser desabilitada."""
        entrada = tmp_path / "entrada.csv"
        df_entrada = pd.DataFrame({
            "NOME": ["João", "Maria"],
            "IDADE": [25, 30]
        })
        df_entrada.to_csv(entrada, index=False)

        saida = tmp_path / "saida.csv"
        processar_csv_paralelo(
            caminho_entrada=str(entrada),
            caminho_saida=str(saida),
            colunas_para_tratar=["NOME"],
            funcao_transformacao=_identidade,
            normalizar_colunas=False
        )

        df_saida = pd.read_csv(saida)
        assert "NOME" in df_saida.columns
        assert "IDADE" in df_saida.columns

    def test_multiplas_colunas(self, tmp_path):
        """Testa transformação em múltiplas colunas."""
        entrada = tmp_path / "entrada.csv"
        df_entrada = pd.DataFrame({
            "nome": ["  joão  ", "  maria  "],
            "cidade": ["  rio  ", "  sp  "],
            "idade": [25, 30]
        })
        df_entrada.to_csv(entrada, index=False)

        saida = tmp_path / "saida.csv"
        processar_csv_paralelo(
            caminho_entrada=str(entrada),
            caminho_saida=str(saida),
            colunas_para_tratar=["nome", "cidade"],
            funcao_transformacao=_limpar_texto
        )

        df_saida = pd.read_csv(saida)
        assert df_saida["nome"].tolist() == ["JOÃO", "MARIA"]
        assert df_saida["cidade"].tolist() == ["RIO", "SP"]
        assert df_saida["idade"].tolist() == [25, 30]

    def test_arquivo_entrada_inexistente(self, tmp_path):
        """Testa que arquivo inexistente causa sys.exit(1)."""
        entrada = tmp_path / "nao_existe.csv"
        saida = tmp_path / "saida.csv"

        with pytest.raises(SystemExit) as exc_info:
            processar_csv_paralelo(
                caminho_entrada=str(entrada),
                caminho_saida=str(saida),
                colunas_para_tratar=["coluna"],
                funcao_transformacao=_identidade
            )

        assert exc_info.value.code == 1

    def test_remover_entrada(self, tmp_path):
        """Testa remoção do arquivo de entrada após processamento."""
        entrada = tmp_path / "entrada.csv"
        df_entrada = pd.DataFrame({"col": [1, 2, 3]})
        df_entrada.to_csv(entrada, index=False)

        saida = tmp_path / "saida.csv"
        processar_csv_paralelo(
            caminho_entrada=str(entrada),
            caminho_saida=str(saida),
            colunas_para_tratar=["col"],
            funcao_transformacao=_identidade,
            remover_entrada=True
        )

        assert not entrada.exists()
        assert saida.exists()

    def test_nao_remover_entrada_por_padrao(self, tmp_path):
        """Testa que arquivo de entrada não é removido por padrão."""
        entrada = tmp_path / "entrada.csv"
        df_entrada = pd.DataFrame({"col": [1, 2, 3]})
        df_entrada.to_csv(entrada, index=False)

        saida = tmp_path / "saida.csv"
        processar_csv_paralelo(
            caminho_entrada=str(entrada),
            caminho_saida=str(saida),
            colunas_para_tratar=["col"],
            funcao_transformacao=_identidade
        )

        assert entrada.exists()
        assert saida.exists()

    def test_chunksize_customizado(self, tmp_path):
        """Testa uso de chunksize customizado."""
        entrada = tmp_path / "entrada.csv"
        df_entrada = pd.DataFrame({
            "col": list(range(100))
        })
        df_entrada.to_csv(entrada, index=False)

        saida = tmp_path / "saida.csv"
        processar_csv_paralelo(
            caminho_entrada=str(entrada),
            caminho_saida=str(saida),
            colunas_para_tratar=["col"],
            funcao_transformacao=_identidade,
            chunksize=10
        )

        df_saida = pd.read_csv(saida)
        assert len(df_saida) == 100

    def test_coluna_inexistente_warning(self, tmp_path):
        """Testa que coluna inexistente gera warning mas não falha."""
        entrada = tmp_path / "entrada.csv"
        df_entrada = pd.DataFrame({
            "nome": ["João", "Maria"],
            "idade": [25, 30]
        })
        df_entrada.to_csv(entrada, index=False)

        saida = tmp_path / "saida.csv"
        processar_csv_paralelo(
            caminho_entrada=str(entrada),
            caminho_saida=str(saida),
            colunas_para_tratar=["coluna_inexistente"],
            funcao_transformacao=_identidade
        )

        assert saida.exists()

    def test_processamento_com_multiplos_chunks(self, tmp_path):
        """Testa processamento com múltiplos chunks."""
        entrada = tmp_path / "entrada.csv"
        df_entrada = pd.DataFrame({
            "texto": [f"  linha {i}  " for i in range(50)],
            "numero": list(range(50))
        })
        df_entrada.to_csv(entrada, index=False)

        saida = tmp_path / "saida.csv"
        processar_csv_paralelo(
            caminho_entrada=str(entrada),
            caminho_saida=str(saida),
            colunas_para_tratar=["texto"],
            funcao_transformacao=_limpar_texto,
            chunksize=10
        )

        df_saida = pd.read_csv(saida)
        assert len(df_saida) == 50
        assert all("LINHA" in texto for texto in df_saida["texto"])

    def test_num_processos_customizado(self, tmp_path):
        """Testa uso de número customizado de processos."""
        entrada = tmp_path / "entrada.csv"
        df_entrada = pd.DataFrame({
            "col": list(range(20))
        })
        df_entrada.to_csv(entrada, index=False)

        saida = tmp_path / "saida.csv"
        processar_csv_paralelo(
            caminho_entrada=str(entrada),
            caminho_saida=str(saida),
            colunas_para_tratar=["col"],
            funcao_transformacao=_identidade,
            num_processos=2
        )

        df_saida = pd.read_csv(saida)
        assert len(df_saida) == 20
