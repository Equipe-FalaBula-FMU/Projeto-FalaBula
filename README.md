# FalaBula — Assistente de consulta a bulas (RAG)

**[Acessar o FalaBula online](https://projeto-falabula-dashshp2g9tj3fr9jop2yv.streamlit.app/)**

Projeto acadêmico de chatbot que responde a perguntas em português sobre **medicamentos documentados nas bulas cadastradas**, utilizando recuperação de informações (RAG). A aplicação foi preparada para receber documentos de outras áreas terapêuticas, sem depender de uma doença específica.

> **Atenção:** conteúdo informativo, não é diagnóstico, prescrição nem orientação de tratamento individual. Não inicie, altere ou interrompa medicamentos com base nas respostas. Consulte profissional habilitado.

## Versão 2.3 — fontes e PDFs (27/11/2026)

A seção **Fontes consultadas** agrupa páginas recuperadas por documento, mostra o nome amigável e permite abrir o PDF completo cadastrado no GitHub. Os links são gerados pelo módulo `fontes.py` a partir dos caminhos relativos dos arquivos. A seção fica recolhida por padrão. A versão no GitHub pode não corresponder à revisão mais recente do fabricante; confira a origem e a validade da bula. O link pressupõe que o arquivo esteja publicado na branch `main` do repositório oficial.

## Versão 2.2 — consultas gerais (26/11/2026)

A aplicação recupera documentos também para perguntas sobre doenças e temas de saúde sem exigir o nome de um medicamento. Prioriza fontes gerais cadastradas e, na ausência delas, pode consultar bulas, explicitando quando a cobertura é insuficiente. Perguntas específicas continuam restritas à bula identificada; pedidos de prescrição não são atendidos.

### Organização da base

- `documentos/` ou `documentos/bulas/`: bulas de medicamentos.
- `documentos/doencas/`: documentos oficiais sobre doenças.
- `documentos/protocolos_clinicos/`: protocolos e diretrizes.
- `documentos/orientacoes_oficiais/`: materiais oficiais de orientação.

As subpastas são reconhecidas automaticamente quando contêm PDFs. Não é necessário mover as bulas existentes. Para uma classificação completa dos tipos de diabetes, cadastre uma fonte oficial que descreva essa classificação; a presença de bulas não garante cobertura suficiente. Consulte o [Ministério da Saúde](https://www.gov.br/saude/pt-br) para obter documentos. A inclusão de PDFs não requer novo treinamento.

## Links úteis

- [Guia de estudo e desenho da arquitetura](docs/ARQUITETURA_E_GUIA_DE_ESTUDO.md)

- [Aplicação online — Streamlit](https://projeto-falabula-dashshp2g9tj3fr9jop2yv.streamlit.app/)
- [Pasta de bulas no GitHub](https://github.com/Equipe-FalaBula-FMU/Projeto-FalaBula/tree/main/documentos)
- [Enviar novos PDFs diretamente ao GitHub](https://github.com/Equipe-FalaBula-FMU/Projeto-FalaBula/upload/main/documentos)
- [Pasta compartilhada no Google Drive](https://drive.google.com/drive/folders/1pw05qc4SeUuLskEq6FS0q0vY1_n5jcBM)

## Situação da base documental

- A base inicial recebeu **12 PDFs da equipe** na [pasta compartilhada no Google Drive](https://drive.google.com/drive/folders/1pw05qc4SeUuLskEq6FS0q0vY1_n5jcBM).
- Nesta etapa, os documentos são predominantemente relacionados a **diabetes e condições associadas**. A arquitetura é genérica, mas **a cobertura de outras enfermidades dependerá do cadastro de novas bulas**.
- A origem regulatória, atualização, laboratório e validade de cada PDF devem ser conferidos pela equipe antes de considerá-lo uma fonte oficial atualizada. A existência do arquivo no Drive não constitui essa validação.
- Os arquivos antigos `Base_Unica_Diabetes_Posologia_Mapeada.pdf` e `GuiaDiabetes.pdf` permanecem na raiz como legado; **a nova interface `frontend.py` consulta somente a pasta `documentos/`**.

## Adicionar, substituir ou retirar bulas

### Inclusão pelo navegador (sem alterar o código)

Abra o [upload de documentos](https://github.com/Equipe-FalaBula-FMU/Projeto-FalaBula/upload/main/documentos), selecione os PDFs, informe uma mensagem de commit e confirme na branch `main` (ou abra um pull request se houver proteção da branch). É necessário ter permissão de escrita. Após a implantação, confira a quantidade de bulas e a lista de documentos no menu lateral do Streamlit e teste uma pergunta com o nome exato do medicamento.

Para novos medicamentos, use nomes como `bula_NomeMedicamento.pdf` (extensão `.pdf` minúscula). O código reconhece documentos novos pelo nome do arquivo; sinônimos, marcas alternativas e princípios ativos não presentes no nome podem exigir atualização do catálogo `CATALOGO` em `falabula_core.py`. Um PDF inválido ou sem texto extraível pode impedir a consulta à base até sua correção ou retirada.

### Procedimento geral

1. Obter o PDF de fonte confiável, preferencialmente no [Bulário Eletrônico da Anvisa](https://consultas.anvisa.gov.br/#/bulario/), conferindo o medicamento, apresentação, fabricante e data da revisão.
2. Colocar o PDF na pasta `documentos/`, mantendo um nome de arquivo identificável. O arquivo deve possuir texto selecionável: PDFs de imagem sem texto exigem preparação anterior.
3. Para execução local, salvar o arquivo nessa pasta e atualizar a página; o cache de leitura é atualizado **na próxima consulta** quando for detectada inclusão, alteração ou remoção de arquivos.
4. Para a versão online do Streamlit, enviar o PDF ao diretório `documentos/` na branch `main` do GitHub. O Streamlit deve implantar a atualização; depois da implantação, a próxima consulta atualiza a leitura da base. **Editar apenas o Google Drive não atualiza automaticamente o GitHub nem a aplicação.**
5. Testar consultas sobre indicações, contraindicações, efeitos adversos e ausência de informação. Evitar documentos duplicados, versões conflitantes ou não verificadas.

A atualização é uma **nova leitura e organização das páginas dos PDFs**, não o treinamento ou ajuste dos pesos do modelo de linguagem. A primeira consulta após mudanças pode ser mais lenta e usar recursos de memória; muitos PDFs grandes podem exceder os limites de hospedagem gratuita.

## Como executar no computador

Requisitos: Python 3.10+ e acesso à Groq.

```bash
git clone https://github.com/Equipe-FalaBula-FMU/Projeto-FalaBula.git
cd Projeto-FalaBula
python -m venv .venv
# Windows: .venv\Scripts\python.exe -m pip install -r requirements.txt
# macOS/Linux: .venv/bin/python -m pip install -r requirements.txt
python -m pip install -r requirements.txt
```

Crie um arquivo local `.env` com a chave:

```env
GROQ_API_KEY=COLE_SUA_CHAVE_AQUI
```

Execute:

```bash
python -m streamlit run frontend.py
```

A aplicação abre normalmente em http://localhost:8501. Para execução online, configure `GROQ_API_KEY` no campo privado **Secrets** da aplicação Streamlit, nunca no GitHub. Em implantações com escopo de segredos do Streamlit, a variável precisa estar disponível ao processo.

## Arquitetura

**[Arquitetura técnica e guia de estudo para apresentação](docs/ARQUITETURA_E_GUIA_DE_ESTUDO.md)** — diagrama Mermaid, tecnologias de frontend e backend, fluxo RAG, infraestrutura, limitações e roteiro de apresentação.


1. **Frontend** — `frontend.py` e `style.css`, com tela de acesso demonstrativa (sem autenticação) e chat responsivo.
2. **Documentos** — PDFs em `documentos/`, listados automaticamente.
3. **Leitura e indexação leve** — `falabula_core.py` extrai o texto dos PDFs com `pypdf`, sem carregar modelos de embeddings ou banco vetorial pesado na memória.
4. **Consulta** — catálogo determinístico para listagens; para perguntas específicas, primeiro identifica a bula pelos nomes e aliases cadastrados ou pelo nome do arquivo novo, depois recupera as páginas pertinentes exclusivamente desse PDF e usa a API Groq (`openai/gpt-oss-120b`).
5. **Rastreabilidade** — as respostas com trechos recuperados apresentam, em uma seção expansível, os documentos agrupados, páginas recuperadas e links para os PDFs completos. Essa lista é uma trilha de recuperação, não uma garantia automática de correção de cada afirmação.
6. **Atualização da base** — assinatura baseada em nome, tamanho e data de modificação dos PDFs para invalidar o índice em cache quando os documentos mudam.

O arquivo `app.py` é agora um **ponto de entrada compatível com Streamlit Cloud** e carrega a mesma interface de `frontend.py`. A versão original de `app.py` permanece na branch de backup. **Ambos os comandos de execução iniciam a mesma aplicação.**

## Perguntas de validação inicial

- Quais os tipos de diabetes? (Recupera documentos relevantes; informa limitações se não houver classificação completa.)
- O que é uma doença ausente da base? (Informa falta de evidências.)

- Para que serve o Mounjaro, segundo a bula?
- Quais contraindicações constam na bula do Glifage?
- Que cuidados a bula do Lantus informa?
- Quais reações adversas constam na bula do Januvia?
- O FalaBula possui informações documentadas sobre um medicamento que ainda não está na pasta?
- Uma bula prova que o medicamento está disponível no Farmácia Popular? (Resposta esperada: **não**; exige fonte oficial específica e atualizada.)

**Observação:** a resposta de IA pode conter erros. Confira sempre o conteúdo integral da bula e seus dados de referência; não use a aplicação para decisões clínicas.

## Organização do repositório

```text
Projeto-FalaBula/
├── documentos/       # PDFs indexados automaticamente pelo frontend
├── fontes.py         # agrupamento de referências e links de PDFs
├── falabula_core.py  # catálogo, identificação e recuperação de documentos
├── frontend.py       # interface atual, genérica
├── style.css         # estilos responsivos
├── requirements.txt  # dependências
├── app.py            # entrada Streamlit Cloud que executa frontend.py
├── GuiaDiabetes.pdf  # legado
├── Base_Unica_Diabetes_Posologia_Mapeada.pdf  # legado
└── README.md
```

## Histórico e preservação

Backup anterior à versão 2.2: [backup/antes-consulta-geral-2026-11-26](https://github.com/Equipe-FalaBula-FMU/Projeto-FalaBula/tree/backup/antes-consulta-geral-2026-11-26).

A versão anterior do repositório oficial está preservada na branch [`backup/antes-correcao-equipe-2026-11-26`](https://github.com/Equipe-FalaBula-FMU/Projeto-FalaBula/tree/backup/antes-correcao-equipe-2026-11-26).

## Responsabilidade

Este é um protótipo acadêmico. As respostas são limitadas aos documentos presentes na pasta `documentos/`. Informações sobre disponibilidade no SUS, Farmácia Popular, preços, estoque e elegibilidade devem ser verificadas em fontes governamentais atuais, não deduzidas de bulas.


## Diagnóstico e testes de regressão

A interface informa a versão 2.3, de 27/11/2026, e a quantidade de PDFs no menu lateral. O comportamento esperado:

- **"Quais medicamentos estão cadastrados?"**: lista apenas os PDFs classificados como bulas, sem gerar a relação por IA.
- **"Para que serve o Mounjaro?"**: seleciona exclusivamente o PDF do Mounjaro; não utiliza excertos de insulina ou metformina.
- **"Quais são os efeitos adversos da dapagliflozina?"**: consulta somente o PDF da dapagliflozina.
- **"Quais medicamentos há para pressão alta?"**: caso não haja bula e medicamento específico, solicita identificação ou informa limitação; não inventa lista.
- **"Explique a posologia"** sem medicamento identificado: solicita o nome do produto, sem prescrever.

Executar testes automatizados de funções puras com `python -m unittest discover -s tests -v`. A API Groq e a disponibilidade da implantação no Streamlit Cloud devem ser validadas separadamente, pois dependem do ambiente externo.
