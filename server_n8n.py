#!/usr/bin/env python3
"""
Serveur Webhook dédié n8n
=========================
Lance ce serveur et configure n8n pour appeler l'URL webhook.

Démarrage :
  python server_n8n.py
  python server_n8n.py --port 8080

Dans n8n :
  Nœud "HTTP Request" → Method: POST → URL: http://ton-serveur:8080/webhook
  Body: JSON avec le champ "prompt" (et optionnellement "action")

Exemples de body n8n :
  { "prompt": "Crée un post TikTok sur la mode été" }
  { "action": "campaign", "topic": "lancement produit", "platforms": ["tiktok","instagram"], "goal": "ventes" }
  { "action": "calendar", "topic": "restaurant", "platforms": ["instagram","facebook"], "days": 7 }
  { "action": "script", "topic": "astuces cuisine", "platform": "tiktok", "duration": 30 }
  { "action": "hashtags", "topic": "fitness", "platform": "instagram", "count": 20 }
  { "action": "visual", "topic": "soldes été", "platform": "instagram", "style": "coloré" }
  { "action": "canva", "topic": "nouvelle collection", "format": "story_instagram", "brand": "Ma Boutique" }
"""

import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

load_dotenv()

app = FastAPI(
    title="Agent Marketing IA — n8n",
    description="Webhook pour intégrer l'agent de création de contenu dans n8n",
    version="1.0.0",
)


def _get_agent():
    """Import lazy pour éviter les erreurs si ANTHROPIC_API_KEY n'est pas définie au chargement."""
    from agents.content_agent import run_agent
    return run_agent


# ─────────────────────────────────────────────
# Route principale n8n
# ─────────────────────────────────────────────

