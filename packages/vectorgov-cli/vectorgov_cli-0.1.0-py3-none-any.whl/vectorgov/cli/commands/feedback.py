"""
Comando de feedback do CLI VectorGov.
"""

import typer
from rich.console import Console

from ..utils.config import ConfigManager

app = typer.Typer()
console = Console()
config_manager = ConfigManager()


@app.callback(invoke_without_command=True)
def feedback(
    query_id: str = typer.Argument(..., help="ID da query (obtido após search ou ask)"),
    like: bool = typer.Option(None, "--like", "-l", help="Marcar como positivo"),
    dislike: bool = typer.Option(None, "--dislike", "-d", help="Marcar como negativo"),
):
    """
    Envia feedback sobre uma resposta (like/dislike).

    Exemplos:
        vectorgov feedback abc123 --like
        vectorgov feedback abc123 --dislike
    """
    # Valida opções
    if like is None and dislike is None:
        console.print("[red]Erro:[/red] Especifique --like ou --dislike")
        raise typer.Exit(1)

    if like and dislike:
        console.print("[red]Erro:[/red] Use apenas --like OU --dislike, não ambos")
        raise typer.Exit(1)

    is_like = like if like is not None else not dislike

    # Obtém API key
    api_key = config_manager.get("api_key")
    if not api_key:
        console.print("[red]Erro:[/red] API key não configurada.")
        console.print("  Use 'vectorgov auth login' para configurar.")
        raise typer.Exit(1)

    # Envia feedback
    try:
        from vectorgov import VectorGov

        vg = VectorGov(api_key=api_key)
        vg.feedback(query_id, like=is_like)

        emoji = "👍" if is_like else "👎"
        status = "positivo" if is_like else "negativo"
        console.print(f"[green]✓[/green] Feedback {emoji} {status} enviado com sucesso!")

    except Exception as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)
