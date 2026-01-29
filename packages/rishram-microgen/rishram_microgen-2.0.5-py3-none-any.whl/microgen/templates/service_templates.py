"""Templates for service-level files"""


def settings_template(service_name):
    """Generate settings.py content"""
    return f"""from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "{service_name}"
    database_url: str = "sqlite:///./database.db"
    debug: bool = True

    class Config:
        env_file = ".env"
        igonre_extra = True 

settings = Settings()
"""


def logger_template():
    """Generate logger.py content"""
    return """import os
import logging

LOG_DIR = "logs"
LOG_LEVEL = logging.INFO
LOG_PER_MODULE = True

def get_logger(module_name):
    logger = logging.getLogger(module_name)

    if not logger.handlers:
        try:
            logger.setLevel(LOG_LEVEL)
            os.makedirs(LOG_DIR, exist_ok=True)
            if LOG_PER_MODULE:
                log_filename = f"{module_name}.log"
            else:
                log_filename = "app.log"
            log_path = os.path.join(LOG_DIR, log_filename)
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(LOG_LEVEL)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(LOG_LEVEL)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            
        except Exception as e:
            print(f"Logger setup error: {e}")
            return logging.getLogger("fallback")
    
    return logger
"""


def main_template(service_name):
    """Generate main.py content"""
    return f"""from fastapi import FastAPI
from app.config.settings import settings
from app.core.logger import get_logger

logger = get_logger("{service_name}")

app = FastAPI(title=settings.app_name)

@app.on_event("startup")
def on_startup():
    logger.info("{service_name} started successfully.")

@app.get("/")
def root():
    logger.info("Root endpoint accessed.")
    return {{"message": "Welcome to {service_name}"}}
"""


def dockerfile_template():
    """Generate Dockerfile content"""
    return """FROM python:3.11-slim
WORKDIR /app

COPY ./app /app/app
COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""


def requirements_template():
    """Generate requirements.txt content"""
    return "fastapi\nuvicorn\npydantic-settings\n"
