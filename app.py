import streamlit as st
import pandas as pd
import pdfplumber
import io

st.set_page_config(page_title="Analisador de Notas Fiscais", layout="wide", page_icon="📄")

def clean_currency(x):
    """Converte valores monetários do formato BRL para float."""
    if isinstance(x, str):
        # Remove R$, pontos de milhar e substitui vírgula por ponto
        x = x.replace('R$', '').replace('.', '').replace(',', '.').strip()
        try:
            return float(x)
        except ValueError:
            return 0.0
    return x

@st.cache_data
def process_pdf(file_bytes):
    """Extrai tabelas do PDF e retorna um DataFrame consolidado."""
    all_data = []
    headers = None
    
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        total_pages = len(pdf.pages)
        progress_bar = st.progress(0)
        
        for i, page in enumerate(pdf.pages):
            # Mostrando o progresso
            progress_bar.progress((i + 1) / total_pages, text=f"Lendo página {i + 1} de {total_pages}...")
            
            # Extraindo a tabela
            tables = page.extract_tables()
            for table in tables:
                if not table: continue
                
                # Assume-se que a primeira página tem o cabeçalho
                # Para tabelas de múltiplas páginas, precisamos lidar com repetição de cabeçalho
                for row in table:
                    # Limpa quebras de linha nas células
                    clean_row = [str(cell).replace('\n', ' ') if cell else '' for cell in row]
                    
                    # Identifica cabeçalho se ainda não o tivermos
                    if headers is None and 'Nota' in clean_row[0] and 'Tomador' in str(clean_row):
                        headers = clean_row
                        continue
                        
                    # Pula repetição de cabeçalhos nas páginas subsequentes
                    if headers and clean_row == headers:
                        continue
                        
                    # Se for uma linha de dados e já tivermos o cabeçalho
                    if headers and len(clean_row) == len(headers):
                        primeira_coluna = clean_row[0].strip()
                        
                        # Se a primeira coluna tem números (ex: "00003846"), é uma nota nova
                        if any(char.isdigit() for char in primeira_coluna):
                            all_data.append(clean_row)
                        # Se não tem números, mas tem algum texto nas outras colunas, é provável continuação
                        elif all_data and any(c.strip() for c in clean_row):
                            # É continuação da linha anterior, então vamos juntar os textos
                            for j in range(len(headers)):
                                if clean_row[j].strip():
                                    all_data[-1][j] += " " + clean_row[j].strip()

    if headers and all_data:
        df = pd.DataFrame(all_data, columns=headers)
        return df
    else:
        return pd.DataFrame()

