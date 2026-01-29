
# Microservice Folder Structure Guide
Made lovingly by Team Rishram, for developers who dream bigger
From my keyboard to your creations — with love,
        — Ujjwal Rana  ❤
## Overview
This document explains the purpose of each folder in your generated microservice architecture, complete with examples, sample `main.py`, route structure, logger usage, and best practices.

---

# 📁 Folder Structure

```
service-name/
│── app/
│   ├── api/
│   │   ├── routes/
│   │   ├── controllers/
│   │   └── __init__.py
│   ├── services/
│   ├── models/
│   ├── schemas/
│   ├── core/
│   ├── db/
│   ├── config/
│   ├── utils/
│   └── main.py
│── tests/
│── logs/
│── Dockerfile
│── requirements.txt
│── .env
```

---

# 📌 Folder Meanings

## ✔ **app/**
Main application folder.

---

## ✔ **api/routes/**
Contains route handler files.

Example:
```python
@router.get("/users")
def get_users():
    return [{"id": 1, "name": "John"}]
```

---

## ✔ **api/controllers/**
Controller logic.

Controller = Request Handler (API Layer)

You can think of it like this:

Routes define the URL → /login, /upload, /detect-ai

## Controller contains the function that runs when that route is hit

Controller = Middleman

User → Route → Controller → Service → DB
Controller just connects these.

Controller handles:

"User is asking for something → let me send it to service → and reply back."
---

## ✔ **services/**
Reusable service classes.

Simple Definition
Controllers = Handle Requests
Services = Handle Logic

---

## ✔ **models/**
Database ORM models.

Example:
```python

from sqlalchemy import Column, Integer, String
from db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)


```
---

## ✔ **schemas/**
Pydantic request/response schemas.

Example:
```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True

```


---

## ✔ **core/**
System core utilities (logging, security, middleware).

base logic which works everywhere 
core logic 

---

## ✔ **db/**
Database connections & sessions.

---

## ✔ **config/**
Settings, environment loading.

---

## ✔ **utils/**
Small helper scripts.

---

# ---------------------------
# 🚀 Example main.py
# ---------------------------

```python
from fastapi import FastAPI
from app.config.settings import settings
from app.core.logger import get_logger
from app.api.routes import all_routes

logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0"
)

app.include_router(all_routes.router)

@app.get("/health")
def health_check():
    logger.info("Health check endpoint called")
    return {"status": "OK", "service": settings.app_name}

@app.on_event("startup")
async def startup_event():
    logger.info(f"{settings.app_name} started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"{settings.app_name} stopped")

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.app_name} microservice"}
```

---

# ---------------------------
# 📁 all_routes.py
# ---------------------------

```python
from fastapi import APIRouter
from app.api.routes.user_routes import router as user_router

router = APIRouter()
router.include_router(user_router, prefix="/users", tags=["Users"])
```

---

# ---------------------------
# 📁 Example user_routes.py
# ---------------------------

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def list_users():
    return {"users": []}
```

---

# ---------------------------
# 📁 Logger Example (core/logger.py)
# ---------------------------

```python
import os
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

```

---

# 🧪 tests/
Unit tests go here.

---

# 🗂 logs/
Logger output.

---

# You're Ready!
This is now a full production‑level microservices folder structure guide.
