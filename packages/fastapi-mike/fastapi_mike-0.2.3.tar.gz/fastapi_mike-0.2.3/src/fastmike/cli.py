import click
import os
import pathlib
import subprocess
from .utils import print_banner, get_db_url
from .templates import (
    get_main_py, 
    get_db_base, 
    get_api_router, 
    get_testmike_files,
    get_alembic_env_py,
    get_security_py,
    get_deps_py,
    get_admin_views_py,
    get_dockerfile_content
)

@click.group()
def main():
    """CLI de FastMike para proyectos FastAPI Enterprise por MIKECARDONA076."""
    pass

@main.command()
@click.option('--name', default='fastapi-project', help='Nombre del proyecto')
def init(name):
    """Inicializa un proyecto robusto con Auth, Admin y Docker."""
    print_banner()
    
    # 1. Estructura Completa
    folders = [
        "app/api/v1/endpoints", "app/core", "app/crud", "app/db",
        "app/models", "app/schemas", "app/services", "app/admin",
        "tests/api", "tests/crud", "TESTMIKE"
    ]
    
    click.echo("📁 Creando estructura de directorios pro...")
    for folder in folders:
        path = pathlib.Path(folder)
        path.mkdir(parents=True, exist_ok=True)
        (path / "__init__.py").touch()
    
    # 2. Configuración y Archivos Base
    db_url = get_db_url()
    secret_key = "MIKECARDONA076_SUPER_SECRET_KEY" # Esto debería ir a .env
    
    click.echo("📝 Generando módulos de Auth y Seguridad...")
    files_to_create = {
        "app/main.py": get_main_py(name),
        "app/db/base_class.py": get_db_base(),
        "app/api/v1/api.py": get_api_router(),
        "app/core/security.py": get_security_py(),
        "app/api/deps.py": get_deps_py(),
        "app/admin/views.py": get_admin_views_py(),
        "Dockerfile": get_dockerfile_content(),
        ".env": f"PROJECT_NAME={name}\nDATABASE_URL={db_url}\nSECRET_KEY={secret_key}\n"
    }

    for path, content in files_to_create.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    # 3. Generar Suite TESTMIKE
    click.echo("🧪 Generando suite TESTMIKE...")
    tests = get_testmike_files(db_url)
    for filename, content in tests.items():
        with open(f"TESTMIKE/{filename}", "w", encoding="utf-8") as f:
            f.write(content)

    # 4. Alembic
    click.echo("⚙️ Configurando migraciones...")
    try:
        if not os.path.exists("alembic.ini"):
            subprocess.run(["alembic", "init", "alembic"], capture_output=True)
        
        with open("alembic/env.py", "w", encoding="utf-8") as f:
            f.write(get_alembic_env_py())
    except Exception:
        click.secho("⚠️ Revisa que 'alembic' esté instalado para completar la config.", fg="yellow")

    click.secho(f"\n🚀 ¡Proyecto '{name}' configurado con Auth y Admin!", fg='green', bold=True)
    click.echo("Ejecuta: pip install fastapi uvicorn[standard] sqladmin sqlalchemy passlib[bcrypt] python-jose[cryptography]")