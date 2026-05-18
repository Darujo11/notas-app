# 📊 Analisador de Notas Fiscais — README

> **Versão:** 2.0.0  
> **Tecnologia:** Python · Streamlit · pandas · pdfplumber · fpdf2  
> **Deploy:** Docker + Traefik → `notas.autozapx.com`

---

## 1. O que é este projeto?

Uma aplicação web construída com **Streamlit** que permite ao usuário fazer upload de um relatório de **Notas Fiscais de Serviço Eletrônicas (NFS-e)** em formato **PDF** ou **CSV**, e automaticamente:

1. **Extrai** os dados relevantes (nº da nota, tomador, CNPJ, valores, ISS, alíquota, data de emissão).
2. **Limpa e normaliza** os dados (converte moeda, padroniza nomes de colunas).
3. **Agrupa por CNPJ** — quando o mesmo tomador de serviço aparece em múltiplas notas, soma os valores.
4. **Exibe KPIs** (total de notas, valor total faturado, quantidade de tomadores únicos, total de ISS).
5. **Permite filtrar** por tomador de serviço.
6. **Gera relatórios** exportáveis em **TXT** e **PDF**.

---

## 2. Estrutura de Arquivos

```
analista-dados/
├── app.py                  ← Código principal (toda a lógica e interface)
├── requirements.txt        ← Dependências Python
├── Dockerfile              ← Imagem Docker para produção
├── docker-compose.yml      ← Orquestração Docker + labels Traefik
├── .gitignore              ← Arquivos ignorados pelo Git
├── SKILL.md                ← Definição da skill do projeto
├── p.csv                   ← Planilha de exemplo (NFS-e exportada)
├── EMPRESA X 2021.pdf      ← PDF de exemplo (relatório de notas)
└── read/
    ├── readme.md           ← Este arquivo
    ├── csv_upload_implementation.md
    └── implementation_plan.md
```

---

## 3. Dependências (`requirements.txt`)

| Pacote | Função |
|--------|--------|
| `streamlit` | Framework web para a interface do usuário |
| `pandas` | Manipulação e análise dos DataFrames |
| `pdfplumber` | Extração de tabelas a partir de PDFs |
| `openpyxl` | Suporte do pandas para exportação Excel |
| `fpdf2` | Geração de relatórios em PDF |

---

## 4. Como Rodar

### Localmente (desenvolvimento)

```bash
# Instalar dependências
python -m pip install -r requirements.txt

# Iniciar o app
python -m streamlit run app.py
```

Acesse: **http://localhost:8501**

### Via Docker (produção)

```bash
docker compose build
docker compose up -d
```

Acesse: **https://notas.autozapx.com** (requer Traefik + DNS configurado)

---

## 5. Fluxo Completo do Programa

