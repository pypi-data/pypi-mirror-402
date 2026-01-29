import click
import os
import pathlib
import subprocess
import sys
from .utils import print_banner, get_db_url
from . import templates

@click.group()
def main():
    """CLI Profesional fastapi-mike por MIKECARDONA076"""
    pass

@main.command()
@click.option('--name', default='fastapi-mike-api', help='Nombre del proyecto')
def init(name):
    """Inicializa la estructura completa e instala dependencias automáticamente."""
    print_banner()
    
    base_path = pathlib.Path(name)
    
    # 1. Creación de Carpetas dentro del directorio del proyecto
    folders = [
        "app/api/v1/endpoints", "app/core", "app/crud", "app/db",
        "app/models", "app/schemas", "app/services", "app/admin",
        "TESTMIKE"
    ]
    
    click.secho(f"📁 Creando estructura profesional en ./{name}...", fg="cyan")
    base_path.mkdir(exist_ok=True)
    
    for folder in folders:
        path = base_path / folder
        path.mkdir(parents=True, exist_ok=True)
        (path / "__init__.py").touch()

    # 2. Preparación de Datos
    db_url = get_db_url()
    
    files_map = {
        "app/main.py": templates.get_main_py(name),
        "app/core/security.py": templates.get_security_py(),
        "app/api/deps.py": templates.get_deps_py(),
        "app/admin/views.py": templates.get_admin_views_py(),
        "app/db/base_class.py": templates.get_db_base(),
        "Dockerfile": templates.get_dockerfile_content(),
        "docker-compose.yml": templates.get_compose_content(),
        "requirements.txt": templates.get_requirements_content(),
        ".env": f"PROJECT_NAME={name}\nDATABASE_URL={db_url}\nSECRET_KEY=MIKE_SECRET_076\n"
    }

    # 3. Escritura de Archivos
    click.echo("📝 Generando archivos de configuración...")
    for path_str, content in files_map.items():
        try:
            target_file = base_path / path_str
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(content)
            click.echo(f"  ✔ {path_str}")
        except Exception as e:
            click.secho(f"  ✘ Error creando {path_str}: {e}", fg="red")

    # 4. Suite de Pruebas TESTMIKE
    click.echo("🧪 Generando Suite de pruebas rápidas...")
    tests = templates.get_testmike_files(db_url)
    for filename, content in tests.items():
        with open(base_path / "TESTMIKE" / filename, "w", encoding="utf-8") as f:
            f.write(content)

    # 5. Inicializar Alembic
    click.echo("⚙️ Configurando Alembic...")
    try:
        # Ejecutamos alembic init dentro de la subcarpeta
        subprocess.run(["alembic", "init", "alembic"], cwd=base_path, capture_output=True)
        with open(base_path / "alembic/env.py", "w", encoding="utf-8") as f:
            f.write(templates.get_alembic_env_py())
    except Exception:
        click.echo("  ⚠️ Salto de Alembic (configuración manual requerida)")

    # 6. Instalación automática de paquetes
    click.echo("\n📦 Instalando dependencias desde requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(base_path / "requirements.txt")])
        click.secho("✅ Dependencias instaladas correctamente.", fg="green", bold=True)
    except Exception as e:
        click.secho(f"⚠️ No se pudo completar la instalación automática: {e}", fg="yellow")

    click.secho(f"\n🚀 ¡Proyecto '{name}' creado con éxito!", fg="green", bold=True)
    click.echo(f"\nPara comenzar:")
    click.echo(f"  1. cd {name}")
    click.echo("  2. uvicorn app.main:app --reload")