def prepare_dataframe(df):
    """Limpa e formata as colunas principais."""
    # Renomear colunas para garantir a ortografia exata do documento original
    col_mapping = {}
    for col in df.columns:
        if 'Nota' in col and 'Valor' not in col:
            col_mapping[col] = 'Nota'
        elif 'Tomador' in col:
            col_mapping[col] = 'Tomador de Serviços'
        elif 'Valor da Nota' in col:
            col_mapping[col] = 'Valor da Nota'
        elif 'CONTRATO' in col.upper():
            col_mapping[col] = 'CONTRATO'
        elif 'Crédito' in col or 'Crdito' in col or 'Cr' in col and 'dito' in col:
            col_mapping[col] = 'Valor Crédito'
        elif 'Emiss' in col:
            col_mapping[col] = 'Emissão'
        elif 'Cód' in col or 'Cd' in col:
            col_mapping[col] = 'Cód.'
            
    df = df.rename(columns=col_mapping)
    
    # Tratamento de dados
    if 'Valor da Nota' in df.columns:
        df['Valor da Nota'] = df['Valor da Nota'].apply(clean_currency)
        
    if 'Tomador de Serviços' in df.columns:
        df['CNPJ'] = df['Tomador de Serviços'].str.extract(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})')[0]
        df['Tomador de Serviços'] = df['Tomador de Serviços'].str.replace(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', '', regex=True).str.strip()
        
    if 'CONTRATO' in df.columns:
        df['CONTRATO'] = df['CONTRATO'].str.strip()
        # Preencher vazios
        df['CONTRATO'] = df['CONTRATO'].replace('', 'NÃO ESPECIFICADO')
        
    # Limpar Número da Nota (às vezes vem "00003846 (NFS-e)")
    if 'Nota' in df.columns:
        df['Nota'] = df['Nota'].str.extract(r'(\d+)')[0]

    return df


# === INTERFACE ===
st.title("📊 Analisador de Notas Fiscais (PDF)")
st.markdown("Faça o upload do seu relatório de Notas Fiscais em PDF para extrair, analisar e agrupar os dados por **Tomador de Serviços** e **Contrato**.")

uploaded_file = st.file_uploader("Arraste e solte o seu arquivo PDF aqui", type=["pdf"])

if uploaded_file is not None:
    st.info(f"Processando arquivo: {uploaded_file.name}")
    
    try:
        # 1. Extração
        raw_df = process_pdf(uploaded_file.getvalue())
        
        if raw_df.empty:
            st.error("Não foi possível encontrar a tabela de notas fiscais no documento. Verifique o formato do PDF.")
        else:
            # 2. Tratamento
            df = prepare_dataframe(raw_df)
            
            st.success(f"Extração concluída com sucesso! {len(df)} notas identificadas.")
            
            st.divider()
            
            # --- KPIs ---
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Notas", len(df))
            with col2:
                if 'Valor da Nota' in df.columns:
                    total_faturado = df['Valor da Nota'].sum()
                    st.metric("Valor Total Faturado", f"R$ {total_faturado:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            with col3:
                if 'Tomador de Serviços' in df.columns:
                    st.metric("Qtd. Tomadores Únicos", df['Tomador de Serviços'].nunique())
            
            st.divider()
            
            # --- VISÃO AGRUPADA ---
            st.subheader("📁 Agrupamento por Tomador e Contrato")
            
            df_filtered = df.copy()
            tomador_selecionado = "Todos"
            
            if 'Tomador de Serviços' in df.columns and 'CONTRATO' in df.columns:
                tomadores = sorted(df['Tomador de Serviços'].dropna().unique())
                
                # Filtro na tela
                tomador_selecionado = st.selectbox("Selecione um Tomador de Serviços para detalhar:", ["Todos"] + list(tomadores))
                
                df_filtered = df if tomador_selecionado == "Todos" else df[df['Tomador de Serviços'] == tomador_selecionado]
                
                # Agrupamento
                group_cols = ['Tomador de Serviços', 'CNPJ', 'CONTRATO'] if 'CNPJ' in df.columns else ['Tomador de Serviços', 'CONTRATO']
                grouped = df_filtered.groupby(group_cols).agg(
                    Qtd_Notas=('Nota', 'count'),
                    Valor_Total=('Valor da Nota', 'sum') if 'Valor da Nota' in df.columns else ('Nota', 'count')
                ).reset_index()
                
                # Ordenar o agrupamento
                grouped = grouped.sort_values(by=group_cols)
                
                # Ordenar o dataframe detalhado também
                sort_cols_df = ['Tomador de Serviços', 'CNPJ'] if 'CNPJ' in df.columns else ['Tomador de Serviços']
                df_filtered = df_filtered.sort_values(by=sort_cols_df)
                
                # Formatar moeda para exibição no Streamlit
                if 'Valor_Total' in grouped.columns:
                     grouped['Valor_Total_Formatado'] = grouped['Valor_Total'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                
                st.dataframe(
                    grouped.drop(columns=['Valor_Total']) if 'Valor_Total' in grouped.columns else grouped, 
                    use_container_width=True,
                    hide_index=True
                )
                
                # Detalhe das Notas
                with st.expander("Ver lista detalhada de notas do filtro atual"):
                    st.dataframe(df_filtered, use_container_width=True)
                    
            else:
                st.warning("Não foi possível identificar as colunas de 'Tomador de Serviços' ou 'CONTRATO' na tabela extraída.")
                st.write("Dados brutos extraídos:")
                st.dataframe(df)

            # --- EXPORTAÇÃO ---
            st.divider()
            st.subheader("📥 Exportar Dados")
            
            st.write("Se o CSV abrir desformatado no seu Excel, tente trocar o separador abaixo:")
            separador = st.radio("Separador do arquivo CSV:", ["; (Recomendado para Excel no Brasil)", ", (Padrão Internacional)"], horizontal=True)
            sep_char = ';' if ';' in separador else ','
            
            col_csv_agrup, col_csv_detalhe, col_excel = st.columns([2, 2, 2])
            
            # Limpar nome do arquivo
            nome_arquivo_tomador = "Todos" if tomador_selecionado == "Todos" else tomador_selecionado.replace(" ", "_").replace("/", "").replace(".", "")
            
            # Botão CSV (Agrupado)
            if 'Tomador de Serviços' in df.columns and 'CONTRATO' in df.columns:
                csv_agrup = grouped.to_csv(index=False, sep=sep_char, encoding='utf-8-sig').encode('utf-8-sig')
                col_csv_agrup.download_button(
                    label="Baixar CSV (Resumo Agrupado)",
                    data=csv_agrup,
                    file_name=f'resumo_agrupado_{nome_arquivo_tomador[:20]}.csv',
                    mime='text/csv',
                )
                
            # Botão CSV (Detalhado)
            csv_detalhe = df_filtered.to_csv(index=False, sep=sep_char, encoding='utf-8-sig').encode('utf-8-sig')
            col_csv_detalhe.download_button(
                label="Baixar CSV (Detalhado)",
                data=csv_detalhe,
                file_name=f'notas_detalhadas_{nome_arquivo_tomador[:20]}.csv',
                mime='text/csv',
            )
            
            # Botão Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, index=False, sheet_name='Notas_Filtradas')
                if 'Tomador de Serviços' in df.columns and 'CONTRATO' in df.columns:
                    grouped.to_excel(writer, index=False, sheet_name='Agrupamento_Filtrado')
                    
            col_excel.download_button(
                label="Baixar Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name=f'notas_extraidas_{nome_arquivo_tomador[:20]}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
    except Exception as e:
        st.error(f"Ocorreu um erro durante o processamento: {str(e)}")
