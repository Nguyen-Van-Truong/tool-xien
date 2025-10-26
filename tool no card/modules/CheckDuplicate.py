import os
from collections import defaultdict

class DuplicateChecker:
    def __init__(self, file_path="acc.txt"):
        self.file_path = file_path
        self.duplicates = defaultdict(list)
        self.unique_accounts = []
        
    def read_accounts(self):
        """Đọc tất cả tài khoản từ file"""
        if not os.path.exists(self.file_path):
            print(f"Không tìm thấy file {self.file_path}")
            return False
            
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Lọc bỏ các dòng trống và khoảng trắng
                lines = [line.strip() for line in lines if line.strip()]
                return lines
        except Exception as e:
            print(f"Lỗi khi đọc file: {str(e)}")
            return False

    def find_duplicates(self, accounts):
        """Tìm các tài khoản trùng email"""
        for index, account in enumerate(accounts):
            try:
                # Giả sử email là phần đầu tiên của mỗi dòng
                email = account.split('|')[0].strip()
                self.duplicates[email].append((index, account))
            except Exception as e:
                print(f"Lỗi khi xử lý dòng {index + 1}: {str(e)}")
                continue

    def process_duplicates(self):
        """Xử lý các tài khoản trùng và giữ lại tài khoản đầu tiên"""
        for email, accounts in self.duplicates.items():
            if len(accounts) > 1:
                print(f"\nTìm thấy {len(accounts)} tài khoản trùng email: {email}")
                # Giữ lại tài khoản đầu tiên
                first_account = accounts[0][1]
                self.unique_accounts.append(first_account)
                print(f"Giữ lại tài khoản: {first_account}")
                # In ra các tài khoản bị xóa
                for _, account in accounts[1:]:
                    print(f"Xóa tài khoản: {account}")
            else:
                # Nếu không trùng thì giữ nguyên
                self.unique_accounts.append(accounts[0][1])

    def save_unique_accounts(self):
        """Lưu các tài khoản không trùng vào file"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                for account in self.unique_accounts:
                    f.write(account + '\n')
            print(f"\nĐã lưu {len(self.unique_accounts)} tài khoản không trùng vào file {self.file_path}")
            return True
        except Exception as e:
            print(f"Lỗi khi lưu file: {str(e)}")
            return False

    def run(self):
        """Chạy toàn bộ quy trình kiểm tra và xóa trùng"""
        print("Bắt đầu kiểm tra tài khoản trùng...")
        
        # Đọc tài khoản
        accounts = self.read_accounts()
        if not accounts:
            return False
            
        print(f"Đọc được {len(accounts)} tài khoản từ file")
        
        # Tìm trùng
        self.find_duplicates(accounts)
        
        # Xử lý trùng
        self.process_duplicates()
        
        # Lưu kết quả
        return self.save_unique_accounts()

def main():
    checker = DuplicateChecker()
    checker.run()

if __name__ == "__main__":
    main() 