```
┌─────────────────────────────────────────────────────────────────────┐
│  USUÁRIO                                                            │
│  ┌──────────────┐                                                   │
│  │ Upload       │  Arrasta um arquivo .pdf ou .csv                  │
│  │ (PDF ou CSV) │                                                   │
│  └──────┬───────┘                                                   │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ DETECÇÃO DE TIPO                                         │       │
│  │ ▸ .pdf  → process_pdf()    (pdfplumber)                  │       │
│  │ ▸ .csv  → load_csv()       (pandas + encoding fallback)  │       │
│  └──────┬───────────────────────────────────────────────────┘       │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ NORMALIZAÇÃO — prepare_dataframe()                       │       │
│  │                                                          │       │
│  │ ▸ Detecta se é CSV ou PDF                                │       │
│  │ ▸ Mapeia colunas para nomes canônicos                    │       │
│  │ ▸ Converte valores monetários (BRL → float)              │       │
│  │ ▸ Extrai CNPJ (do campo separado ou do campo Tomador)    │       │
│  │ ▸ Limpa número da nota                                   │       │
│  └──────┬───────────────────────────────────────────────────┘       │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ INTERFACE (Streamlit)                                    │       │
│  │                                                          │       │
│  │ ▸ 4 KPIs: Notas / Valor Total / Tomadores / ISS Total   │       │
│  │ ▸ Tabela agrupada por Tomador + CNPJ (com somas)        │       │
│  │ ▸ Filtro por Tomador (selectbox)                         │       │
│  │ ▸ Expander com dados detalhados                          │       │
│  │ ▸ Download: Relatório TXT e PDF                          │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Detalhamento das Funções

### 6.1 `load_csv(file_obj)` — Linhas 10–25

**Objetivo:** Ler um arquivo CSV com tratamento robusto de encoding e separador.

**Lógica:**
- Tenta 4 combinações: `(utf-8, ;)` → `(utf-8, ,)` → `(latin1, ;)` → `(latin1, ,)`
- Se o resultado tiver apenas 1 coluna, significa que o separador está errado → tenta o próximo.
- **Fallback final:** `latin1` + `;` (padrão de CSVs brasileiros exportados do sistema NFS-e).

**Por que é necessário:**
- CSVs gerados por sistemas brasileiros quase sempre usam `;` como separador e `latin1` ou `ISO-8859-1` como encoding (devido a acentos como ã, ç, ô).

---

### 6.2 `clean_currency(x)` — Linhas 30–42

**Objetivo:** Converter valores monetários do formato brasileiro (string) para `float`.

**Exemplos:**
| Entrada | Saída |
|---------|-------|
| `"R$ 16.852,96"` | `16852.96` |
| `"248.838,42"` | `248838.42` |
| `"0,00"` | `0.0` |
| `1000` (int) | `1000.0` |

**Lógica:**
1. Remove `R$`
2. Remove `.` (ponto de milhar)
3. Troca `,` por `.` (separador decimal)
4. Converte para `float`

---

### 6.3 `process_pdf(file_bytes)` — Linhas 44–96

**Objetivo:** Extrair a tabela de notas fiscais de um PDF multi-páginas.

**Lógica:**
1. Abre o PDF com `pdfplumber`.
2. Itera página por página com barra de progresso.
3. Usa `page.extract_tables()` para extrair tabelas.
4. **Detecta o cabeçalho** na primeira página (procura "Nota" + "Tomador").
5. **Ignora cabeçalhos repetidos** em páginas seguintes.
6. **Identifica linhas de dados** (primeira coluna tem números → nota nova).
7. **Trata continuação de linhas** (quando o texto de uma célula quebra para a próxima linha da tabela → concatena com a anterior).
8. Retorna um DataFrame com todas as notas.

**Cache:** Decorada com `@st.cache_data` para não reprocessar o mesmo PDF em reruns do Streamlit.

---

### 6.4 `prepare_dataframe(df)` — Linhas 98–180

**Objetivo:** Normalizar o DataFrame bruto (de PDF ou CSV) para um formato canônico.

**Detecta o tipo de arquivo** pela presença da coluna `CPF/CNPJ/NIF do Tomador`.

#### Caminho CSV (sistema NFS-e)

Mapeia **7 colunas específicas** por pattern matching parcial:

| Coluna original no CSV | Coluna canônica |
|---|---|
| `Nº da Nota Fiscal Eletrônica` | **Nota** |
| `Data Hora da Emissão da Nota Fiscal` | **Emissão** |
| `CPF/CNPJ/NIF do Tomador` | **CNPJ** |
| `Razão Social do Tomador` | **Tomador de Serviços** |
| `Alíquota` | **Alíquota** |
| `Valor dos Serviços` | **Valor da Nota** |
| `Valor do ISS` | **Valor ISS** |

- **Seleciona apenas essas colunas** (descarta as 70+ restantes).
- Aplica `clean_currency` nos campos de valor.
- Extrai apenas dígitos do número da nota.

#### Caminho PDF

- Usa fuzzy matching nos nomes das colunas extraídas do PDF.
- Extrai CNPJ do campo "Tomador de Serviços" via regex (`XX.XXX.XXX/XXXX-XX`).
- Remove o CNPJ do nome do tomador após extração.

---

### 6.5 `format_brl(value)` — Linhas 182–184

**Objetivo:** Formatar um `float` como moeda brasileira.

| Entrada | Saída |
|---------|-------|
| `16852.96` | `R$ 16.852,96` |
| `1000000.00` | `R$ 1.000.000,00` |

---

### 6.6 `generate_text_report(df)` — Linhas 186–229

**Objetivo:** Gerar um relatório em texto plano agrupado por Tomador + CNPJ.

**Estrutura do relatório:**
```
============================================================
Tomador de Serviço: TRIDENT ENERGY DO BRASIL LTDA
CNPJ: 33.639.843/0005-15
Qtd. Notas: 5
Valor Total: R$ 500.000,00
ISS Total: R$ 10.000,00
Notas fiscais correspondentes:
  1. NFS-e nº 3968
  2. NFS-e nº 3969
  ...
