"""Testes para o módulo limpeza_pastas."""

import pytest

from nia_etl_utils.exceptions import DiretorioError
from nia_etl_utils.limpeza_pastas import (
    criar_pasta_se_nao_existir,
    limpar_pasta,
    listar_arquivos,
    remover_pasta_recursivamente,
)


class TestLimparPasta:
    """Testes para a função limpar_pasta."""

    def test_criar_pasta_inexistente(self, tmp_path):
        """Testa criação de pasta quando ela não existe."""
        pasta_teste = tmp_path / "nova_pasta"

        removidos = limpar_pasta(str(pasta_teste), log=False)

        assert pasta_teste.exists()
        assert pasta_teste.is_dir()
        assert removidos == 0

    def test_limpar_pasta_com_arquivos(self, tmp_path):
        """Testa remoção de arquivos de pasta existente."""
        pasta_teste = tmp_path / "pasta_com_arquivos"
        pasta_teste.mkdir()

        # Cria alguns arquivos
        (pasta_teste / "arquivo1.txt").write_text("conteudo1")
        (pasta_teste / "arquivo2.csv").write_text("conteudo2")

        removidos = limpar_pasta(str(pasta_teste), log=False)

        # Pasta deve existir mas estar vazia
        assert pasta_teste.exists()
        assert len(list(pasta_teste.iterdir())) == 0
        assert removidos == 2

    def test_limpar_pasta_preserva_subdiretorios(self, tmp_path):
        """Testa que subdiretórios são preservados (só arquivos são removidos)."""
        pasta_teste = tmp_path / "pasta_principal"
        pasta_teste.mkdir()

        # Cria arquivo e subdiretório
        (pasta_teste / "arquivo.txt").write_text("conteudo")
        subdir = pasta_teste / "subpasta"
        subdir.mkdir()
        (subdir / "arquivo_sub.txt").write_text("sub_conteudo")

        removidos = limpar_pasta(str(pasta_teste), log=False)

        # Arquivo raiz deve ser removido, mas subdiretório preservado
        assert not (pasta_teste / "arquivo.txt").exists()
        assert subdir.exists()
        assert (subdir / "arquivo_sub.txt").exists()
        assert removidos == 1

    def test_limpar_pasta_vazia(self, tmp_path):
        """Testa limpar pasta que já está vazia."""
        pasta_teste = tmp_path / "pasta_vazia"
        pasta_teste.mkdir()

        removidos = limpar_pasta(str(pasta_teste), log=False)

        assert pasta_teste.exists()
        assert len(list(pasta_teste.iterdir())) == 0
        assert removidos == 0


class TestRemoverPastaRecursivamente:
    """Testes para a função remover_pasta_recursivamente."""

    def test_remover_pasta_com_conteudo(self, tmp_path):
        """Testa remoção recursiva de pasta com arquivos e subpastas."""
        pasta_teste = tmp_path / "pasta_completa"
        pasta_teste.mkdir()

        # Cria estrutura complexa
        (pasta_teste / "arquivo1.txt").write_text("conteudo1")
        subdir = pasta_teste / "subpasta"
        subdir.mkdir()
        (subdir / "arquivo2.txt").write_text("conteudo2")

        resultado = remover_pasta_recursivamente(str(pasta_teste), log=False)

        # Pasta e todo conteúdo devem ter sido removidos
        assert not pasta_teste.exists()
        assert resultado is True

    def test_remover_pasta_inexistente(self, tmp_path):
        """Testa remoção de pasta que não existe (retorna False)."""
        pasta_inexistente = tmp_path / "nao_existe"

        resultado = remover_pasta_recursivamente(str(pasta_inexistente), log=False)

        assert not pasta_inexistente.exists()
        assert resultado is False

    def test_remover_pasta_vazia(self, tmp_path):
        """Testa remoção de pasta vazia."""
        pasta_teste = tmp_path / "pasta_vazia"
        pasta_teste.mkdir()

        resultado = remover_pasta_recursivamente(str(pasta_teste), log=False)

        assert not pasta_teste.exists()
        assert resultado is True

    def test_remover_arquivo_levanta_erro(self, tmp_path):
        """Testa que tentar remover arquivo (não diretório) levanta DiretorioError."""
        arquivo = tmp_path / "arquivo.txt"
        arquivo.write_text("conteudo")

        with pytest.raises(DiretorioError) as exc_info:
            remover_pasta_recursivamente(str(arquivo), log=False)

        assert "não é um diretório" in str(exc_info.value)


