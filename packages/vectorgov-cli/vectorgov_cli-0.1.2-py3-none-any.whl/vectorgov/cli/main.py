"""
Ponto de entrada principal do CLI VectorGov.
"""

import typer
from rich.console import Console

from .commands import auth, search, ask, feedback, docs, config, tokens

# Console para output formatado
console = Console()

# App principal
app = typer.Typer(
    name="vectorgov",
    help="CLI para a API VectorGov - Busca semântica em legislação brasileira",
    add_completion=True,
    no_args_is_help=True,
)

# Registra subcomandos
app.add_typer(auth.app, name="auth", help="Autenticação e gerenciamento de credenciais")
app.add_typer(search.app, name="search", help="Buscar documentos na base de legislação")
app.add_typer(ask.app, name="ask", help="Fazer perguntas com resposta de IA")
app.add_typer(feedback.app, name="feedback", help="Enviar feedback sobre respostas")
app.add_typer(docs.app, name="docs", help="Listar e consultar documentos disponíveis")
app.add_typer(config.app, name="config", help="Gerenciar configurações")
app.add_typer(tokens.app, name="tokens", help="Estimar tokens para planejamento de uso de LLM")


@app.command()
def version():
    """Mostra a versão do CLI."""
    from . import __version__
    console.print(f"vectorgov-cli versão {__version__}")


@app.callback()
def callback():
    """
    VectorGov CLI - Busca semântica em legislação brasileira.

    Use 'vectorgov COMANDO --help' para mais informações sobre cada comando.
    """
    pass


def main():
    """Função principal executada pelo entry point."""
    app()


if __name__ == "__main__":
    main()
