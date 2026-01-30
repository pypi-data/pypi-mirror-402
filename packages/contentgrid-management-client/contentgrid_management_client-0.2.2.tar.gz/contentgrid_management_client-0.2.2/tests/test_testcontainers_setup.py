import requests
from tests.management_testcontainers import keycloak_container, keycloak_user_token, architect_container, architect_with_auth, gateway_container, gateway_with_auth
    
    
def test_gateway_routes_to_architect(gateway_with_auth):
    """Test that Gateway routes requests to Architect."""
    gateway_url = gateway_with_auth["gateway_url"]
    headers = gateway_with_auth["headers"]
    
    response = requests.get(f"{gateway_url}/orgs", headers=headers)
    # This should be routed to Architect
    assert response.status_code != 404
    
    
def test_can_reach_blueprint_through_gw(gateway_with_auth):
    blueprint_url = gateway_with_auth["blueprint_url"]
    headers = gateway_with_auth["headers"]
    
    # Make authenticated request
    response = requests.get(blueprint_url, headers=headers)

    # Should not return 401 (unauthorized)
    assert response.status_code != 401