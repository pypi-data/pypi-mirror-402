"""
Comando de estimativa de tokens do CLI VectorGov.
"""

import json
import typer
from rich.console import Console
from rich.table import Table

from ..utils.config import ConfigManager

app = typer.Typer()
console = Console()
config_manager = ConfigManager()


@app.callback(invoke_without_command=True)
def tokens(
    query: str = typer.Argument(..., help="Query para buscar e estimar tokens"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Número de resultados (1-20)"),
    mode: str = typer.Option("balanced", "--mode", "-m", help="Modo de busca: fast, balanced, precise"),
    output: str = typer.Option("table", "--output", "-o", help="Formato: table, json"),
):
    """
    Estima tokens de uma busca para planejamento de uso de LLM.

    Útil para verificar se o contexto cabe na janela de contexto
    do modelo que você pretende usar.

    Exemplos:
        vectorgov tokens "O que é ETP?"
        vectorgov tokens "O que é ETP?" --top-k 10
        vectorgov tokens "pesquisa de preços" --output json
    """
    # Obtém API key
    api_key = config_manager.get("api_key")
    if not api_key:
        console.print("[red]Erro:[/red] API key não configurada.")
        console.print("  Use 'vectorgov auth login' para configurar.")
        raise typer.Exit(1)

    # Valida parâmetros
    if top_k < 1 or top_k > 20:
        console.print("[red]Erro:[/red] top_k deve estar entre 1 e 20.")
        raise typer.Exit(1)

    if mode not in ["fast", "balanced", "precise"]:
        console.print("[red]Erro:[/red] mode deve ser: fast, balanced ou precise.")
        raise typer.Exit(1)

    try:
        from vectorgov import VectorGov

        console.print(f"Buscando e estimando tokens para: [cyan]{query}[/cyan]", style="dim")

        vg = VectorGov(api_key=api_key)

        # Busca resultados
        results = vg.search(query, top_k=top_k, mode=mode)

        # Estima tokens
        stats = vg.estimate_tokens(results, query=query)

        if output == "json":
            data = {
                "query": query,
                "top_k": top_k,
                "context_tokens": stats.context_tokens,
                "system_tokens": stats.system_tokens,
                "query_tokens": stats.query_tokens,
                "total_tokens": stats.total_tokens,
                "hits_count": stats.hits_count,
                "char_count": stats.char_count,
                "encoding": stats.encoding,
            }
            console.print_json(json.dumps(data, ensure_ascii=False))
        else:
            # Tabela formatada
            console.print()
            table = Table(title="Estimativa de Tokens")
            table.add_column("Componente", style="cyan")
            table.add_column("Tokens", justify="right", style="green")
            table.add_column("Descrição")

            table.add_row("Contexto", f"{stats.context_tokens:,}", f"{stats.hits_count} hits da busca")
            table.add_row("System Prompt", f"{stats.system_tokens:,}", "Instruções do sistema")
            table.add_row("Query", f"{stats.query_tokens:,}", "Pergunta do usuário")
            table.add_row("─" * 15, "─" * 10, "─" * 25)
            table.add_row("[bold]Total[/bold]", f"[bold]{stats.total_tokens:,}[/bold]", f"{stats.char_count:,} caracteres")

            console.print(table)

            # Comparação com limites de modelos populares
            console.print()
            console.print("[dim]Comparação com limites de modelos:[/dim]")

            models = [
                ("GPT-4o", 128_000),
                ("GPT-4o-mini", 128_000),
                ("Claude 3.5 Sonnet", 200_000),
                ("Gemini 2.0 Flash", 1_000_000),
            ]

            for model_name, limit in models:
                pct = (stats.total_tokens / limit) * 100
                if pct < 50:
                    status = f"[green]OK {pct:.1f}%[/green]"
                elif pct < 80:
                    status = f"[yellow]!! {pct:.1f}%[/yellow]"
                else:
                    status = f"[red]X {pct:.1f}%[/red]"
                console.print(f"  {model_name}: {status} ({stats.total_tokens:,}/{limit:,})")

    except Exception as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)
