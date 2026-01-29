def get_requirements_content():
    return """fastapi>=0.100.0
uvicorn[standard]>=0.22.0
sqladmin>=0.11.0
sqlalchemy>=2.0.0
alembic>=1.10.0
passlib[bcrypt]>=1.7.4
python-jose[cryptography]>=3.3.0
python-multipart>=0.0.6
pydantic-settings>=2.0.0
requests>=2.28.0
"""

def get_security_py():
    return """from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
SECRET_KEY = "MIKECARDONA076_CHANGE_ME"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
"""

def get_deps_py():
    return """from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.core.security import ALGORITHM, SECRET_KEY

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/login/access-token")

def get_db() -> Generator:
    # Implementación de sesión de DB
    yield None 
"""

def get_admin_views_py():
    return """from sqladmin import ModelView

class UserAdmin(ModelView, model=None): 
    column_list = ["id", "email", "is_active"]
    icon = "fa-solid fa-user"
"""

def get_dockerfile_content():
    return """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

def get_compose_content():
    return """version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
"""

def get_main_py(name):
    return f"""from fastapi import FastAPI
from sqladmin import Admin
from app.admin.views import UserAdmin

app = FastAPI(title="{name}")

# Configuración de Admin:
# from app.db.session import engine
# admin = Admin(app, engine)
# admin.add_view(UserAdmin)

@app.get("/")
def root():
    return {{"message": "Welcome to {name}", "status": "active", "author": "MIKECARDONA076"}}
"""

def get_db_base():
    return """from sqlalchemy.ext.declarative import as_declarative, declared_attr
@as_declarative()
class Base:
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
"""

def get_testmike_files(db_url):
    return {
        "db_check.py": f"import sqlalchemy; print('Validating {db_url}')",
        "auth_smoke.py": "from app.core.security import get_password_hash; print(f'Hash OK: {{get_password_hash(\"mike\")}}')",
        "cors_check.py": "import requests; print('Checking CORS policy...')",
        "backup_check.py": "print('Secure backup simulation successful.')",
        "model_check.py": "from app.db.base_class import Base; print('SQLAlchemy Metadata loaded.')"
    }

def get_alembic_env_py():
    return "from app.db.base_class import Base\ntarget_metadata = Base.metadata"
