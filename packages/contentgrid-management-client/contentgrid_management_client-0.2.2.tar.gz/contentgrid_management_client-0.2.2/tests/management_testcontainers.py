from testcontainers.generic.server import DockerContainer
from pytest import fixture
import logging
import os
import docker
import time
import requests
from pathlib import Path
from tests.keycloak_utils import get_user_token
from typing import Callable, Any

KEYCLOAK_EXPOSED_PORT = 8080
KEYCLOAK_ADMIN = "admin"
KEYCLOAK_ADMIN_PASSWORD = "admin"
KEYCLOAK_IMAGE = "quay.io/keycloak/keycloak:25.0.1"
KEYCLOAK_REALM_NAME = "contentgrid-dev"
KEYCLOAK_CLIENT_ID = "contentgrid-gateway"
KEYCLOAK_TEST_USERNAME = "watson"
KEYCLOAK_TEST_PASSWORD = "watson"

# Architect container constants
ARCHITECT_IMAGE = "docker.xenit.eu/contentgrid/architect:SNAPSHOT"
ARCHITECT_EXPOSED_PORT = 8080
ARCHITECT_MANAGEMENT_PORT = 8081
ARCHITECT_BOOTSTRAP = "true"
ARCHITECT_ASSISTANT_ENABLED = "true"
ARCHITECT_MAX_RETRIES = 60
ARCHITECT_SLEEP_INTERVAL = 5
ARCHITECT_DEFAULT_BLUEPRINT = "/orgs/holmes/projects/dcm/blueprints/main"

# Gateway container constants
GATEWAY_IMAGE = "ghcr.io/xenit-eu/contentgrid-gateway:SNAPSHOT"
GATEWAY_EXPOSED_PORT = 8080
GATEWAY_MAX_RETRIES = 10
GATEWAY_SLEEP_INTERVAL = 3
GATEWAY_CLIENT_ID = "contentgrid-gateway"
GATEWAY_CLIENT_SECRET = "d6a59786-ea91-4b7d-892f-eb3426b4d8cb"
GATEWAY_CLIENT_SCOPE = "openid,profile,email"

# Registry authentication constants
DEFAULT_REGISTRY_URL = "docker.xenit.eu"


def wait_for_service_ready(
    check_function: Callable[[], bool],
    service_name: str,
    max_retries: int,
    sleep_interval: int = 2,
    error_callback: Callable[[], Any] | None = None
) -> None:
    """
    Generic retry mechanism for waiting for services to be ready.
    
    Args:
        check_function: Function that returns True when service is ready
        service_name: Name of the service for logging
        max_retries: Maximum number of retry attempts
        sleep_interval: Time to sleep between retries in seconds
        error_callback: Optional function to call on final failure for debugging
    """
    for i in range(max_retries):
        try:
            if check_function():
                logging.info(f"{service_name} is ready")
                return
        except Exception as e:
            if i == max_retries - 1:
                if error_callback:
                    error_callback()
                raise Exception(f"{service_name} container did not start properly: {e}")
        
        logging.info(f"Waiting for {service_name} to be ready... ({i+1}/{max_retries})")
        time.sleep(sleep_interval)
    
    if error_callback:
        error_callback()
    raise Exception(f"{service_name} container did not start properly after {max_retries} retries")


keycloak_dir = Path(__file__).parent / "keycloak"
# Keycloak testcontainer
keycloak = DockerContainer(KEYCLOAK_IMAGE)
keycloak.with_command("start-dev --import-realm")
keycloak.with_exposed_ports(KEYCLOAK_EXPOSED_PORT)
keycloak.with_env("KEYCLOAK_ADMIN", KEYCLOAK_ADMIN)
keycloak.with_env("KEYCLOAK_ADMIN_PASSWORD", KEYCLOAK_ADMIN_PASSWORD)
keycloak.with_volume_mapping(str(keycloak_dir.absolute()), "/opt/keycloak/data/import/", mode="rw")

