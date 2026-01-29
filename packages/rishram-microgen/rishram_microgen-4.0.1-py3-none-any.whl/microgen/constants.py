"""Constants and configuration for microgen CLI"""
from pathlib import Path

# Paths
PACKAGE_DIR = Path(__file__).resolve().parent
OTHER_MD_PATH = PACKAGE_DIR / "other.md"

# Folder structure template
TEMPLATE_FOLDERS = [
    "app/api/routes",
    "app/api/controller",
    "app/core",
    "app/config",
    "app/db",
    "app/services",
    "app/data",
    "app/models",
    "app/schemas",
    "tests",
    "logs"
]

# Default microservices to generate
DEFAULT_SERVICES = [
    "auth-service",
    "user-service",
    "product-service",
    "order-service",
    "payment-service",
    "notification-service"
]
