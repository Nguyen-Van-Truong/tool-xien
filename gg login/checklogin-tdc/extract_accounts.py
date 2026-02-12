import pdfplumber
import re
import os

FOLDER = os.path.dirname(os.path.abspath(__file__))
MSSV_PATTERN = re.compile(r'^(\d{5})([a-zA-Z]{2})(\d{4})$')

def mssv_to_account(mssv):
    """Chuyển MSSV thành email|password"""
    m = MSSV_PATTERN.match(mssv.strip())
    if not m:
        return None
    prefix, letters, suffix = m.groups()
    email = f"{prefix}{letters.lower()}{suffix}@mail.tdc.edu.vn"
    password = f"{prefix}{letters.upper()}{suffix}@mail.tdc.edu.vn"
    return f"{email}|{password}"

def extract_from_pdf(pdf_path):
    """Trích xuất danh sách MSSV từ file PDF"""
    accounts = []
    seen = set()
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or len(row) < 2:
                        continue
                    cell = row[1]  # MSSV ở cột thứ 2
                    if not cell:
                        continue
                    cell = cell.strip()
                    if MSSV_PATTERN.match(cell) and cell not in seen:
                        seen.add(cell)
                        acc = mssv_to_account(cell)
                        if acc:
                            accounts.append(acc)
    return accounts

def main():
    pdf_files = sorted([f for f in os.listdir(FOLDER) if f.lower().endswith('.pdf')])
    if not pdf_files:
        print("Khong tim thay file PDF nao!")
        return

    total = 0
    for pdf_file in pdf_files:
        pdf_path = os.path.join(FOLDER, pdf_file)
        txt_name = os.path.splitext(pdf_file)[0] + '.txt'
        txt_path = os.path.join(FOLDER, txt_name)

        accounts = extract_from_pdf(pdf_path)
        with open(txt_path, 'w', encoding='utf-8') as f:
            for acc in accounts:
                f.write(acc + '\n')

        print(f"[+] {pdf_file} -> {txt_name} ({len(accounts)} accounts)")
        if accounts:
            print(f"    VD: {accounts[0]}")
        total += len(accounts)

    print(f"\nTong: {total} accounts tu {len(pdf_files)} file PDF")

if __name__ == '__main__':
    main()
