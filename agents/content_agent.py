"""
Agent principal de création de contenu.
Utilise Claude (claude-opus-4-6) avec des outils spécialisés pour orchestrer
la création de textes, visuels, scripts et calendriers pour les réseaux sociaux.
"""

import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from tools.content_tools import TOOLS, execute_tool

console = Console()

SYSTEM_PROMPT = """Tu es un expert en marketing digital et création de contenu pour les réseaux sociaux.
Tu maîtrises parfaitement TikTok, Instagram, Facebook, LinkedIn, YouTube et Canva.

Ton rôle :
- Créer du contenu viral, engageant et adapté à chaque plateforme
- Générer des visuels percutants (briefs Canva, prompts IA)
- Écrire des scripts TikTok/Reels qui accrochent dès les 3 premières secondes
- Planifier des stratégies de contenu cohérentes
- Optimiser pour les algorithmes de chaque réseau social

Utilise toujours les outils disponibles pour créer le contenu demandé.
Sois créatif, précis et orienté résultats. Réponds en français sauf indication contraire.
"""


def run_agent(user_prompt: str, stream_output: bool = True) -> dict:
    """
    Lance l'agent de création de contenu.

    Args:
        user_prompt: La demande de l'utilisateur.
        stream_output: Afficher la réponse en streaming dans la console.

    Returns:
        dict avec les champs 'response' (texte final) et 'tools_used' (liste des outils appelés).
    """
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": user_prompt}]
    tools_used = []
    final_response = ""

    if stream_output:
        console.print(Panel(
            f"[bold cyan]Requête :[/bold cyan] {user_prompt}",
            title="🚀 Agent Marketing IA",
            border_style="cyan",
        ))

    # Boucle agentique : continue jusqu'à ce que Claude n'appelle plus d'outil
    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8192,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Extraire le contenu texte de cette itération
        text_blocks = [b for b in response.content if b.type == "text"]
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        # Afficher le texte intermédiaire si présent
        if stream_output and text_blocks:
            for block in text_blocks:
                if block.text.strip():
                    console.print(Markdown(block.text))

        # Si Claude a terminé (pas d'appel d'outil), on sort
        if response.stop_reason == "end_turn" or not tool_use_blocks:
            if text_blocks:
                final_response = "\n".join(b.text for b in text_blocks)
            break

        # Ajouter la réponse de l'assistant à l'historique
        messages.append({"role": "assistant", "content": response.content})

        # Exécuter les outils et collecter les résultats
        tool_results = []
        for tool_block in tool_use_blocks:
            tool_name = tool_block.name
            tool_input = tool_block.input

            if stream_output:
                console.print(f"\n[bold yellow]🔧 Outil appelé :[/bold yellow] [cyan]{tool_name}[/cyan]")

            # Exécuter l'outil
            result = execute_tool(tool_name, tool_input)
            tools_used.append({"tool": tool_name, "input": tool_input})

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_block.id,
                "content": result,
            })

        # Ajouter les résultats des outils à l'historique
        messages.append({"role": "user", "content": tool_results})

    return {
        "response": final_response,
        "tools_used": tools_used,
    }
