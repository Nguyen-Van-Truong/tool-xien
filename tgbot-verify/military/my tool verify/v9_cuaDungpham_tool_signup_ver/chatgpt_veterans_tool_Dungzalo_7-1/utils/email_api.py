"""
Email API - Xử lý email API để đọc OTP và verification links
"""

import aiohttp
import asyncio


class EmailAPI:
    """Email API handler"""
    
    def __init__(self, email_login: str, refresh_token: str, client_id: str):
        self.email_login = email_login
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.api_url = 'https://buonqua.online/api/get_messages_oauth2.php'
    
    async def get_messages(self) -> list:
        """Lấy messages từ email API"""
        try:
            payload = {
                'email': self.email_login,
                'refresh_token': self.refresh_token,
                'client_id': self.client_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('status') and data.get('messages'):
                            # Sort by date (newest first)
                            messages = data['messages']
                            messages.sort(key=lambda x: x.get('date', 0), reverse=True)
                            return messages
                        else:
                            return []
                    else:
                        return []
        except Exception as e:
            print(f"Error getting messages: {str(e)}")
            return []
    
    def get_messages_sync(self) -> list:
        """Synchronous wrapper"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.get_messages())
        loop.close()
        return result

