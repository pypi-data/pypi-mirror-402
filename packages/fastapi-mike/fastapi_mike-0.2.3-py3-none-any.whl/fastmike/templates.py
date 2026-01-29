def get_security_py():
    return """from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
SECRET_KEY = "MIKECARDONA076_CHANGE_ME"

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
"""

def get_deps_py():
    return """from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.db.session import SessionLocal # Asumiendo este archivo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login/access-token")

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# Aquí iría la lógica para obtener el current_user usando el token
"""

def get_admin_views_py():
    return """from sqladmin import ModelView
# from app.models.user import User

class UserAdmin(ModelView, model=None): # Cambiar None por el modelo User
    column_list = ["id", "username", "email"]
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

def get_main_py(project_name):
    return f"""from fastapi import FastAPI
from sqladmin import Admin
from app.api.v1.api import api_router
# from app.db.session import engine

app = FastAPI(title="{project_name}")

# Admin (Requiere configurar engine en db/session.py)
# admin = Admin(app, engine)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {{"status": "online", "author": "MIKECARDONA076"}}
"""

# Reutilizar funciones anteriores de templates.py (get_db_base, get_testmike_files, etc.)
def get_db_base():
    return """from sqlalchemy.ext.declarative import as_declarative, declared_attr
@as_declarative()
class Base:
    __name__: str
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
"""

def get_api_router():
    return "from fastapi import APIRouter\napi_router = APIRouter()"

def get_testmike_files(db_url):
    return {
        "db_check.py": f"import sqlalchemy; print('Testing {db_url}')",
        "auth_test.py": "from app.core.security import get_password_hash; print(get_password_hash('mike'))"
    }

def get_alembic_env_py():
    return "from app.db.base_class import Base\ntarget_metadata = Base.metadata"