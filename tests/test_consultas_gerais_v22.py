import unittest
from pathlib import Path
from falabula_core import pergunta_catalogo, identificar_documentos, responder_pergunta, resposta_catalogo, chave_documento

class ConsultasGerais(unittest.TestCase):
    def setUp(self):
        self.m = Path("documentos/bula_Mounjaro.pdf")
        self.g = Path("documentos/bula_glifage.pdf")
        self.d = Path("documentos/doencas/diabetes.pdf")
        self.arquivos = [self.m, self.g, self.d]
        self.base = {chave_documento(self.m): [(1, "Diabetes tipo 2")], chave_documento(self.g): [(1, "Metformina")], chave_documento(self.d): [(1, "Classificação de diabetes tipo 1 e tipo 2")]}

    def test_catalogo(self):
        self.assertTrue(pergunta_catalogo("Quais medicamentos estão cadastrados?"))
        self.assertFalse(pergunta_catalogo("Quais contraindicações constam na bula do Glifage?"))
        self.assertNotIn("diabetes.pdf", resposta_catalogo(self.arquivos))

    def test_geral_prioriza_fonte(self):
        _, fontes = responder_pergunta("Quais os tipos de diabetes?", self.arquivos, self.base, "")
        self.assertTrue(fontes)
        self.assertTrue(fontes[0].startswith("doencas/diabetes.pdf"))

    def test_medicamento_isolado(self):
        self.assertEqual(identificar_documentos("Para que serve Monjaro?", self.arquivos), [self.m])
        _, fontes = responder_pergunta("Quais contraindicações constam na bula do Glifage?", self.arquivos, self.base, "")
        self.assertTrue(fontes)
        self.assertTrue(all(f.startswith(self.g.name) for f in fontes))

    def test_sem_evidencia(self):
        resposta, fontes = responder_pergunta("O que é malária?", self.arquivos, self.base, "")
        self.assertFalse(fontes)
        self.assertIn("Não encontrei", resposta)

    def test_sem_prescricao(self):
        _, fontes = responder_pergunta("Qual medicamento devo tomar?", self.arquivos, self.base, "")
        self.assertFalse(fontes)

if __name__ == "__main__":
    unittest.main()
