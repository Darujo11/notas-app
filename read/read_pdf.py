import pdfplumber

pdf_path = r"c:\Users\CLIENTE\OneDrive\Documentos\Skill\Dados\analista-dados\analista-dados\EMPRESA X 2021.pdf"
output_path = r"C:\Users\CLIENTE\.gemini\antigravity\brain\e2e4ebfe-3bc0-4f88-bdb1-647ae9308a2d\scratch\empresa_x_output.txt"

try:
    with pdfplumber.open(pdf_path) as pdf:
        with open(output_path, "w", encoding="utf-8") as out:
            for i, page in enumerate(pdf.pages):
                out.write(f"--- Page {i+1} ---\n")
                text = page.extract_text()
                out.write(text if text else "")
                out.write("\n" + "-" * 20 + "\n")
    print("Success")
except Exception as e:
    print(f"Error: {e}")
