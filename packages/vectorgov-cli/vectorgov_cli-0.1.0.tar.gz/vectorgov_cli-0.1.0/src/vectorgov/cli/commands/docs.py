"""
Comando de documentos do CLI VectorGov.
"""

import json
import typer
from rich.console import Console
from rich.table import Table

from ..utils.config import ConfigManager

app = typer.Typer(no_args_is_help=True)
console = Console()
config_manager = ConfigManager()


@app.command("list")
def list_docs(
    output: str = typer.Option("table", "--output", "-o", help="Formato: table, json"),
):
    """
    Lista documentos disponíveis na base.

    Exemplos:
        vectorgov docs list
        vectorgov docs list --output json
    """
    # Obtém API key
    api_key = config_manager.get("api_key")
    if not api_key:
        console.print("[red]Erro:[/red] API key não configurada.")
        console.print("  Use 'vectorgov auth login' para configurar.")
        raise typer.Exit(1)

    try:
        from vectorgov import VectorGov

        vg = VectorGov(api_key=api_key)
        docs = vg.list_documents()

        if output == "json":
            data = [
                {
                    "id": d.id,
                    "title": d.title,
                    "type": d.type,
                    "year": d.year,
                    "chunks": d.chunks_count,
                }
                for d in docs
            ]
            console.print_json(json.dumps(data, ensure_ascii=False))
        else:
            table = Table(title="Documentos Disponíveis")
            table.add_column("ID", style="cyan")
            table.add_column("Título")
            table.add_column("Tipo", style="green")
            table.add_column("Ano", justify="right")
            table.add_column("Chunks", justify="right")

            for d in docs:
                table.add_row(
                    d.id,
                    d.title[:50] + "..." if len(d.title) > 50 else d.title,
                    d.type,
                    str(d.year),
                    str(d.chunks_count),
                )

            console.print(table)
            console.print(f"\nTotal: {len(docs)} documentos")

    except Exception as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)


@app.command("info")
def doc_info(
    document_id: str = typer.Argument(..., help="ID do documento"),
):
    """
    Mostra informações detalhadas de um documento.

    Exemplos:
        vectorgov docs info LEI-14133-2021
        vectorgov docs info IN-58-2022
    """
    # Obtém API key
    api_key = config_manager.get("api_key")
    if not api_key:
        console.print("[red]Erro:[/red] API key não configurada.")
        console.print("  Use 'vectorgov auth login' para configurar.")
        raise typer.Exit(1)

    try:
        from vectorgov import VectorGov

        vg = VectorGov(api_key=api_key)
        doc = vg.get_document(document_id)

        console.print(f"\n[bold]{doc.title}[/bold]")
        console.print(f"ID: [cyan]{doc.id}[/cyan]")
        console.print(f"Tipo: [green]{doc.type}[/green]")
        console.print(f"Ano: {doc.year}")
        console.print(f"Chunks: {doc.chunks_count}")

        if hasattr(doc, 'description') and doc.description:
            console.print(f"\nDescrição: {doc.description}")

    except Exception as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)
