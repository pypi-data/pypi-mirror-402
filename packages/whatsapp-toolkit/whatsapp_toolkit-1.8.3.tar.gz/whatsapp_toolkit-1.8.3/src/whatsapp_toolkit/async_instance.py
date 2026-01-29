import httpx
from typing import Optional, Dict
from colorstreak import Logger
import base64

class AsyncWhatsAppInstance:
    def __init__(self, api_key: str, instance_name: str, server_url: str):
        self.api_key = api_key
        self.name_instance = instance_name
        self.server_url = server_url.rstrip("/")
        
        # Headers base para todas las peticiones
        self.headers = {
            "apikey": self.api_key, 
            "Content-Type": "application/json"
        }

    async def create(self) -> Dict:
        """Crea la instancia en el servidor Evolution."""
        endpoint = f"{self.server_url}/instance/create"
        payload = {
            "instanceName": self.name_instance,
            "integration": "WHATSAPP-BAILEYS",
            "syncFullHistory": False,
        }
        
        async with httpx.AsyncClient(headers=self.headers) as client:
            try:
                resp = await client.post(endpoint, json=payload)
                return resp.json()
            except Exception as e:
                Logger.error(f"❌ Error creando instancia: {e}")
                return {"error": str(e)}

    async def delete(self) -> bool:
        """Elimina la instancia."""
        endpoint = f"{self.server_url}/instance/delete/{self.name_instance}"
        async with httpx.AsyncClient(headers=self.headers) as client:
            try:
                resp = await client.delete(endpoint)
                return resp.status_code == 200
            except Exception as e:
                Logger.error(f"❌ Error eliminando instancia: {e}")
                return False
            
    async def get_state(self) -> str:
        """
        Verifica el estado actual de la instancia.
        Retorna: 'open', 'connecting', 'close' o 'not_found'.
        """
        endpoint = f"{self.server_url}/instance/connectionState/{self.name_instance}"
        
        async with httpx.AsyncClient(headers=self.headers) as client:
            try:
                resp = await client.get(endpoint)
                Logger.debug(f"Estado de instancia '{self.name_instance}': {resp.status_code} - {resp.text}")
                
                if resp.status_code == 200:
                    # Evolution devuelve: { "instance": "main", "state": "open" }
                    return resp.json().get("state", "unknown")
                
                if resp.status_code == 404:
                    return "not_found"
                    
                return "error"
            except Exception as e:
                Logger.error(f"❌ Error verificando estado: {e}")
                return "error"
        

    async def get_connection_code(self) -> Optional[bytes]: # <--- Retorna BYTES
        """
        Obtiene el QR como bytes crudos (imagen PNG).
        """
        endpoint = f"{self.server_url}/instance/connect/{self.name_instance}"
        async with httpx.AsyncClient(headers=self.headers) as client:
            try:
                resp = await client.get(endpoint)
                if resp.status_code == 200:
                    data = resp.json()
                    b64_str = data.get("base64")
                    
                    if b64_str:
                        # Evolution a veces manda "data:image/png;base64,....."
                        # Hay que limpiar el encabezado si existe
                        if "," in b64_str:
                            b64_str = b64_str.split(",")[1]
                            
                        # Decodificamos a bytes
                        return base64.b64decode(b64_str)
                        
                return None
            except Exception as e:
                Logger.error(f"❌ Error obteniendo QR: {e}")
                return None
        