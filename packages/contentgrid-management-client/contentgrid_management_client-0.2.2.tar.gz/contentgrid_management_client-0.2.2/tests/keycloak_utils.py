import requests
from typing import Dict, Any, Optional
import logging

def get_user_token(keycloak_url: str, realm_name: str = "contentgrid-dev", 
                  client_id: str = "admin-cli", username: Optional[str] = None, 
                  password: Optional[str] = None, client_secret: Optional[str] = None) -> Dict[str, Any]:
    """
    Get access token for a user from Keycloak.
    
    Args:
        keycloak_url: Base URL of Keycloak (e.g., http://localhost:8082)
        realm_name: Name of the realm
        client_id: Client ID configured in Keycloak
        username: Username to authenticate
        password: User password
        client_secret: Client secret (required for confidential clients)
        internal_keycloak_url: Internal Keycloak URL to use for JWT issuer consistency
    
    Returns:
        Dictionary containing token information
    """
    # Use internal URL if provided, otherwise use external URL
    token_url = f"{keycloak_url}/realms/{realm_name}/protocol/openid-connect/token"
    
    data = {
        "grant_type": "password",
        "client_id": client_id,
        "username": username,
        "password": password
    }
    
    # Add client secret for confidential clients
    if client_secret:
        data["client_secret"] = client_secret
    
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        logging.info(f"Successfully obtained token for user {username}")
        
        return {
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "token_type": token_data.get("token_type", "Bearer"),
            "expires_in": token_data.get("expires_in"),
            "scope": token_data.get("scope")
        }
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise Exception(f"Authentication failed for user {username}. Check username/password.")
        elif e.response.status_code == 400:
            error_detail = e.response.json().get("error_description", "Bad request")
            raise Exception(f"Token request failed: {error_detail}")
        else:
            raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to connect to Keycloak: {e}")