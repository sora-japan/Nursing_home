import pdfplumber
with pdfplumber.opne("") as pdf:
   tables = pdf.pages[0].extract_tables()