@fixture(scope="session")
def keycloak_container():
    """Setup Keycloak container for all tests."""
    
    keycloak.start()
    
    keycloak_host = keycloak.get_container_host_ip()
    keycloak_port = keycloak.get_exposed_port(KEYCLOAK_EXPOSED_PORT)
    keycloak_url = f"http://172.17.0.1:{keycloak_port}"
    
    logging.info(f"Started Keycloak container: {keycloak_url}")
    
    # Wait for Keycloak to be ready
    def check_keycloak_ready():
        response = requests.get(f"{keycloak_url}/realms/master/.well-known/openid-configuration", timeout=5)
        return response.status_code == 200
    
    wait_for_service_ready(
        check_function=check_keycloak_ready,
        service_name="Keycloak",
        max_retries=30,
        sleep_interval=2
    )
    
    # Set environment variable for OIDC issuer to point to the test container
    original_oidc_issuer = os.environ.get("OIDC_ISSUER")
    os.environ["OIDC_ISSUER"] = f"{keycloak_url}/realms/{KEYCLOAK_REALM_NAME}"
    
    yield {
        "url": keycloak_url,
        "host": keycloak_host,
        "port": keycloak_port,
        "admin_user": KEYCLOAK_ADMIN,
        "admin_password": KEYCLOAK_ADMIN_PASSWORD,
        "issuer_url": f"{keycloak_url}/realms/{KEYCLOAK_REALM_NAME}"
    }
    
    # Restore original environment variable
    if original_oidc_issuer:
        os.environ["OIDC_ISSUER"] = original_oidc_issuer
    else:
        os.environ.pop("OIDC_ISSUER", None)
    
    # Cleanup
    try:
        keycloak.stop()
        logging.info("Keycloak container stopped successfully")
    except (docker.errors.NotFound, docker.errors.APIError) as e:
        logging.warning(f"Keycloak container cleanup warning: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during Keycloak container cleanup: {e}")

@fixture
def keycloak_user_token(keycloak_container):
    """Get a user token for testing."""
    keycloak_url = keycloak_container["url"]
    
    token_data = get_user_token(
        keycloak_url=keycloak_url,
        realm_name=KEYCLOAK_REALM_NAME,
        client_id=KEYCLOAK_CLIENT_ID,  
        username=KEYCLOAK_TEST_USERNAME, 
        password=KEYCLOAK_TEST_PASSWORD,
        client_secret=GATEWAY_CLIENT_SECRET
    )
    
    return token_data

