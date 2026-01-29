"""
Comandos de autenticação do CLI VectorGov.
"""

import typer
from rich.console import Console
from rich.prompt import Prompt

from ..utils.config import ConfigManager

app = typer.Typer(no_args_is_help=True)
console = Console()
config_manager = ConfigManager()


@app.command()
def login(
    api_key: str = typer.Option(
        None,
        "--api-key", "-k",
        help="API key do VectorGov. Se não fornecida, será solicitada interativamente."
    ),
):
    """
    Configura a API key para autenticação.

    Exemplo:
        vectorgov auth login
        vectorgov auth login --api-key vg_sua_chave
    """
    if not api_key:
        api_key = Prompt.ask("Digite sua API key", password=True)

    if not api_key.startswith("vg_"):
        console.print("[red]Erro:[/red] API key deve começar com 'vg_'")
        raise typer.Exit(1)

    # Testa a API key
    console.print("Validando API key...", style="dim")
    try:
        from vectorgov import VectorGov
        vg = VectorGov(api_key=api_key)
        # Faz uma busca simples para validar
        vg.search("teste", top_k=1)
        console.print("[green]OK[/green] API key valida!")
    except Exception as e:
        console.print(f"[red]ERRO[/red] Erro ao validar API key: {e}")
        raise typer.Exit(1)

    # Salva a configuracao
    config_manager.set("api_key", api_key)
    console.print("[green]OK[/green] Configuracao salva com sucesso!")
    console.print(f"  Arquivo: {config_manager.config_file}")


@app.command()
def logout():
    """
    Remove a API key salva.

    Exemplo:
        vectorgov auth logout
    """
    if config_manager.get("api_key"):
        config_manager.delete("api_key")
        console.print("[green]OK[/green] API key removida com sucesso!")
    else:
        console.print("[yellow]![/yellow] Nenhuma API key configurada.")


@app.command()
def status():
    """
    Mostra o status da autenticação atual.

    Exemplo:
        vectorgov auth status
    """
    api_key = config_manager.get("api_key")

    if not api_key:
        console.print("[yellow]![/yellow] Nenhuma API key configurada.")
        console.print("  Use 'vectorgov auth login' para configurar.")
        return

    # Mascara a API key
    masked = api_key[:8] + "..." + api_key[-4:]
    console.print(f"[green]OK[/green] API key configurada: {masked}")

    # Testa a conexao
    console.print("Testando conexao...", style="dim")
    try:
        from vectorgov import VectorGov
        vg = VectorGov(api_key=api_key)
        vg.search("teste", top_k=1)
        console.print("[green]OK[/green] Conexao OK!")
    except Exception as e:
        console.print(f"[red]ERRO[/red] Erro na conexao: {e}")


@app.command()
def whoami():
    """
    Alias para 'status'. Mostra informações da conta atual.
    """
    status()
