# Reestruturação do Analisador de Notas Fiscais

Reestruturar a lógica de colunas e agrupamento do `app.py` para: usar as colunas corretas do CSV, adicionar campos faltantes (Emissão, Alíquota, Valor ISS), remover CONTRATO de todo o app, e agrupar por CNPJ somando valores.

## User Review Required

> [!IMPORTANT]
> **Remoção total da coluna CONTRATO**: A coluna CONTRATO será removida de toda a lógica (mapeamento, agrupamento, filtros, relatórios TXT e PDF). A visão agrupada passará a agrupar por **Tomador de Serviços + CNPJ** apenas.

> [!IMPORTANT]
> **Agrupamento com soma**: Quando o mesmo CNPJ aparecer múltiplas vezes, as notas serão unificadas somando `Valor da Nota` e `Valor ISS`. O campo `Qtd_Notas` mostrará quantas notas foram somadas.

## Open Questions

> [!NOTE]
> O PDF atual também precisa extrair `Alíquota` e `Valor ISS`? Ou essas colunas são exclusivas do CSV?
> Por enquanto, o plano assume que o **PDF mantém a estrutura original** (extrai o que já extraía) e o **CSV** extrai as 7 colunas novas. Ambos terão a mesma lógica de agrupamento por CNPJ.

## Proposed Changes

### Extração e Mapeamento de Colunas

#### [MODIFY] [app.py](file:///c:/Users/CLIENTE/OneDrive/Documentos/Skill/Dados/analista-dados/analista-dados/app.py)

**1. `prepare_dataframe` — bloco CSV (linhas 102–134)**

Atualizar o `csv_col_map` para incluir as 7 colunas solicitadas:

| Coluna CSV original | Nome canônico | Posição na planilha |
|---|---|---|
| `Nº da Nota Fiscal Eletrônica` | **Nota** | A |
| `Data Hora da Emissão da Nota Fiscal` | **Emissão** | D |
| `CPF/CNPJ/NIF do Tomador` | **CNPJ** | Z |
| `Razão Social do Tomador` | **Tomador de Serviços** | AC |
| `Alíquota` | **Alíquota** | AW |
| `Valor dos Serviços` | **Valor da Nota** | AX |
| `Valor do ISS` | **Valor ISS** | BH |

Remover a linha que cria `df['CONTRATO']`.

**2. `prepare_dataframe` — bloco PDF (linhas 136–171)**

- Remover mapeamento de CONTRATO (`elif 'CONTRATO' in col.upper()`).
- Remover criação de `df['CONTRATO']` padrão.
- Adicionar mapeamento de `Valor ISS` se existir coluna com "ISS" no PDF.
- Adicionar mapeamento de `Alíquota` se existir coluna com "Al" no PDF.

---

### Relatórios TXT e PDF

**3. `generate_text_report` (linhas 174–207)**

- Trocar `group_cols` de `['Tomador de Serviços', 'CNPJ', 'CONTRATO']` para `['Tomador de Serviços', 'CNPJ']`.
- Remover referências a `contrato` no texto do relatório.
- Adicionar soma de `Valor da Nota` e `Valor ISS` por grupo no relatório.

**4. `generate_pdf_report` (linhas 209–250)**

- Mesmas mudanças: remover CONTRATO, adicionar totais de valor e ISS.

---

### Interface (UI Streamlit)

**5. Título e descrição (linhas 253–256)**

- Mudar título de `"📊 Analisador de Notas Fiscais (PDF)"` para `"📊 Analisador de Notas Fiscais"`.
- Remover menção a "Contrato" na descrição.

**6. KPIs (linhas 292–303)**

- Adicionar um 4º KPI: **Total ISS** (soma de `Valor ISS`).

**7. Visão Agrupada (linhas 306–351)**

Reescrever completamente:

- Título: `"📁 Agrupamento por Tomador (CNPJ)"` em vez de `"...e Contrato"`.
- Remover condição `'CONTRATO' in df.columns` → substituir por `'Tomador de Serviços' in df.columns`.
- `group_cols` passa a ser `['Tomador de Serviços', 'CNPJ']`.
- Agrupamento: `Qtd_Notas` (count), `Valor_Total` (sum de Valor da Nota), `ISS_Total` (sum de Valor ISS).
- Manter filtro por Tomador no selectbox.
- Manter expander com lista detalhada.

**8. Exportação (linhas 353–380)**

- Remover `CONTRATO` do nome do arquivo exportado.
- O resto permanece igual — os relatórios já estarão atualizados.

---

### Resumo dos arquivos afetados

| Arquivo | Mudança |
|---|---|
| `app.py` | Reescrever `prepare_dataframe`, `generate_text_report`, `generate_pdf_report`, e todo o bloco de UI |

Nenhum outro arquivo precisa ser modificado.

## Verification Plan

### Automated Tests
1. Rodar `python -m streamlit run app.py` e confirmar que o app inicia sem erros.
2. Subir o `p.csv` e confirmar:
   - As 7 colunas são reconhecidas.
   - Os KPIs mostram Total de Notas, Valor Total, Qtd Tomadores, e Total ISS.
   - A tabela agrupada mostra Tomador + CNPJ com somas corretas.
   - Os relatórios TXT e PDF são gerados sem menção a CONTRATO.
3. Subir um PDF (ex: `EMPRESA X 2021.pdf`) e confirmar que o fluxo PDF continua funcionando.

### Manual Verification
- Conferir visualmente a interface no browser em `http://localhost:8501`.