@app.post("/webhook")
async def n8n_webhook(request: Request):
    """
    Point d'entrée principal pour n8n.
    Accepte un JSON avec soit 'prompt' (texte libre) soit 'action' (structuré).

    Retourne un JSON compatible n8n avec tous les champs utilisables dans les nœuds suivants.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Corps JSON invalide")

    # Construire le prompt selon le type de requête
    prompt = _build_prompt_from_body(body)
    if not prompt:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Champ 'prompt' ou 'action' requis",
                "exemples": {
                    "texte_libre": {"prompt": "Crée un post TikTok viral sur la mode"},
                    "campagne": {
                        "action": "campaign",
                        "topic": "lancement produit",
                        "platforms": ["tiktok", "instagram"],
                        "goal": "ventes",
                        "brand": "Ma Marque",
                    },
                    "calendrier": {
                        "action": "calendar",
                        "topic": "restaurant",
                        "platforms": ["instagram", "facebook"],
                        "days": 7,
                    },
                    "script": {"action": "script", "topic": "astuces", "platform": "tiktok", "duration": 30},
                    "hashtags": {"action": "hashtags", "topic": "fitness", "platform": "instagram"},
                    "visuel": {"action": "visual", "topic": "soldes", "platform": "instagram", "style": "coloré"},
                    "canva": {"action": "canva", "topic": "collection", "format": "story_instagram"},
                    "texte": {"action": "text", "topic": "produit", "platform": "tiktok", "tone": "humoristique"},
                },
            },
        )

    run_agent = _get_agent()
    result = run_agent(prompt, stream_output=False)

    # Réponse optimisée pour n8n — tous les champs sont accessibles dans les nœuds suivants
    return JSONResponse({
        "success": True,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input": {
            "action": body.get("action", "prompt_libre"),
            "prompt_used": prompt,
            "raw_body": body,
        },
        "output": {
            "content": result["response"],
            "tools_used": [t["tool"] for t in result["tools_used"]],
            "tools_count": len(result["tools_used"]),
        },
        # Champs plats pour utilisation directe dans n8n Set/IF nodes
        "content": result["response"],
        "tools": ", ".join(t["tool"] for t in result["tools_used"]),
    })


# ─────────────────────────────────────────────
# Routes utilitaires
# ─────────────────────────────────────────────

@app.get("/health")
async def health():
    """Vérifie que le serveur est opérationnel."""
    api_ok = bool(os.getenv("ANTHROPIC_API_KEY"))
    return {
        "status": "ok" if api_ok else "warning",
        "anthropic_key": "configurée" if api_ok else "manquante — ajoutez ANTHROPIC_API_KEY dans .env",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "server": "n8n webhook",
        "endpoints": {
            "POST /webhook": "Point d'entrée principal n8n",
            "GET /health": "Statut serveur",
            "GET /tools": "Liste des outils disponibles",
            "GET /examples": "Exemples de payloads n8n",
        },
    }


@app.get("/tools")
async def list_tools():
    """Liste tous les outils disponibles et leurs paramètres."""
    from tools.content_tools import TOOLS
    return {
        "tools": [
            {
                "name": t["name"],
                "description": t["description"],
                "required_params": t["input_schema"].get("required", []),
                "all_params": list(t["input_schema"]["properties"].keys()),
            }
            for t in TOOLS
        ]
    }


@app.get("/examples")
async def show_examples():
    """Retourne des exemples de payloads JSON pour n8n."""
    return {
        "description": "Exemples de body JSON à envoyer dans le nœud HTTP Request de n8n",
        "url": "POST http://localhost:8080/webhook",
        "examples": [
            {
                "label": "Texte libre",
                "body": {"prompt": "Crée un post TikTok viral sur les tendances mode été 2025"},
            },
            {
                "label": "Campagne complète",
                "body": {
                    "action": "campaign",
                    "topic": "lancement nouveau parfum",
                    "brand": "Mon Parfum",
                    "platforms": ["tiktok", "instagram", "facebook"],
                    "goal": "ventes",
                    "audience": "femmes 25-40 ans",
                },
            },
            {
                "label": "Calendrier 7 jours",
                "body": {
                    "action": "calendar",
                    "topic": "restaurant gastronomique",
                    "platforms": ["instagram", "facebook"],
                    "days": 7,
                    "posts_per_day": 2,
                },
            },
            {
                "label": "Script TikTok 30s",
                "body": {
                    "action": "script",
                    "topic": "5 astuces pour mieux dormir",
                    "platform": "tiktok",
                    "format": "éducatif",
                    "duration": 30,
                    "cta": "abonne-toi pour plus de conseils",
                },
            },
            {
                "label": "Hashtags Instagram",
                "body": {
                    "action": "hashtags",
                    "topic": "sport et fitness",
                    "platform": "instagram",
                    "niche": "fitness",
                    "count": 25,
                },
            },
            {
                "label": "Prompt visuel Midjourney",
                "body": {
                    "action": "visual",
                    "topic": "soldes été collection mode",
                    "platform": "instagram",
                    "style": "coloré",
                    "brand_colors": "#FF5733, #FFC300",
                },
            },
            {
                "label": "Brief Canva",
                "body": {
                    "action": "canva",
                    "topic": "nouvelle collection automne",
                    "format": "story_instagram",
                    "brand": "Ma Boutique",
                    "style": "luxueux, sombre, doré",
                },
            },
            {
                "label": "Texte plateforme",
                "body": {
                    "action": "text",
                    "topic": "lancement application mobile",
                    "platform": "linkedin",
                    "tone": "professionnel",
                    "language": "français",
                },
            },
        ],
    }


# ─────────────────────────────────────────────
# Construction du prompt depuis le body
# ─────────────────────────────────────────────

def _build_prompt_from_body(body: dict) -> str | None:
    """Convertit le body JSON n8n en prompt pour l'agent."""

    # Mode texte libre
    if "prompt" in body:
        return str(body["prompt"])

    action = body.get("action", "").lower()

    if action == "campaign":
        topic = body.get("topic", "")
        brand = body.get("brand", "Ma Marque")
        platforms = body.get("platforms", ["tiktok", "instagram"])
        goal = body.get("goal", "engagement")
        audience = body.get("audience", "audience générale")
        if not topic:
            return None
        return (
            f"Génère une campagne de contenu COMPLÈTE pour '{brand}' autour de '{topic}'. "
            f"Plateformes : {', '.join(platforms)}. Objectif : {goal}. Audience : {audience}."
        )

    elif action == "calendar":
        topic = body.get("topic", "")
        platforms = body.get("platforms", ["instagram"])
        days = body.get("days", 7)
        posts = body.get("posts_per_day", 1)
        if not topic:
            return None
        return (
            f"Crée un calendrier éditorial de {days} jours pour '{topic}' "
            f"sur {', '.join(platforms)}, {posts} post(s) par jour."
        )

    elif action == "script":
        topic = body.get("topic", "")
        platform = body.get("platform", "tiktok")
        duration = body.get("duration", 30)
        fmt = body.get("format", "éducatif")
        cta = body.get("cta", "abonne-toi")
        if not topic:
            return None
        return (
            f"Génère un script vidéo {platform} de {duration}s, format '{fmt}', "
            f"sujet : '{topic}'. CTA : {cta}."
        )

    elif action == "hashtags":
        topic = body.get("topic", "")
        platform = body.get("platform", "instagram")
        count = body.get("count", 20)
        niche = body.get("niche", "")
        if not topic:
            return None
        niche_str = f" dans la niche '{niche}'" if niche else ""
        return f"Génère {count} hashtags {platform} pour '{topic}'{niche_str}."

    elif action == "visual":
        topic = body.get("topic", "")
        platform = body.get("platform", "instagram")
        style = body.get("style", "moderne")
        colors = body.get("brand_colors", "")
        if not topic:
            return None
        colors_str = f" Couleurs de marque : {colors}." if colors else ""
        return (
            f"Génère un brief visuel et un prompt Midjourney/DALL-E pour "
            f"{platform}, sujet : '{topic}', style : {style}.{colors_str}"
        )

    elif action == "canva":
        topic = body.get("topic", "")
        fmt = body.get("format", "post_instagram")
        brand = body.get("brand", "Ma Marque")
        style = body.get("style", "moderne")
        if not topic:
            return None
        return (
            f"Génère un brief Canva complet pour '{brand}', format : {fmt}, "
            f"sujet : '{topic}', style : {style}."
        )

    elif action == "text":
        topic = body.get("topic", "")
        platform = body.get("platform", "instagram")
        tone = body.get("tone", "décontracté")
        lang = body.get("language", "français")
        if not topic:
            return None
        return (
            f"Rédige un texte optimisé pour {platform} sur '{topic}', "
            f"ton : {tone}, langue : {lang}."
        )

    return None


# ─────────────────────────────────────────────
# Point d'entrée
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serveur webhook n8n — Agent Marketing IA")
    parser.add_argument("--port", type=int, default=8080, help="Port d'écoute (défaut: 8080)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Adresse d'écoute")
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY manquante. Ajoutez-la dans le fichier .env")
        sys.exit(1)

    print(f"""
╔══════════════════════════════════════════════════════════╗
║      🔗 SERVEUR WEBHOOK N8N — Agent Marketing IA        ║
╚══════════════════════════════════════════════════════════╝

✅ Serveur démarré sur http://{args.host}:{args.port}

Dans n8n, configurez un nœud "HTTP Request" :
  Method : POST
  URL    : http://localhost:{args.port}/webhook
  Body   : JSON (voir /examples pour les formats)

Endpoints :
  POST http://localhost:{args.port}/webhook   ← Point d'entrée principal
  GET  http://localhost:{args.port}/health    ← Statut
  GET  http://localhost:{args.port}/tools     ← Outils disponibles
  GET  http://localhost:{args.port}/examples  ← Exemples de payloads
""")

    uvicorn.run(app, host=args.host, port=args.port)
