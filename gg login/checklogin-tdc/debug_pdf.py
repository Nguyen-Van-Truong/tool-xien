import pdfplumber
import os

folder = r'E:\tool xien\gg login\checklogin-tdc'
for f in sorted(os.listdir(folder)):
    if not f.lower().endswith('.pdf'):
        continue
    path = os.path.join(folder, f)
    with pdfplumber.open(path) as pdf:
        sep = '=' * 70
        print(f'\n{sep}')
        print(f'FILE: {f} | Pages: {len(pdf.pages)}')
        print(sep)
        page = pdf.pages[0]
        text = page.extract_text()
        if text:
            lines = text.split('\n')
            for line in lines[:25]:
                print(line)
        else:
            print('NO TEXT')
        tables = page.extract_tables()
        if tables:
            print(f'\nTABLES: {len(tables)}')
            for i, t in enumerate(tables):
                cols = len(t[0]) if t else 0
                print(f'  Table {i+1}: {len(t)} rows x {cols} cols')
                for row in t[:5]:
                    print(f'    {row}')
