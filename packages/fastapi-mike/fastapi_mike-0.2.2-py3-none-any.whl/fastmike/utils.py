import click

def print_banner():
    banner = r"""
  __  __ _____ _  cache _____   _____            _____  _____   ____  _   _ 
 |  \/  |_   _| |/ /  | ____| |  ___|/\   / \  / ____|/ ____| / __ \| \ | |
 | \  / | | | | ' /   |  _|   | |_  /  \ /   \| (___ | |     | |  | |  \| |
 | |\/| | | | |  <    | |___  |  _|/ /\ \\ / / \___ \| |     | |  | | . ` |
 | |  | |_| |_| . \   | |____ | | / ____ \/ /  ____) | |____ | |__| | |\  |
 |_|  |_|_____|_|\_\  |______||_|/_/    \_\/  |_____/ \_____| \____/|_| \_|
                                                                           
                         DEVELOPED BY: MIKECARDONA076
    """
    click.secho(banner, fg="cyan")

def get_db_url():
    click.echo("\nConfiguración de Base de Datos:")
    db_type = click.prompt(
        "Elige DB (1: SQLite, 2: Postgres, 3: MySQL)", 
        type=click.Choice(['1', '2', '3']), 
        default='1'
    )
    if db_type == '1': return "sqlite:///./sql_app.db"
    if db_type == '2': return "postgresql://user:pass@localhost:5432/db"
    return "mysql+pymysql://user:pass@localhost:3306/db"