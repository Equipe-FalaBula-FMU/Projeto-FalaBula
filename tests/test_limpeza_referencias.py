import unittest
from falabula_core import limpar_referencias_tecnicas

class TestLimpezaReferencias(unittest.TestCase):
    def test_marcador_pagina(self):
        self.assertEqual(
            limpar_referencias_tecnicas("Diabetes mellitus tipo 1 autoimune (DM1A)【PÁGINA: 1】."),
            "Diabetes mellitus tipo 1 autoimune (DM1A)."
        )

    def test_multiplas_paginas(self):
        self.assertEqual(limpar_referencias_tecnicas("DM2 [PÁGINAS: 2, 3 e 5]."), "DM2.")

    def test_documento_pagina(self):
        self.assertEqual(
            limpar_referencias_tecnicas("Diabetes gestacional【DOCUMENTO: guia.pdf | PÁGINA: 4】."),
            "Diabetes gestacional."
        )

    def test_preserva_conteudo_clinico(self):
        texto = "DM1A, DM1B e DM2.\n\nGlicemia: 126 mg/dL. [informação complementar]"
        self.assertEqual(limpar_referencias_tecnicas(texto), texto)

if __name__ == "__main__":
    unittest.main()
