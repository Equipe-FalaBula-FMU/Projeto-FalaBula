import unittest
from fontes import agrupar_fontes

class TestFontes(unittest.TestCase):
    def test_agrupamento(self):
        g = agrupar_fontes(["bula_Mounjaro.pdf — página 5", "bula_Mounjaro.pdf — página 1", "bula_Mounjaro.pdf — página 1"])
        self.assertEqual(len(g), 1)
        self.assertEqual(g[0]["paginas"], [1, 5])
        self.assertEqual(g[0]["titulo"], "Mounjaro")
        self.assertTrue(g[0]["url"].endswith("/documentos/bula_Mounjaro.pdf"))

    def test_subpasta_e_espacos(self):
        g = agrupar_fontes(["doencas/Guia diabetes.pdf — página 2"])
        self.assertEqual(g[0]["tipo"], "Documento")
        self.assertTrue(g[0]["url"].endswith("/doencas/Guia%20diabetes.pdf"))

    def test_referencias_invalidas(self):
        self.assertEqual(agrupar_fontes(["../segredo.pdf — página 1", "x.pdf — página 0", "texto"]), [])

if __name__ == "__main__":
    unittest.main()