@fixture(scope="session")
def architect_container(keycloak_container):
    """Setup Architect container for all tests."""
    
    # Create architect container
    architect = DockerContainer(ARCHITECT_IMAGE)
    architect.with_exposed_ports(ARCHITECT_EXPOSED_PORT)
    architect.with_exposed_ports(ARCHITECT_MANAGEMENT_PORT)
    architect.with_env("CONTENTGRID_ARCHITECT_BOOTSTRAP", ARCHITECT_BOOTSTRAP)
    architect.with_env("CONTENTGRID_ARCHITECT_ASSISTANT_ENABLED", ARCHITECT_ASSISTANT_ENABLED)
    
    # Set up trusted JWT issuers - use the test Keycloak
    # Convert to container-accessible URL using Docker bridge gateway IP
    keycloak_issuer = keycloak_container["issuer_url"]
    architect.with_env("CONTENTGRID_SECURITY_OAUTH2_TRUSTEDJWTISSUERS_0", keycloak_issuer)
    
    try:
        architect.start()
        
        architect_host = "172.17.0.1"
        architect_port = architect.get_exposed_port(ARCHITECT_EXPOSED_PORT)
        architect_management_port = architect.get_exposed_port(ARCHITECT_MANAGEMENT_PORT)
        architect_url = f"http://{architect_host}:{architect_port}"
        architect_management_url = f"http://{architect_host}:{architect_management_port}"
        
        logging.info(f"Started Architect container: {architect_url}")
        
        # Wait for Architect to be ready
        def check_architect_ready():
            response = requests.get(f"{architect_management_url}/actuator/health/liveness", timeout=10)
            return response.status_code in [200, 404]  # 404 is also OK, means service is up
        
        def architect_error_callback():
            try:
                logs = architect.get_logs()
                logging.error(f"Architect container logs: {logs}")
            except Exception as log_error:
                logging.warning(f"Could not get container logs: {log_error}")
        
        wait_for_service_ready(
            check_function=check_architect_ready,
            service_name="Architect",
            max_retries=ARCHITECT_MAX_RETRIES,
            sleep_interval=ARCHITECT_SLEEP_INTERVAL,
            error_callback=architect_error_callback
        )
        
        yield {
            "url": architect_url,
            "host": architect_host,
            "port": architect_port,
            "keycloak_issuer": keycloak_issuer
        }
    
    except docker.errors.ImageNotFound:
        logging.error(f"Architect image not found: {ARCHITECT_IMAGE}")
        raise Exception(
            f"Cannot pull architect image {ARCHITECT_IMAGE}. "
            "Please check authentication or image availability."
        )
    except Exception as e:
        logging.error(f"Failed to start Architect container: {e}")
        raise
    
    finally:
        # Cleanup
        try:
            architect.stop()
            logging.info("Architect container stopped successfully")
        except (docker.errors.NotFound, docker.errors.APIError) as e:
            logging.warning(f"Architect container cleanup warning: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during Architect container cleanup: {e}")


@fixture
def architect_with_auth(architect_container, keycloak_user_token):
    """Provide Architect container with authentication token."""
    return {
        "architect_url": architect_container["url"],
        "blueprint_url": f"{architect_container['url']}{ARCHITECT_DEFAULT_BLUEPRINT}",
        "access_token": keycloak_user_token["access_token"],
        "keycloak_issuer": architect_container["keycloak_issuer"],
        "headers": {
            "Authorization": f"Bearer {keycloak_user_token['access_token']}",
            "Content-Type": "application/json"
        }
    }

