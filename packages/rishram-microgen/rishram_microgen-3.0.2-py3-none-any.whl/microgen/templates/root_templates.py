"""Templates for root-level files"""

GITIGNORE_TEMPLATE = """
# Python
__pycache__/
*.pyc
*.pyo

# Environments
.env
.env.*
venv/
.venv/

# Logs
logs/
*/logs/

# IDE
.vscode/
.idea/

# Cache
*.pytest_cache/
.mypy_cache/

# Ignore generated help files
**/help.md
"""


ENV_TEMPLATE = """# Environment Configuration
DEBUG=True
ENVIRONMENT=development

# Database Configuration
DATABASE_URL=sqlite:///./database.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO

# Other Services
AUTH_SERVICE_URL=http://auth-service:8000
USER_SERVICE_URL=http://user-service:8001
PRODUCT_SERVICE_URL=http://product-service:8002
ORDER_SERVICE_URL=http://order-service:8003
PAYMENT_SERVICE_URL=http://payment-service:8004
NOTIFICATION_SERVICE_URL=http://notification-service:8005
"""


def docker_compose_template(services):
    """Generate docker-compose.yml content"""
    compose_services = ""
    port = 8000

    for service in services:
        compose_services += f"""
  {service}:
    build: ./{service}
    container_name: {service}
    ports:
      - "{port}:8000"
    volumes:
      - ./{service}:/app
"""
        port += 1

    return f"""version: "3.9"

services:
{compose_services}

networks:
  default:
    driver: bridge
"""
