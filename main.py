#!/usr/bin/env python3
"""
Agent IA de Création de Contenu Marketing
==========================================
Lance l'agent en mode CLI ou en mode serveur webhook (n8n / Make).

Usage:
  python main.py                         → mode interactif CLI
  python main.py --server                → mode serveur webhook (port 8080)
  python main.py --prompt "..."          → mode commande unique
  python main.py --server --port 9000    → serveur sur port custom
"""

import os
import sys
import typer
from typing import Optional
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

load_dotenv()

app = typer.Typer(help="Agent IA de création de contenu pour les réseaux sociaux.")
console = Console()

BANNER = """
╔══════════════════════════════════════════════════════════╗
║         🎯 AGENT IA MARKETING - CRÉATION CONTENU        ║
║   TikTok • Instagram • Facebook • LinkedIn • Canva      ║
╚══════════════════════════════════════════════════════════╝
"""

EXEMPLES = """
📝 Exemples de commandes :

  • "Crée un post TikTok viral sur les tendances mode été 2025"
  • "Génère une campagne complète pour lancer mon produit de skincare sur Instagram et TikTok"
  • "Écris un script de 30 secondes pour TikTok sur les astuces productivité"
  • "Planifie mon calendrier de contenu pour 7 jours pour un restaurant"
  • "Crée un brief Canva pour une story Instagram sur ma nouvelle collection"
  • "Génère 20 hashtags Instagram pour la niche fitness"
  • "Crée un visuel prompt Midjourney pour un post LinkedIn tech"
"""


def _check_api_key():
    """Vérifie que la clé API est configurée."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print(
            Panel(
                "[red]❌ ANTHROPIC_API_KEY non trouvée.[/red]\n\n"
                "1. Copiez [cyan].env.example[/cyan] vers [cyan].env[/cyan]\n"
                "2. Ajoutez votre clé API Anthropic\n"
                "   Obtenez-la sur : [link=https://console.anthropic.com]console.anthropic.com[/link]",
                title="Configuration requise",
                border_style="red",
            )
        )
        sys.exit(1)


@app.command()
def cli(
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Prompt direct (mode non-interactif)"),
    server: bool = typer.Option(False, "--server", "-s", help="Lancer le serveur webhook (n8n/Make)"),
    port: int = typer.Option(8080, "--port", help="Port du serveur webhook"),
    host: str = typer.Option("0.0.0.0", "--host", help="Adresse d'écoute du serveur"),
):
    """Agent IA de création de contenu pour les réseaux sociaux."""
    _check_api_key()

    if server:
        # Mode serveur webhook pour n8n / Make
        _run_server(host=host, port=port)
    elif prompt:
        # Mode commande unique
        _run_single(prompt)
    else:
        # Mode interactif CLI
        _run_interactive()


def _run_single(prompt: str):
    """Exécute une seule requête et affiche le résultat."""
    from agents.content_agent import run_agent
    console.print(BANNER, style="bold cyan")
    result = run_agent(prompt, stream_output=True)
    if result["tools_used"]:
        console.print(f"\n[dim]Outils utilisés : {', '.join(t['tool'] for t in result['tools_used'])}[/dim]")


def _run_interactive():
    """Lance le mode interactif CLI."""
    from agents.content_agent import run_agent

    console.print(BANNER, style="bold cyan")
    console.print(EXEMPLES, style="dim")
    console.print("[bold green]Tapez 'quitter' ou 'exit' pour arrêter.[/bold green]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]🎯 Votre demande[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Au revoir ! 👋[/yellow]")
            break

        if user_input.lower() in ("quitter", "exit", "quit", "q"):
            console.print("[yellow]Au revoir ! 👋[/yellow]")
            break

        if not user_input.strip():
            continue

        result = run_agent(user_input, stream_output=True)
        if result["tools_used"]:
            tools_names = ", ".join(t["tool"] for t in result["tools_used"])
            console.print(f"\n[dim italic]Outils utilisés : {tools_names}[/dim italic]")
        console.print("\n" + "─" * 60 + "\n")


def _run_server(host: str, port: int):
    """Lance le serveur HTTP pour les webhooks n8n et Make."""
    try:
        from server import create_app
    except ImportError:
        console.print("[red]Erreur : impossible de charger le serveur. Vérifiez server.py.[/red]")
        sys.exit(1)

    import uvicorn
    console.print(Panel(
        f"[bold green]✅ Serveur webhook démarré[/bold green]\n\n"
        f"URL locale : [cyan]http://localhost:{port}[/cyan]\n\n"
        f"[bold]Endpoints disponibles :[/bold]\n"
        f"  POST [cyan]/webhook/n8n[/cyan]      → Pour n8n\n"
        f"  POST [cyan]/webhook/make[/cyan]     → Pour Make (Integromat)\n"
        f"  POST [cyan]/api/generate[/cyan]     → API générique\n"
        f"  GET  [cyan]/health[/cyan]           → Statut du serveur\n"
        f"  GET  [cyan]/api/tools[/cyan]        → Liste des outils disponibles",
        title="🌐 Serveur Webhook IA Marketing",
        border_style="green",
    ))
    app_instance = create_app()
    uvicorn.run(app_instance, host=host, port=port)


if __name__ == "__main__":
    app()
