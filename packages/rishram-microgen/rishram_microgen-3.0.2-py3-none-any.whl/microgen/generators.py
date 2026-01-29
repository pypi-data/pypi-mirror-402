"""Core generation logic for microservices"""
import os
from pathlib import Path
from microgen.constants import TEMPLATE_FOLDERS, OTHER_MD_PATH
from microgen.templates.root_templates import GITIGNORE_TEMPLATE, ENV_TEMPLATE, docker_compose_template
from microgen.templates.service_templates import (
    settings_template,
    logger_template,
    main_template,
    dockerfile_template,
    requirements_template,
)


def create_root_files(services):
    """Create root-level files like .gitignore, .env and docker-compose.yml"""
    
    # Create .gitignore
    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write(GITIGNORE_TEMPLATE)

    # Create .env
    with open(".env", "w", encoding="utf-8") as f:
        f.write(ENV_TEMPLATE)

    # Create docker-compose.yml
    compose_content = docker_compose_template(services)
    with open("docker-compose.yml", "w", encoding="utf-8") as f:
        f.write(compose_content)


def create_service_folders(service_path):
    """Create folder structure for a microservice"""
    os.makedirs(service_path, exist_ok=True)

    for folder in TEMPLATE_FOLDERS:
        path = os.path.join(service_path, folder)
        os.makedirs(path, exist_ok=True)
        open(os.path.join(path, ".gitkeep"), "w", encoding="utf-8").close()
        # Create __init__.py for all folders except logs
        if not folder.endswith("logs"):
            open(os.path.join(path, "__init__.py"), "w", encoding="utf-8").close()



def create_service_files(service_path, service_name):
    """Create configuration and code files for a microservice"""
    
    # settings.py
    with open(f"{service_path}/app/config/settings.py", "w", encoding="utf-8") as f:
        f.write(settings_template(service_name))

    # logger.py
    with open(f"{service_path}/app/core/logger.py", "w", encoding="utf-8") as f:
        f.write(logger_template())

    # main.py
    with open(f"{service_path}/app/main.py", "w", encoding="utf-8") as f:
        f.write(main_template(service_name))

    # Dockerfile
    with open(f"{service_path}/Dockerfile", "w", encoding="utf-8") as f:
        f.write(dockerfile_template())

    # requirements.txt
    with open(f"{service_path}/requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements_template())


def create_help_file(service_path):
    """Create help.md from other.md template"""
    content = ""
    if OTHER_MD_PATH.exists():
        content = OTHER_MD_PATH.read_text(encoding="utf-8")

    with open(f"{service_path}/help.md", "w", encoding="utf-8") as f:
        f.write(content)
        f.write("\n\nThanks for using microgen — feedback: ujjwalr754@gmail.com\n")


def create_service(service_name):
    """Generate a complete microservice"""
    service_path = service_name

    create_service_folders(service_path)
    create_service_files(service_path, service_name)
    create_help_file(service_path)