class TestCriarPastaSeNaoExistir:
    """Testes para a função criar_pasta_se_nao_existir."""

    def test_criar_pasta_simples(self, tmp_path):
        """Testa criação de pasta simples."""
        pasta_teste = tmp_path / "nova_pasta"

        criada = criar_pasta_se_nao_existir(str(pasta_teste), log=False)

        assert pasta_teste.exists()
        assert pasta_teste.is_dir()
        assert criada is True

    def test_criar_pasta_com_pais(self, tmp_path):
        """Testa criação de pasta com diretórios pai inexistentes."""
        pasta_teste = tmp_path / "nivel1" / "nivel2" / "nivel3"

        criada = criar_pasta_se_nao_existir(str(pasta_teste), log=False)

        assert pasta_teste.exists()
        assert pasta_teste.is_dir()
        assert criada is True

    def test_criar_pasta_ja_existente(self, tmp_path):
        """Testa criar pasta que já existe (retorna False)."""
        pasta_teste = tmp_path / "pasta_existente"
        pasta_teste.mkdir()

        criada = criar_pasta_se_nao_existir(str(pasta_teste), log=False)

        assert pasta_teste.exists()
        assert criada is False


class TestListarArquivos:
    """Testes para a função listar_arquivos."""

    def test_listar_todos_arquivos(self, tmp_path):
        """Testa listagem de todos os arquivos."""
        (tmp_path / "arquivo1.txt").write_text("1")
        (tmp_path / "arquivo2.csv").write_text("2")
        (tmp_path / "arquivo3.json").write_text("3")

        arquivos = listar_arquivos(str(tmp_path))

        assert len(arquivos) == 3

    def test_listar_por_extensao(self, tmp_path):
        """Testa filtro por extensão."""
        (tmp_path / "arquivo1.txt").write_text("1")
        (tmp_path / "arquivo2.txt").write_text("2")
        (tmp_path / "arquivo3.csv").write_text("3")

        arquivos = listar_arquivos(str(tmp_path), extensao=".txt")

        assert len(arquivos) == 2
        assert all(a.suffix == ".txt" for a in arquivos)

    def test_listar_recursivo(self, tmp_path):
        """Testa listagem recursiva."""
        (tmp_path / "arquivo1.txt").write_text("1")
        subdir = tmp_path / "subpasta"
        subdir.mkdir()
        (subdir / "arquivo2.txt").write_text("2")

        # Sem recursão
        arquivos_sem = listar_arquivos(str(tmp_path), recursivo=False)
        assert len(arquivos_sem) == 1

        # Com recursão
        arquivos_com = listar_arquivos(str(tmp_path), recursivo=True)
        assert len(arquivos_com) == 2

    def test_listar_pasta_vazia(self, tmp_path):
        """Testa listagem de pasta vazia."""
        pasta_vazia = tmp_path / "vazia"
        pasta_vazia.mkdir()

        arquivos = listar_arquivos(str(pasta_vazia))

        assert arquivos == []

    def test_listar_pasta_inexistente(self, tmp_path):
        """Testa que pasta inexistente levanta DiretorioError."""
        pasta_inexistente = tmp_path / "nao_existe"

        with pytest.raises(DiretorioError) as exc_info:
            listar_arquivos(str(pasta_inexistente))

        assert "não existe" in str(exc_info.value)

    def test_listar_arquivo_levanta_erro(self, tmp_path):
        """Testa que passar arquivo em vez de pasta levanta DiretorioError."""
        arquivo = tmp_path / "arquivo.txt"
        arquivo.write_text("conteudo")

        with pytest.raises(DiretorioError) as exc_info:
            listar_arquivos(str(arquivo))

        assert "não é um diretório" in str(exc_info.value)

    def test_listar_ordenado(self, tmp_path):
        """Testa que arquivos são retornados ordenados."""
        (tmp_path / "c_arquivo.txt").write_text("c")
        (tmp_path / "a_arquivo.txt").write_text("a")
        (tmp_path / "b_arquivo.txt").write_text("b")

        arquivos = listar_arquivos(str(tmp_path))

        nomes = [a.name for a in arquivos]
        assert nomes == sorted(nomes)
