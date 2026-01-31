import httpx
from loguru import logger
from src.config import settings


class EvolutionClient:
    """Client for Evolution API communication"""
    
    def __init__(self):
        self.base_url = settings.evolution_api_url
        self.api_key = settings.evolution_api_key
        self.instance_name = settings.evolution_instance_name
        self.headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def send_text_message(self, phone: str, message: str) -> dict:
        """
        Send text message via Evolution API
        
        Args:
            phone: Phone number (format: 5562999999999)
            message: Text message to send
            
        Returns:
            dict: Response from Evolution API
        """
        try:
            # Ensure phone has @s.whatsapp.net suffix
            if not phone.endswith("@s.whatsapp.net"):
                remote_jid = f"{phone}@s.whatsapp.net"
            else:
                remote_jid = phone
            
            url = f"{self.base_url}/message/sendText/{self.instance_name}"
            
            payload = {
                "number": remote_jid,
                "text": message
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"✉️ Message sent to {phone[:8]}... - Status: {response.status_code}")
                return result
        
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error sending message: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
            raise
    
    async def send_file(self, phone: str, file_url: str, caption: str = None) -> dict:
        """
        Send file/media via Evolution API
        
        Args:
            phone: Phone number
            file_url: URL of the file to send
            caption: Optional caption for the file
            
        Returns:
            dict: Response from Evolution API
        """
        try:
            if not phone.endswith("@s.whatsapp.net"):
                remote_jid = f"{phone}@s.whatsapp.net"
            else:
                remote_jid = phone
            
            url = f"{self.base_url}/message/sendMedia/{self.instance_name}"
            
            payload = {
                "number": remote_jid,
                "mediatype": "document",
                "media": file_url
            }
            
            if caption:
                payload["caption"] = caption
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"📎 File sent to {phone[:8]}...")
                return result
        
        except Exception as e:
            logger.error(f"❌ Error sending file: {e}")
            raise
    
    async def get_instance_status(self) -> dict:
        """Get instance connection status"""
        try:
            url = f"{self.base_url}/instance/connectionState/{self.instance_name}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
        
        except Exception as e:
            logger.error(f"❌ Error getting instance status: {e}")
            raise
    
    async def set_webhook(self, webhook_url: str) -> dict:
        """
        Configure webhook for the instance
        
        Args:
            webhook_url: Your webhook URL (e.g., ngrok URL)
            
        Returns:
            dict: Response from Evolution API
        """
        try:
            url = f"{self.base_url}/webhook/set/{self.instance_name}"
            
            payload = {
                "url": webhook_url,
                "webhook_by_events": False,
                "webhook_base64": False,
                "events": [
                    "MESSAGES_UPSERT",
                    "MESSAGES_UPDATE",
                    "CONNECTION_UPDATE"
                ]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"🔗 Webhook configured: {webhook_url}")
                return result
        
        except Exception as e:
            logger.error(f"❌ Error setting webhook: {e}")
            raise


# Singleton instance
evolution_client = EvolutionClient()