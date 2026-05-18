import pandas as pd
import pdfplumber
import io

def clean_currency(x):
    if isinstance(x, str):
        x = x.replace('R$', '').replace('.', '').replace(',', '.').strip()
        try:
            return float(x)
        except ValueError:
            return 0.0
    return x

def prepare_dataframe(df):
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
    
    if 'Valor da Nota' in df.columns:
        df['Valor da Nota'] = df['Valor da Nota'].apply(clean_currency)
        
    if 'Tomador de Serviços' in df.columns:
        df['CNPJ'] = df['Tomador de Serviços'].str.extract(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})')[0]
        df['Tomador de Serviços'] = df['Tomador de Serviços'].str.replace(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', '', regex=True).str.strip()
        
    if 'CONTRATO' in df.columns:
        df['CONTRATO'] = df['CONTRATO'].str.strip()
        df['CONTRATO'] = df['CONTRATO'].replace('', 'NÃO ESPECIFICADO')
        
    if 'Nota' in df.columns:
        df['Nota'] = df['Nota'].str.extract(r'(\d+)')[0]

    return df

def generate_text_report(df):
    report = []
    group_cols = ['Tomador de Serviços', 'CNPJ', 'CONTRATO'] if 'CNPJ' in df.columns else ['Tomador de Serviços', 'CONTRATO']
    
    for col in group_cols:
        if col not in df.columns:
            return "Colunas necessárias não encontradas para gerar o relatório."
            
    df_sorted = df.sort_values(by=group_cols)
    grouped = df_sorted.groupby(group_cols)
    
    for name, group in grouped:
        if isinstance(name, tuple):
            tomador = name[0]
            cnpj = name[1] if 'CNPJ' in df.columns else ""
            contrato = name[2] if 'CNPJ' in df.columns else name[1]
        else:
            tomador = name
            cnpj = ""
            contrato = ""
            
        report.append("Tomador de Serviço CNPJ Contrato(s) Identificado(s)")
        report.append(f"{tomador} {cnpj} {contrato}")
        report.append("Notas fiscais correspondentes:")
        
        for i, row in enumerate(group.itertuples()):
            nota = getattr(row, 'Nota', 'N/A')
            report.append(f"{i+1}. NFS-e nº {nota}")
        report.append("-" * 20)
        
    return "\n".join(report)

pdf_path = r"c:\Users\CLIENTE\OneDrive\Documentos\Skill\Dados\analista-dados\analista-dados\EMPRESA X 2021.pdf"

try:
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
        
    print("Reading PDF...")
    all_data = []
    headers = None
    
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            print(f"Page {i+1}: Found {len(tables)} tables.")
            for table in tables:
                if not table: continue
                for row in table:
                    clean_row = [str(cell).replace('\n', ' ') if cell else '' for cell in row]
                    
                    if headers is None and any('Nota' in str(c) for c in clean_row) and any('Tomador' in str(c) for c in clean_row):
                        headers = clean_row
                        print(f"Headers found: {headers}")
                        continue
                        
                    if headers and clean_row == headers:
                        continue
                        
                    if headers and len(clean_row) == len(headers):
                        primeira_coluna = clean_row[0].strip()
                        if any(char.isdigit() for char in primeira_coluna):
                            all_data.append(clean_row)
                        elif all_data and any(c.strip() for c in clean_row):
                            for j in range(len(headers)):
                                if clean_row[j].strip():
                                    all_data[-1][j] += " " + clean_row[j].strip()
                                    
    if headers and all_data:
        df = pd.DataFrame(all_data, columns=headers)
        print(f"Extracted {len(df)} rows.")
        
        df_clean = prepare_dataframe(df)
        print("Cleaned DataFrame columns:", df_clean.columns)
        
        report = generate_text_report(df_clean)
        print("Generated Report (preview):")
        print(report[:500])
    else:
        print("No tables found or headers not matched.")
        
except Exception as e:
    print(f"Error: {e}")
