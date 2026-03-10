#!/usr/bin/env python3
"""
Serveur Webhook dédié Make (ex-Integromat)
==========================================
Lance ce serveur et configure Make pour appeler l'URL webhook.

Démarrage :
  python server_make.py
  python server_make.py --port 8081

Dans Make :
  Module "HTTP → Make a request"
  Method : POST
  URL    : http://ton-serveur:8081/webhook
  Body   : application/json

Make supporte aussi les webhooks entrants — utilisez le module "Webhooks → Custom webhook"
et configurez l'URL générée dans Make comme source, puis redirigez vers ce serveur.

Format de réponse Make-compatible :
  Tous les champs sont à plat (pas de nesting) pour être utilisables directement
  dans les modules Make suivants avec {{1.content}}, {{1.platform}}, etc.

Exemples de body Make :
  { "prompt": "Crée un post TikTok viral sur la mode été" }
  { "action": "campaign", "topic": "lancement produit", "platforms": "tiktok,instagram", "goal": "ventes" }
  { "action": "calendar", "topic": "restaurant", "platforms": "instagram,facebook", "days": "7" }
  { "action": "script", "topic": "astuces cuisine", "platform": "tiktok", "duration": "30" }
  { "action": "hashtags", "topic": "fitness", "platform": "instagram", "count": "20" }
  { "action": "visual", "topic": "soldes été", "platform": "instagram", "style": "coloré" }
  { "action": "canva", "topic": "nouvelle collection", "format": "story_instagram" }
  { "action": "text", "topic": "produit", "platform": "tiktok", "tone": "humoristique" }

Note Make : Les valeurs numériques peuvent être passées en string ("7") ou en number (7).
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
    title="Agent Marketing IA — Make",
    description="Webhook pour intégrer l'agent de création de contenu dans Make (Integromat)",
    version="1.0.0",
)


def _get_agent():
    from agents.content_agent import run_agent
    return run_agent


# ─────────────────────────────────────────────
# Route principale Make
# ─────────────────────────────────────────────

@app.post("/webhook")
async def make_webhook(request: Request):
    """
    Point d'entrée principal pour Make.

    Make envoie les données en JSON (application/json) ou form-data.
    Ce serveur accepte les deux formats.

    Retourne un JSON à plat pour faciliter l'utilisation dans les modules Make :
    {{1.content}}, {{1.platform}}, {{1.tools_used}}, {{1.success}}, etc.
    """
    content_type = request.headers.get("content-type", "")

    # Accepter JSON ou form-data (Make peut envoyer les deux)
    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Corps JSON invalide")
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        body = dict(form)
    else:
        # Tenter JSON par défaut
        try:
            body = await request.json()
        except Exception:
            body = {}

    if not body:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Body vide ou format non reconnu",
                "formats_acceptes": ["application/json", "application/x-www-form-urlencoded"],
                "champs_requis": "'prompt' (texte libre) OU 'action' avec les paramètres associés",
            },
        )

    # Normaliser les types (Make peut envoyer des strings pour les nombres et listes)
    body = _normalize_make_body(body)

    prompt = _build_prompt_from_body(body)
    if not prompt:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Impossible de construire le prompt. Vérifiez les champs requis.",
                "body_recu": body,
                "exemples": _get_examples_make(),
            },
        )

    run_agent = _get_agent()
    result = run_agent(prompt, stream_output=False)

    tools_list = [t["tool"] for t in result["tools_used"]]

    # Réponse à plat — chaque champ est accessible directement dans Make
    # {{1.content}}, {{1.success}}, {{1.action}}, {{1.tools_used}}, etc.
    return JSONResponse({
        # Statut
        "success": True,
        "timestamp": datetime.utcnow().isoformat() + "Z",

        # Contenu généré — champ principal
        "content": result["response"],

        # Métadonnées utiles dans Make
        "action": body.get("action", "prompt_libre"),
        "topic": body.get("topic", body.get("prompt", "")),
        "platform": body.get("platform", body.get("platforms", "")),
        "tools_used": ", ".join(tools_list),
        "tools_count": str(len(tools_list)),

        # Champ prompt utilisé (pour debug dans Make)
        "prompt_used": prompt,

        # Champ erreur vide (pour les conditions Make)
        "error": "",
    })


@app.post("/webhook/error-handler")
async def make_webhook_with_error(request: Request):
    """
    Version avec gestion d'erreur explicite pour Make.
    Retourne toujours un 200 avec success=false en cas d'erreur
    (utile si Make ne gère pas bien les codes HTTP d'erreur).
    """
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
        else:
            form = await request.form()
            body = dict(form)

        body = _normalize_make_body(body)
        prompt = _build_prompt_from_body(body)

        if not prompt:
            return JSONResponse({
                "success": False,
                "error": "Champ 'prompt' ou 'action' requis",
                "content": "",
                "tools_used": "",
                "tools_count": "0",
            })

        run_agent = _get_agent()
        result = run_agent(prompt, stream_output=False)
        tools_list = [t["tool"] for t in result["tools_used"]]

        return JSONResponse({
            "success": True,
            "content": result["response"],
            "action": body.get("action", "prompt_libre"),
            "topic": body.get("topic", ""),
            "platform": body.get("platform", ""),
            "tools_used": ", ".join(tools_list),
            "tools_count": str(len(tools_list)),
            "error": "",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "content": "",
            "tools_used": "",
            "tools_count": "0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })


# ─────────────────────────────────────────────
# Routes utilitaires
# ─────────────────────────────────────────────

@app.get("/health")
async def health():
    api_ok = bool(os.getenv("ANTHROPIC_API_KEY"))
    return {
        "status": "ok" if api_ok else "warning",
        "anthropic_key": "configurée" if api_ok else "manquante",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "server": "make webhook",
        "endpoints": {
            "POST /webhook": "Point d'entrée Make principal",
            "POST /webhook/error-handler": "Variante sans erreurs HTTP (toujours 200)",
            "GET /health": "Statut",
            "GET /tools": "Outils disponibles",
            "GET /examples": "Exemples Make",
        },
    }


@app.get("/tools")
async def list_tools():
    from tools.content_tools import TOOLS
    return {
        "count": len(TOOLS),
        "tools": [
            {
                "name": t["name"],
                "description": t["description"][:100] + "...",
                "required_params": t["input_schema"].get("required", []),
            }
            for t in TOOLS
        ],
    }


@app.get("/examples")
async def show_examples():
    return {
        "description": "Exemples de configuration pour Make (HTTP → Make a request)",
        "url": "POST http://localhost:8081/webhook",
        "content_type": "application/json",
        "note": "Dans Make, les valeurs peuvent être string ou number (les deux fonctionnent)",
        "examples": _get_examples_make(),
    }


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _normalize_make_body(body: dict) -> dict:
    """
    Normalise le body Make : convertit les strings en types natifs.
    Make peut envoyer les nombres et listes comme strings.
    """
    normalized = {}
    for key, value in body.items():
        if isinstance(value, str):
            # Convertir les entiers
            if value.isdigit():
                normalized[key] = int(value)
            # Convertir les listes séparées par virgules
            elif "," in value and key in ("platforms",):
                normalized[key] = [v.strip() for v in value.split(",")]
            else:
                normalized[key] = value
        else:
            normalized[key] = value
    return normalized


def _build_prompt_from_body(body: dict) -> str | None:
    """Même logique que n8n mais avec support des formats Make."""

    if "prompt" in body:
        return str(body["prompt"])

    action = body.get("action", "").lower()

    if action == "campaign":
        topic = body.get("topic", "")
        brand = body.get("brand", body.get("brand_name", "Ma Marque"))
        platforms = body.get("platforms", ["tiktok", "instagram"])
        if isinstance(platforms, str):
            platforms = [p.strip() for p in platforms.split(",")]
        goal = body.get("goal", body.get("campaign_goal", "engagement"))
        audience = body.get("audience", body.get("target_audience", "audience générale"))
        if not topic:
            return None
        return (
            f"Génère une campagne de contenu COMPLÈTE pour '{brand}' autour de '{topic}'. "
            f"Plateformes : {', '.join(platforms)}. Objectif : {goal}. Audience : {audience}."
        )

    elif action == "calendar":
        topic = body.get("topic", "")
        platforms = body.get("platforms", ["instagram"])
        if isinstance(platforms, str):
            platforms = [p.strip() for p in platforms.split(",")]
        days = int(body.get("days", 7))
        posts = int(body.get("posts_per_day", body.get("posts", 1)))
        if not topic:
            return None
        return (
            f"Crée un calendrier éditorial de {days} jours pour '{topic}' "
            f"sur {', '.join(platforms)}, {posts} post(s) par jour."
        )

    elif action == "script":
        topic = body.get("topic", "")
        platform = body.get("platform", "tiktok")
        duration = int(body.get("duration", body.get("duration_seconds", 30)))
        fmt = body.get("format", body.get("video_format", "éducatif"))
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
        count = int(body.get("count", 20))
        niche = body.get("niche", "")
        if not topic:
            return None
        niche_str = f" dans la niche '{niche}'" if niche else ""
        return f"Génère {count} hashtags {platform} pour '{topic}'{niche_str}."

    elif action == "visual":
        topic = body.get("topic", "")
        platform = body.get("platform", "instagram")
        style = body.get("style", "moderne")
        colors = body.get("brand_colors", body.get("colors", ""))
        if not topic:
            return None
        colors_str = f" Couleurs : {colors}." if colors else ""
        return (
            f"Génère un brief visuel et un prompt Midjourney/DALL-E pour "
            f"{platform}, sujet : '{topic}', style : {style}.{colors_str}"
        )

    elif action == "canva":
        topic = body.get("topic", "")
        fmt = body.get("format", body.get("canva_format", "post_instagram"))
        brand = body.get("brand", body.get("brand_name", "Ma Marque"))
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
        lang = body.get("language", body.get("lang", "français"))
        if not topic:
            return None
        return (
            f"Rédige un texte optimisé pour {platform} sur '{topic}', "
            f"ton : {tone}, langue : {lang}."
        )

    return None


def _get_examples_make() -> list:
    return [
        {
            "label": "Texte libre",
            "body": {"prompt": "Crée un post TikTok viral sur les tendances mode été 2025"},
            "make_fields": {"content": "{{1.content}}"},
        },
        {
            "label": "Campagne complète",
            "body": {
                "action": "campaign",
                "topic": "lancement nouveau parfum",
                "brand": "Mon Parfum",
                "platforms": "tiktok,instagram,facebook",
                "goal": "ventes",
                "audience": "femmes 25-40 ans",
            },
            "make_fields": {"content": "{{1.content}}", "action": "{{1.action}}"},
        },
        {
            "label": "Calendrier 7 jours",
            "body": {
                "action": "calendar",
                "topic": "restaurant gastronomique",
                "platforms": "instagram,facebook",
                "days": 7,
                "posts_per_day": 2,
            },
        },
        {
            "label": "Script TikTok",
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
            "label": "Visuel Midjourney",
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
            "label": "Texte LinkedIn",
            "body": {
                "action": "text",
                "topic": "lancement application mobile",
                "platform": "linkedin",
                "tone": "professionnel",
                "language": "français",
            },
        },
    ]


# ─────────────────────────────────────────────
# Point d'entrée
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serveur webhook Make — Agent Marketing IA")
    parser.add_argument("--port", type=int, default=8081, help="Port d'écoute (défaut: 8081)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Adresse d'écoute")
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY manquante. Ajoutez-la dans le fichier .env")
        sys.exit(1)

    print(f"""
╔══════════════════════════════════════════════════════════╗
║     🔗 SERVEUR WEBHOOK MAKE — Agent Marketing IA        ║
╚══════════════════════════════════════════════════════════╝

✅ Serveur démarré sur http://{args.host}:{args.port}

Dans Make, configurez un module "HTTP → Make a request" :
  Method       : POST
  URL          : http://localhost:{args.port}/webhook
  Body type    : application/json
  Body content : voir /examples

Champs disponibles dans Make après l'appel :
  {{{{1.content}}}}      → Contenu généré
  {{{{1.success}}}}      → true / false
  {{{{1.action}}}}       → Action exécutée
  {{{{1.tools_used}}}}   → Outils utilisés
  {{{{1.error}}}}        → Message d'erreur (vide si succès)

Endpoints :
  POST http://localhost:{args.port}/webhook                ← Principal
  POST http://localhost:{args.port}/webhook/error-handler  ← Toujours 200 (sans erreurs HTTP)
  GET  http://localhost:{args.port}/health                 ← Statut
  GET  http://localhost:{args.port}/examples               ← Exemples Make
""")

    uvicorn.run(app, host=args.host, port=args.port)
