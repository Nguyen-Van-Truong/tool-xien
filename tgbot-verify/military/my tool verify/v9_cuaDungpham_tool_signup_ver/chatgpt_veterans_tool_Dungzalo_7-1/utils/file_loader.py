"""
File Loader - Load accounts, proxies, and veteran data from files
"""


class FileLoader:
    """File loader utility"""
    
    @staticmethod
    def load_accounts(file_path: str) -> list:
        """
        Load ChatGPT accounts from file
        Format: email-chatgpt|pass-chatgpt|email-login|pass-email|refresh_token|client_id
        """
        accounts = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split('|')
                if len(parts) >= 6:
                    accounts.append({
                        'email': parts[0].strip(),
                        'password': parts[1].strip(),
                        'emailLogin': parts[2].strip(),
                        'passEmail': parts[3].strip(),
                        'refreshToken': parts[4].strip(),
                        'clientId': parts[5].strip()
                    })
        
        return accounts
    
    @staticmethod
    def load_proxies(file_path: str) -> list:
        """
        Load proxies from file
        Format: host:port:username:password hoặc host:port
        """
        proxies = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split(':')
                if len(parts) >= 2:
                    proxy = {
                        'host': parts[0].strip(),
                        'port': parts[1].strip()
                    }
                    
                    if len(parts) >= 4:
                        proxy['username'] = parts[2].strip()
                        proxy['password'] = parts[3].strip()
                    
                    proxies.append(proxy)
        
        return proxies
    
    @staticmethod
    def load_veteran_data(file_path: str) -> list:
        """
        Load veteran data from file
        Format: first|last|branch|month|day|year
        """
        data = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split('|')
                if len(parts) >= 6:
                    data.append({
                        'first': parts[0].strip(),
                        'last': parts[1].strip(),
                        'branch': parts[2].strip(),
                        'month': parts[3].strip(),
                        'day': parts[4].strip(),
                        'year': parts[5].strip(),
                        'original': line
                    })
        
        return data
    
    @staticmethod
    def remove_veteran_data_from_file(file_path: str, line_to_remove: str) -> bool:
        """
        Remove a specific veteran data line from file
        Args:
            file_path: Path to veteran data file
            line_to_remove: The original line to remove (exact match)
        Returns True if successful
        """
        try:
            # Read all lines
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Filter out the line to remove
            valid_lines = []
            removed = False
            
            for line in lines:
                line_stripped = line.rstrip('\n\r').strip()
                if not line_stripped:
                    continue
                
                # Check if this is the line to remove (exact match)
                if line_stripped == line_to_remove.strip() and not removed:
                    removed = True
                    continue
                
                valid_lines.append(line_stripped)
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                for line in valid_lines:
                    f.write(line + '\n')
            
            return True
        except Exception as e:
            print(f"Error removing veteran data from file: {str(e)}")
            return False

