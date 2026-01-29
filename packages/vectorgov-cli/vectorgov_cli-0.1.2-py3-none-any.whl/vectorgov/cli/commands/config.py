"""
Comando de configuração do CLI VectorGov.
"""

import typer
from rich.console import Console
from rich.table import Table

from ..utils.config import ConfigManager

app = typer.Typer(no_args_is_help=True)
console = Console()
config_manager = ConfigManager()


@app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Nome da configuração"),
    value: str = typer.Argument(..., help="Valor da configuração"),
):
    """
    Define uma configuração.

    Exemplos:
        vectorgov config set api_key vg_sua_chave
        vectorgov config set default_mode precise
    """
    # Valida chaves conhecidas
    valid_keys = ["api_key", "default_mode", "default_top_k", "output_format"]

    if key not in valid_keys:
        console.print(f"[yellow]Aviso:[/yellow] '{key}' não é uma chave conhecida.")
        console.print(f"Chaves válidas: {', '.join(valid_keys)}")

    config_manager.set(key, value)
    console.print(f"[green]OK[/green] Configuracao '{key}' salva!")


@app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Nome da configuração"),
):
    """
    Obtém uma configuração.

    Exemplos:
        vectorgov config get api_key
        vectorgov config get default_mode
    """
    value = config_manager.get(key)

    if value is None:
        console.print(f"[yellow]![/yellow] Configuracao '{key}' nao definida.")
    else:
        # Mascara API key
        if key == "api_key" and value:
            value = value[:8] + "..." + value[-4:]
        console.print(f"{key}: {value}")


@app.command("list")
def config_list():
    """
    Lista todas as configurações.

    Exemplo:
        vectorgov config list
    """
    configs = config_manager.list_all()

    if not configs:
        console.print("[yellow]![/yellow] Nenhuma configuracao definida.")
        return

    table = Table(title="Configurações")
    table.add_column("Chave", style="cyan")
    table.add_column("Valor")

    for key, value in configs.items():
        # Mascara API key
        if key == "api_key" and value:
            value = value[:8] + "..." + value[-4:]
        table.add_row(key, str(value))

    console.print(table)
    console.print(f"\nArquivo: {config_manager.config_file}")


@app.command("delete")
def config_delete(
    key: str = typer.Argument(..., help="Nome da configuração"),
):
    """
    Remove uma configuração.

    Exemplo:
        vectorgov config delete default_mode
    """
    if config_manager.get(key):
        config_manager.delete(key)
        console.print(f"[green]OK[/green] Configuracao '{key}' removida!")
    else:
        console.print(f"[yellow]![/yellow] Configuracao '{key}' nao existe.")


@app.command("path")
def config_path():
    """
    Mostra o caminho do arquivo de configuração.

    Exemplo:
        vectorgov config path
    """
    console.print(f"Arquivo de configuração: {config_manager.config_file}")
