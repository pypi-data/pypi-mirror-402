"""
Comando de busca do CLI VectorGov.
"""

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..utils.config import ConfigManager
from ..utils.output import OutputFormat, format_search_results

app = typer.Typer()
console = Console()
config_manager = ConfigManager()


@app.callback(invoke_without_command=True)
def search(
    query: str = typer.Argument(..., help="Pergunta ou termo de busca"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Número de resultados (1-20)"),
    mode: str = typer.Option(
        "balanced",
        "--mode", "-m",
        help="Modo de busca: fast, balanced, precise"
    ),
    use_cache: bool = typer.Option(False, "--cache", help="Usar cache semântico"),
    output: OutputFormat = typer.Option(
        OutputFormat.table,
        "--output", "-o",
        help="Formato de saída: table, json, text"
    ),
    raw: bool = typer.Option(False, "--raw", help="Saída sem formatação (JSON bruto)"),
):
    """
    Busca documentos na base de legislação.

    Exemplos:
        vectorgov search "O que é ETP?"
        vectorgov search "pesquisa de preços" --top-k 10
        vectorgov search "licitação" --mode precise --output json
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

    # Executa busca
    try:
        from vectorgov import VectorGov

        if not raw:
            console.print(f"Buscando: [cyan]{query}[/cyan]", style="dim")

        vg = VectorGov(api_key=api_key)
        results = vg.search(query, top_k=top_k, mode=mode, use_cache=use_cache)

        # Formata saída
        if raw:
            # JSON bruto para pipes
            data = {
                "query": query,
                "total": results.total,
                "cached": results.cached,
                "latency_ms": results.latency_ms,
                "query_id": results.query_id,
                "hits": [
                    {
                        "text": h.text,
                        "article_number": h.article_number,
                        "document_id": h.document_id,
                        "score": h.score,
                    }
                    for h in results.hits
                ]
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            format_search_results(console, results, output, query)

    except Exception as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)
