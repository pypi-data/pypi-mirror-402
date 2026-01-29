"""
Utilitários de formatação de saída do CLI VectorGov.
"""

import json
from enum import Enum
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel


class OutputFormat(str, Enum):
    """Formatos de saída suportados."""
    table = "table"
    json = "json"
    text = "text"
    markdown = "markdown"


def format_search_results(console: Console, results: Any, output_format: OutputFormat, query: str):
    """
    Formata e exibe resultados de busca.

    Args:
        console: Console Rich para output
        results: Objeto SearchResult da API
        output_format: Formato desejado
        query: Query original
    """
    if output_format == OutputFormat.json:
        data = {
            "query": query,
            "total": results.total,
            "cached": results.cached,
            "latency_ms": results.latency_ms,
            "query_id": results.query_id,
            "hits": [
                {
                    "text": h.text,
                    "article_number": getattr(h, "article_number", None),
                    "document_id": getattr(h, "document_id", None),
                    "score": h.score,
                }
                for h in results.hits
            ]
        }
        console.print_json(json.dumps(data, ensure_ascii=False))

    elif output_format == OutputFormat.table:
        # Cabeçalho
        console.print()
        console.print(f"[bold]Resultados para:[/bold] {query}")
        console.print(f"[dim]Total: {results.total} | Latência: {results.latency_ms:.0f}ms | Cache: {'Sim' if results.cached else 'Não'}[/dim]")
        console.print()

        # Tabela
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("#", justify="right", style="dim", width=3)
        table.add_column("Artigo", style="green", width=10)
        table.add_column("Texto", width=60)
        table.add_column("Score", justify="right", width=8)

        for i, hit in enumerate(results.hits, 1):
            article = getattr(hit, "article_number", "-") or "-"
            text = hit.text[:100] + "..." if len(hit.text) > 100 else hit.text
            text = text.replace("\n", " ")
            table.add_row(str(i), str(article), text, f"{hit.score:.3f}")

        console.print(table)

        # Footer
        console.print(f"\n[dim]Query ID: {results.query_id}[/dim]")
        console.print("[dim]Use 'vectorgov feedback <query_id> --like' para avaliar[/dim]")

    else:  # text
        console.print()
        console.print(Panel(f"[bold]{query}[/bold]", title="Busca", border_style="blue"))

        for i, hit in enumerate(results.hits, 1):
            article = getattr(hit, "article_number", None)
            header = f"[{i}] Art. {article}" if article else f"[{i}]"

            console.print(f"\n[bold cyan]{header}[/bold cyan] (score: {hit.score:.3f})")
            console.print(hit.text[:300] + "..." if len(hit.text) > 300 else hit.text)

        console.print(f"\n[dim]Total: {results.total} | Latência: {results.latency_ms:.0f}ms[/dim]")
        console.print(f"[dim]Query ID: {results.query_id}[/dim]")


def format_code_block(console: Console, code: str, language: str = "python"):
    """
    Formata e exibe um bloco de código.

    Args:
        console: Console Rich
        code: Código a exibir
        language: Linguagem para syntax highlighting
    """
    from rich.syntax import Syntax
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)