------------------------------------------------------------
```

---

### 6.7 `generate_pdf_report(df)` — Linhas 231–279

**Objetivo:** Gerar um relatório em PDF com a mesma estrutura do TXT.

**Usa fpdf2** (classe `FPDF`) com:
- Fonte Helvetica (tamanhos 9 e 10)
- Bold para nome do tomador
- Itálico para rótulo "Notas fiscais"
- Totais (Valor Total e ISS Total) por grupo

---

### 6.8 Interface Streamlit — Linhas 282–429

#### Upload (linhas 290–309)
- Aceita `.pdf` e `.csv`.
- Detecta o tipo pelo MIME type ou extensão do arquivo.
- Botão "Nova Análise" reseta o uploader.

#### KPIs (linhas 321–336)
4 métricas em colunas:

| KPI | Cálculo |
|-----|---------|
| Total de Notas | `len(df)` |
| Valor Total Faturado | `df['Valor da Nota'].sum()` |
| Qtd. Tomadores Únicos | `df['Tomador de Serviços'].nunique()` |
| Total ISS | `df['Valor ISS'].sum()` |

#### Visão Agrupada (linhas 339–396)
- **Selectbox** para filtrar por tomador.
- **Agrupamento** por `['Tomador de Serviços', 'CNPJ']`.
- Colunas calculadas: `Qtd_Notas`, `Valor_Total`, `ISS_Total`.
- Quando o mesmo CNPJ tem múltiplas notas, **soma** os valores.
- **Expander** com a lista detalhada de todas as notas.

#### Exportação (linhas 398–425)
- Dois botões lado a lado: **TXT** e **PDF**.
- O nome do arquivo inclui o tomador selecionado (ou "Todos").

#### Tratamento de Erros (linhas 427–428)
- `try/except` genérico que exibe o erro na tela para o usuário.

---

## 7. Deploy (Docker)

### Dockerfile
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501",
     "--server.address=0.0.0.0", "--server.headless=true"]
```

### docker-compose.yml
```yaml
services:
  app:
    image: notas-app:latest
    networks: [Monadanet]
    deploy:
      replicas: 1
      labels:
        - traefik.enable=true
        - traefik.http.routers.notas-app.rule=Host(`notas.autozapx.com`)
        - traefik.http.routers.notas-app.tls.certresolver=letsencryptresolver
        - traefik.http.services.notas-app.loadbalancer.server.port=8501
networks:
  Monadanet:
    external: true
```

**Requisitos no servidor:**
- Docker Swarm ativo
- Rede `Monadanet` criada (`docker network create --driver overlay Monadanet`)
- Traefik rodando com entrypoint `websecure` e resolver `letsencryptresolver`
- DNS de `notas.autozapx.com` apontando para o IP do servidor

---

## 8. Histórico de Versões

| Versão | Data | Mudanças |
|--------|------|----------|
| **1.0.0** | — | Versão inicial: suporte apenas a PDF, agrupamento por Tomador + Contrato |
| **1.1.0** | — | Adicionado suporte a upload de CSV |
| **2.0.0** | 17/05/2026 | Reestruturação completa: 7 colunas do CSV, remoção de CONTRATO, agrupamento por CNPJ com soma, 4 KPIs, novo formato de relatórios |

---

## 9. Glossário

| Termo | Significado |
|-------|-------------|
| **NFS-e** | Nota Fiscal de Serviço Eletrônica |
| **Tomador de Serviços** | Empresa que **contrata** o serviço (cliente) |
| **Prestador de Serviços** | Empresa que **executa** o serviço |
| **CNPJ** | Cadastro Nacional da Pessoa Jurídica (identificador único da empresa) |
| **ISS** | Imposto Sobre Serviços (tributo municipal) |
| **Alíquota** | Percentual do imposto aplicado sobre o valor do serviço |
| **Traefik** | Reverse proxy/load balancer que roteia o tráfego HTTP/HTTPS |
| **Streamlit** | Framework Python para criar interfaces web interativas rapidamente |

---

*Documentação gerada em 17/05/2026 — Analisador de Notas Fiscais v2.0.0*
