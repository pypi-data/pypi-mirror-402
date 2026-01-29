"""Testes para o módulo limpeza_pastas."""

from nia_etl_utils.limpeza_pastas import (
    limpar_pasta,
    remover_pasta_recursivamente,
    criar_pasta_se_nao_existir
)


class TestLimparPasta:
    """Testes para a função limpar_pasta."""

    def test_criar_pasta_inexistente(self, tmp_path):
        """Testa criação de pasta quando ela não existe."""
        pasta_teste = tmp_path / "nova_pasta"

        limpar_pasta(str(pasta_teste), log=False)

        assert pasta_teste.exists()
        assert pasta_teste.is_dir()

    def test_limpar_pasta_com_arquivos(self, tmp_path):
        """Testa remoção de arquivos de pasta existente."""
        pasta_teste = tmp_path / "pasta_com_arquivos"
        pasta_teste.mkdir()

        # Cria alguns arquivos
        (pasta_teste / "arquivo1.txt").write_text("conteudo1")
        (pasta_teste / "arquivo2.csv").write_text("conteudo2")

        limpar_pasta(str(pasta_teste), log=False)

        # Pasta deve existir mas estar vazia
        assert pasta_teste.exists()
        assert len(list(pasta_teste.iterdir())) == 0

    def test_limpar_pasta_preserva_subdiretorios(self, tmp_path):
        """Testa que subdiretórios são preservados (só arquivos são removidos)."""
        pasta_teste = tmp_path / "pasta_principal"
        pasta_teste.mkdir()

        # Cria arquivo e subdiretório
        (pasta_teste / "arquivo.txt").write_text("conteudo")
        subdir = pasta_teste / "subpasta"
        subdir.mkdir()
        (subdir / "arquivo_sub.txt").write_text("sub_conteudo")

        limpar_pasta(str(pasta_teste), log=False)

        # Arquivo raiz deve ser removido, mas subdiretório preservado
        assert not (pasta_teste / "arquivo.txt").exists()
        assert subdir.exists()
        assert (subdir / "arquivo_sub.txt").exists()

    def test_limpar_pasta_vazia(self, tmp_path):
        """Testa limpar pasta que já está vazia."""
        pasta_teste = tmp_path / "pasta_vazia"
        pasta_teste.mkdir()

        limpar_pasta(str(pasta_teste), log=False)

        assert pasta_teste.exists()
        assert len(list(pasta_teste.iterdir())) == 0


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

        remover_pasta_recursivamente(str(pasta_teste), log=False)

        # Pasta e todo conteúdo devem ter sido removidos
        assert not pasta_teste.exists()

    def test_remover_pasta_inexistente(self, tmp_path):
        """Testa remoção de pasta que não existe (não deve dar erro)."""
        pasta_inexistente = tmp_path / "nao_existe"

        # Não deve lançar exceção
        remover_pasta_recursivamente(str(pasta_inexistente), log=False)

        assert not pasta_inexistente.exists()

    def test_remover_pasta_vazia(self, tmp_path):
        """Testa remoção de pasta vazia."""
        pasta_teste = tmp_path / "pasta_vazia"
        pasta_teste.mkdir()

        remover_pasta_recursivamente(str(pasta_teste), log=False)

        assert not pasta_teste.exists()


class TestCriarPastaSeNaoExistir:
    """Testes para a função criar_pasta_se_nao_existir."""

    def test_criar_pasta_simples(self, tmp_path):
        """Testa criação de pasta simples."""
        pasta_teste = tmp_path / "nova_pasta"

        criar_pasta_se_nao_existir(str(pasta_teste), log=False)

        assert pasta_teste.exists()
        assert pasta_teste.is_dir()

    def test_criar_pasta_com_pais(self, tmp_path):
        """Testa criação de pasta com diretórios pai inexistentes."""
        pasta_teste = tmp_path / "nivel1" / "nivel2" / "nivel3"

        criar_pasta_se_nao_existir(str(pasta_teste), log=False)

        assert pasta_teste.exists()
        assert pasta_teste.is_dir()

    def test_criar_pasta_ja_existente(self, tmp_path):
        """Testa criar pasta que já existe (não deve dar erro)."""
        pasta_teste = tmp_path / "pasta_existente"
        pasta_teste.mkdir()

        # Não deve lançar exceção
        criar_pasta_se_nao_existir(str(pasta_teste), log=False)

        assert pasta_teste.exists()
