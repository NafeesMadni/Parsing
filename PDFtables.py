# #  pip install tabula-py
import tabula

tables = tabula.read_pdf('./files/BSCS-M2-22-13.pdf', pages='all')
output_file_path = './files/output.csv'

for table in tables:
    table.to_csv(output_file_path, index=False, encoding='utf-8')
