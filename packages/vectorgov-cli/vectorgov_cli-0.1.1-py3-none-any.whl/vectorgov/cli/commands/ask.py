"""
Comando de perguntas do CLI VectorGov.

Este comando busca contexto relevante e prepara para uso com LLMs.
O usuário deve usar seu próprio LLM (OpenAI, Anthropic, Google, etc).
"""

import json
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

from ..utils.config import ConfigManager
from ..utils.output import OutputFormat

app = typer.Typer()
console = Console()
config_manager = ConfigManager()


@app.callback(invoke_without_command=True)
def ask(
    query: str = typer.Argument(..., help="Pergunta em linguagem natural"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Número de chunks para contexto"),
    mode: str = typer.Option(
        "balanced",
        "--mode", "-m",
        help="Modo de busca: fast, balanced, precise"
    ),
    output: OutputFormat = typer.Option(
        OutputFormat.text,
        "--output", "-o",
        help="Formato de saída: text, json, messages"
    ),
    raw: bool = typer.Option(False, "--raw", help="Saída sem formatação (JSON bruto)"),
    show_code: bool = typer.Option(False, "--code", help="Mostrar código de exemplo para LLM"),
):
    """
    Busca contexto relevante para responder uma pergunta.

    O VectorGov retorna os chunks mais relevantes da legislação.
    Use os métodos to_messages() ou to_context() para integrar com seu LLM.

    Exemplos:
        vectorgov ask "O que é ETP?"
        vectorgov ask "Quando o ETP pode ser dispensado?" --mode precise
        vectorgov ask "critérios de julgamento" --output messages
        vectorgov ask "O que é ETP?" --code  # Mostra código de exemplo
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
            console.print(f"Buscando contexto para: [cyan]{query}[/cyan]", style="dim")

        vg = VectorGov(api_key=api_key)
        results = vg.search(query, top_k=top_k, mode=mode)

        # Formata saída
        if raw:
            # JSON bruto para pipes
            messages = results.to_messages(query)
            data = {
                "query": query,
                "total": results.total,
                "cached": results.cached,
                "latency_ms": results.latency_ms,
                "query_id": results.query_id,
                "messages": messages,
                "context": results.to_context(),
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))

        elif output == OutputFormat.json or str(output) == "messages":
            # Formato messages para usar com LLMs
            messages = results.to_messages(query)
            data = {
                "messages": messages,
                "metadata": {
                    "query": query,
                    "total": results.total,
                    "query_id": results.query_id,
                }
            }
            console.print_json(json.dumps(data, ensure_ascii=False))

        else:  # text
            # Mostra contexto formatado
            console.print()

            # Info da busca
            cache_str = "[green]✓ Cache[/green]" if results.cached else "[dim]Sem cache[/dim]"
            console.print(f"Encontrados: [cyan]{results.total}[/cyan] chunks | "
                         f"Latência: [cyan]{results.latency_ms}ms[/cyan] | {cache_str}")
            console.print()

            # Mostra cada hit
            for i, hit in enumerate(results.hits, 1):
                title = f"[bold]#{i}[/bold] Art. {hit.article_number} ({hit.document_id})"
                console.print(Panel(
                    hit.text[:500] + ("..." if len(hit.text) > 500 else ""),
                    title=title,
                    border_style="blue"
                ))
                console.print()

            # Query ID para feedback
            console.print(f"[dim]Query ID: {results.query_id}[/dim]")
            console.print("[dim]Use 'vectorgov feedback <query_id> --like' para avaliar[/dim]")

            # Mostra código de exemplo se solicitado
            if show_code:
                console.print()
                console.print("[bold yellow]Código de exemplo para usar com LLM:[/bold yellow]")
                code = f'''from vectorgov import VectorGov
from openai import OpenAI  # ou anthropic, google-generativeai, etc.

vg = VectorGov(api_key="vg_xxx")
openai = OpenAI()

results = vg.search("{query}", top_k={top_k})

# Usar com OpenAI
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=results.to_messages("{query}")
)
print(response.choices[0].message.content)

# Ou usar contexto diretamente
context = results.to_context()
'''
                console.print(Syntax(code, "python", theme="monokai"))

    except Exception as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)