@fixture(scope="session")
def gateway_container(keycloak_container, architect_container):
    """Setup Gateway container for all tests."""
    
    # Get URLs from other containers
    keycloak_issuer_uri = keycloak_container["issuer_url"]
    architect_uri = architect_container["url"]
    
    # Create gateway container (publicly available image)
    gateway = DockerContainer(GATEWAY_IMAGE)
    gateway.with_exposed_ports(GATEWAY_EXPOSED_PORT)
    
    # Convert Keycloak URL to be accessible from within Gateway container
    # Replace localhost with Docker bridge gateway IP for container-to-host communication
    
    # Set environment variables for OAuth2 client configuration
    gateway.with_env("SPRING_SECURITY_OAUTH2_CLIENT_PROVIDER_KEYCLOAK_ISSUERURI", keycloak_issuer_uri)
    gateway.with_env("SPRING_SECURITY_OAUTH2_CLIENT_REGISTRATION_KEYCLOAK_CLIENTID", GATEWAY_CLIENT_ID)
    gateway.with_env("SPRING_SECURITY_OAUTH2_CLIENT_REGISTRATION_KEYCLOAK_SCOPE", GATEWAY_CLIENT_SCOPE)
    gateway.with_env("SPRING_SECURITY_OAUTH2_CLIENT_REGISTRATION_KEYCLOAK_CLIENTSECRET", GATEWAY_CLIENT_SECRET)
    
    # Set environment variables for OAuth2 resource server
    gateway.with_env("SPRING_SECURITY_OAUTH2_RESOURCESERVER_JWT_ISSUERURI", keycloak_issuer_uri)
    
    # Set CORS configuration
    gateway.with_env("CONTENTGRID_GATEWAY_CORS_CONFIGURATIONS_LOCALHOST_ALLOWEDORIGINS", "http://localhost:8085,http://localhost:9085")
    gateway.with_env("CONTENTGRID_GATEWAY_CORS_CONFIGURATIONS_DEFAULT_ALLOWEDORIGINS", "http://172.17.0.1:8085,http://172.17.0.1:9085,http://localhost:9085,http://localhost:8085")
    
    # Disable testing bootstrap
    gateway.with_env("TESTING_BOOTSTRAP_ENABLE", "false")
    
    # Configure routes to architect (convert localhost to Docker bridge gateway IP)
    gateway.with_env("SPRING_CLOUD_GATEWAY_ROUTES_0_ID", "architect")
    gateway.with_env("SPRING_CLOUD_GATEWAY_ROUTES_0_URI", f"{architect_uri}/")
    gateway.with_env("SPRING_CLOUD_GATEWAY_ROUTES_0_PREDICATES_0", "Path=/,/orgs/**,/projects/**,/users/**,/blueprints/**,/datamodel/**,/permalink/**,/authorize/**")
    
    # Configure routes to assistant (will point to host machine for now)
    gateway.with_env("SPRING_CLOUD_GATEWAY_ROUTES_1_ID", "assistant")
    gateway.with_env("SPRING_CLOUD_GATEWAY_ROUTES_1_URI", "http://172.17.0.1:5002/")
    gateway.with_env("SPRING_CLOUD_GATEWAY_ROUTES_1_PREDICATES_0", "Path=/assistant,/assistant/**")
    
    try:
        gateway.start()
        
        gateway_host = gateway.get_container_host_ip()
        gateway_port = gateway.get_exposed_port(GATEWAY_EXPOSED_PORT)
        gateway_url = f"http://{gateway_host}:{gateway_port}"
        
        logging.info(f"Started Gateway container: {gateway_url}")
        
        # Wait for Gateway to be ready
        def check_gateway_ready():
            response = requests.get(f"{gateway_url}/actuator/health/liveness", timeout=10)
            return response.status_code in [200, 404]  # 404 is also OK, means service is up
        
        def gateway_error_callback():
            try:
                logs = gateway.get_logs()
                logging.error(f"Gateway container logs: {logs}")
            except Exception as log_error:
                logging.warning(f"Could not get container logs: {log_error}")
        
        wait_for_service_ready(
            check_function=check_gateway_ready,
            service_name="Gateway",
            max_retries=GATEWAY_MAX_RETRIES,
            sleep_interval=GATEWAY_SLEEP_INTERVAL,
            error_callback=gateway_error_callback
        )
        
        yield {
            "url": gateway_url,
            "host": gateway_host,
            "port": gateway_port,
            "keycloak_issuer": keycloak_issuer_uri,
            "architect_uri": architect_uri
        }
    
    except docker.errors.ImageNotFound:
        logging.error(f"Gateway image not found: {GATEWAY_IMAGE}")
        raise Exception(
            f"Cannot pull gateway image {GATEWAY_IMAGE}. "
            "Please check image availability."
        )
    except Exception as e:
        logging.error(f"Failed to start Gateway container: {e}")
        raise
    
    finally:
        # Cleanup
        try:
            gateway.stop()
            logging.info("Gateway container stopped successfully")
        except (docker.errors.NotFound, docker.errors.APIError) as e:
            logging.warning(f"Gateway container cleanup warning: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during Gateway container cleanup: {e}")

@fixture
def gateway_with_auth(gateway_container, keycloak_user_token):
    """Provide Gateway container with authentication token."""
    return {
        "gateway_url": gateway_container["url"],
        "access_token": keycloak_user_token["access_token"],
        "blueprint_url": f"{gateway_container['url']}{ARCHITECT_DEFAULT_BLUEPRINT}",
        "headers": {
            "Authorization": f"Bearer {keycloak_user_token['access_token']}",
            "Content-Type": "application/json"
        }
    }

