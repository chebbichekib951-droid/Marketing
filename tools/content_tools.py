"""
Outils de création de contenu pour l'agent marketing.
Chaque outil génère un type de contenu spécifique à une plateforme ou un format.
"""

import json
from typing import Any

# ─────────────────────────────────────────────
# Définitions des outils (schémas JSON pour Claude)
# ─────────────────────────────────────────────

TOOLS = [
    {
        "name": "generate_platform_text",
        "description": (
            "Génère un texte optimisé pour une plateforme sociale spécifique "
            "(TikTok, Instagram, Facebook, LinkedIn, Twitter/X, YouTube). "
            "Adapte le ton, la longueur et le style à chaque réseau."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["tiktok", "instagram", "facebook", "linkedin", "twitter", "youtube"],
                    "description": "La plateforme cible.",
                },
                "topic": {
                    "type": "string",
                    "description": "Le sujet ou l'idée principale du contenu.",
                },
                "tone": {
                    "type": "string",
                    "enum": ["professionnel", "décontracté", "humoristique", "inspirant", "éducatif"],
                    "description": "Le ton du message.",
                },
                "language": {
                    "type": "string",
                    "description": "La langue du contenu (ex: français, anglais).",
                    "default": "français",
                },
            },
            "required": ["platform", "topic", "tone"],
        },
    },
    {
        "name": "generate_hashtags",
        "description": (
            "Génère des hashtags pertinents et tendance pour une plateforme donnée. "
            "Mélange hashtags populaires, de niche et de marque pour maximiser la portée."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["tiktok", "instagram", "facebook", "linkedin", "twitter", "youtube"],
                    "description": "La plateforme cible.",
                },
                "topic": {
                    "type": "string",
                    "description": "Le sujet du contenu.",
                },
                "count": {
                    "type": "integer",
                    "description": "Nombre de hashtags à générer (défaut: 15).",
                    "default": 15,
                },
                "niche": {
                    "type": "string",
                    "description": "Le secteur ou la niche (ex: mode, fitness, tech, cuisine).",
                },
            },
            "required": ["platform", "topic"],
        },
    },
    {
        "name": "generate_visual_prompt",
        "description": (
            "Génère un brief visuel détaillé et un prompt prêt à utiliser dans Canva, "
            "DALL-E, Midjourney ou Stable Diffusion pour créer des visuels percutants."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["tiktok", "instagram", "instagram_story", "facebook", "linkedin", "youtube_thumbnail", "canva"],
                    "description": "La plateforme ou le format visuel cible.",
                },
                "topic": {
                    "type": "string",
                    "description": "Le sujet ou le message du visuel.",
                },
                "style": {
                    "type": "string",
                    "enum": ["moderne", "minimaliste", "coloré", "professionnel", "lifestyle", "illustratif", "photo-réaliste"],
                    "description": "Le style visuel souhaité.",
                },
                "brand_colors": {
                    "type": "string",
                    "description": "Les couleurs de marque (ex: '#FF5733, #2C3E50') ou nom de palette.",
                },
            },
            "required": ["platform", "topic", "style"],
        },
    },
    {
        "name": "generate_video_script",
        "description": (
            "Génère un script complet pour une vidéo TikTok, Reels Instagram ou YouTube Shorts. "
            "Inclut le hook d'accroche, le développement, l'appel à l'action et les indications de tournage."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["tiktok", "instagram_reels", "youtube_shorts"],
                    "description": "La plateforme vidéo cible.",
                },
                "topic": {
                    "type": "string",
                    "description": "Le sujet de la vidéo.",
                },
                "duration_seconds": {
                    "type": "integer",
                    "description": "Durée cible en secondes (15, 30, 60).",
                    "default": 30,
                },
                "format": {
                    "type": "string",
                    "enum": ["tutoriel", "storytelling", "tendance", "challenge", "éducatif", "divertissement", "produit"],
                    "description": "Le format narratif de la vidéo.",
                },
                "cta": {
                    "type": "string",
                    "description": "L'appel à l'action souhaité (ex: 'abonne-toi', 'achète maintenant', 'visite le lien en bio').",
                },
            },
            "required": ["platform", "topic", "format"],
        },
    },
    {
        "name": "create_content_calendar",
        "description": (
            "Crée un calendrier éditorial avec des idées de posts sur plusieurs jours. "
            "Planifie les thèmes, plateformes, formats et horaires de publication optimaux."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "brand_topic": {
                    "type": "string",
                    "description": "Le thème ou secteur principal de la marque/compte.",
                },
                "platforms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Liste des plateformes actives (ex: ['tiktok', 'instagram', 'linkedin']).",
                },
                "days": {
                    "type": "integer",
                    "description": "Nombre de jours à planifier (7 ou 30).",
                    "default": 7,
                },
                "posts_per_day": {
                    "type": "integer",
                    "description": "Nombre de posts par jour.",
                    "default": 1,
                },
                "content_mix": {
                    "type": "string",
                    "description": "Répartition souhaitée (ex: '50% éducatif, 30% divertissant, 20% promotionnel').",
                },
            },
            "required": ["brand_topic", "platforms"],
        },
    },
    {
        "name": "generate_canva_brief",
        "description": (
            "Génère un brief complet pour créer un design dans Canva. "
            "Inclut les dimensions, éléments visuels, textes, disposition et conseils de design."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "enum": [
                        "post_instagram",
                        "story_instagram",
                        "post_facebook",
                        "bannière_linkedin",
                        "miniature_youtube",
                        "post_tiktok",
                        "flyer",
                        "infographie",
                    ],
                    "description": "Le format du design Canva.",
                },
                "topic": {
                    "type": "string",
                    "description": "Le sujet ou message principal du design.",
                },
                "brand_name": {
                    "type": "string",
                    "description": "Le nom de la marque ou du compte.",
                },
                "style_keywords": {
                    "type": "string",
                    "description": "Mots-clés de style (ex: 'luxueux, sombre, doré').",
                },
            },
            "required": ["format", "topic"],
        },
    },
    {
        "name": "generate_full_campaign",
        "description": (
            "Génère une campagne de contenu complète autour d'un sujet : "
            "textes pour chaque plateforme, hashtags, brief visuel, script vidéo et planning. "
            "Utilise cet outil pour créer tout le contenu d'un coup."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_topic": {
                    "type": "string",
                    "description": "Le sujet central de la campagne.",
                },
                "brand_name": {
                    "type": "string",
                    "description": "Nom de la marque ou du créateur.",
                },
                "target_audience": {
                    "type": "string",
                    "description": "Description de l'audience cible.",
                },
                "platforms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Plateformes cibles pour la campagne.",
                },
                "campaign_goal": {
                    "type": "string",
                    "enum": ["notoriété", "engagement", "ventes", "abonnés", "trafic_site"],
                    "description": "L'objectif principal de la campagne.",
                },
            },
            "required": ["campaign_topic", "platforms", "campaign_goal"],
        },
    },
]


# ─────────────────────────────────────────────
# Exécuteurs d'outils (logique métier)
# ─────────────────────────────────────────────

def execute_tool(name: str, tool_input: dict[str, Any]) -> str:
    """Dispatch l'exécution vers le bon handler d'outil."""
    handlers = {
        "generate_platform_text": _handle_platform_text,
        "generate_hashtags": _handle_hashtags,
        "generate_visual_prompt": _handle_visual_prompt,
        "generate_video_script": _handle_video_script,
        "create_content_calendar": _handle_content_calendar,
        "generate_canva_brief": _handle_canva_brief,
        "generate_full_campaign": _handle_full_campaign,
    }
    handler = handlers.get(name)
    if handler is None:
        return json.dumps({"error": f"Outil inconnu : {name}"})
    return handler(tool_input)


def _handle_platform_text(args: dict) -> str:
    platform = args["platform"]
    topic = args["topic"]
    tone = args["tone"]
    language = args.get("language", "français")

    specs = {
        "tiktok": {"max_chars": 150, "style": "accrocheur, direct, émojis, tendances"},
        "instagram": {"max_chars": 2200, "style": "storytelling, émojis, paragraphes aérés"},
        "facebook": {"max_chars": 500, "style": "conversationnel, question d'engagement"},
        "linkedin": {"max_chars": 1300, "style": "professionnel, insights, valeur ajoutée"},
        "twitter": {"max_chars": 280, "style": "concis, impactant, accrocheur"},
        "youtube": {"max_chars": 1000, "style": "description SEO, mots-clés, liens"},
    }
    spec = specs.get(platform, {"max_chars": 300, "style": "général"})

    return json.dumps({
        "tool": "generate_platform_text",
        "platform": platform,
        "topic": topic,
        "tone": tone,
        "language": language,
        "specs": spec,
        "instruction": (
            f"Génère maintenant le texte complet pour {platform.upper()} sur le sujet : '{topic}'. "
            f"Ton : {tone}. Langue : {language}. "
            f"Style requis : {spec['style']}. Limite : {spec['max_chars']} caractères max. "
            "Inclus des émojis adaptés et un appel à l'action fort."
        ),
    }, ensure_ascii=False)


def _handle_hashtags(args: dict) -> str:
    platform = args["platform"]
    topic = args["topic"]
    count = args.get("count", 15)
    niche = args.get("niche", "général")

    hashtag_strategies = {
        "tiktok": "Mix viral : 3 méga (#fyp, #viral), 5 populaires, 5 niche, 2 de marque",
        "instagram": "Mix stratégique : petits (10K-100K) + moyens (100K-1M) + grands (>1M)",
        "linkedin": "5-10 hashtags professionnels et sectoriels",
        "twitter": "2-3 hashtags max, trending si possible",
        "facebook": "3-5 hashtags pertinents",
        "youtube": "Tags SEO : titre, variations, mots-clés longue traîne",
    }
    strategy = hashtag_strategies.get(platform, "hashtags pertinents")

    return json.dumps({
        "tool": "generate_hashtags",
        "platform": platform,
        "topic": topic,
        "niche": niche,
        "count": count,
        "strategy": strategy,
        "instruction": (
            f"Génère {count} hashtags pour {platform.upper()} sur '{topic}' (niche: {niche}). "
            f"Stratégie : {strategy}. "
            "Classe-les par catégorie (viral/tendance, populaire, niche, marque). "
            "Indique le volume estimé pour chaque hashtag."
        ),
    }, ensure_ascii=False)


def _handle_visual_prompt(args: dict) -> str:
    platform = args["platform"]
    topic = args["topic"]
    style = args["style"]
    brand_colors = args.get("brand_colors", "non spécifié")

    dimensions = {
        "tiktok": "1080x1920px (9:16)",
        "instagram": "1080x1080px (1:1) ou 1080x1350px (4:5)",
        "instagram_story": "1080x1920px (9:16)",
        "facebook": "1200x630px (1.91:1)",
        "linkedin": "1200x627px (1.91:1)",
        "youtube_thumbnail": "1280x720px (16:9)",
        "canva": "Format personnalisé",
    }
    dim = dimensions.get(platform, "1080x1080px")

    return json.dumps({
        "tool": "generate_visual_prompt",
        "platform": platform,
        "dimensions": dim,
        "topic": topic,
        "style": style,
        "brand_colors": brand_colors,
        "instruction": (
            f"Génère un brief visuel complet ET un prompt Canva/DALL-E/Midjourney pour : "
            f"Plateforme: {platform} ({dim}), Sujet: '{topic}', Style: {style}, "
            f"Couleurs: {brand_colors}. "
            "Inclus : 1) Description visuelle détaillée, 2) Prompt IA en anglais (Midjourney/DALL-E), "
            "3) Instructions Canva étape par étape, 4) Textes à superposer, 5) Conseils de composition."
        ),
    }, ensure_ascii=False)


def _handle_video_script(args: dict) -> str:
    platform = args["platform"]
    topic = args["topic"]
    duration = args.get("duration_seconds", 30)
    format_type = args["format"]
    cta = args.get("cta", "abonne-toi pour plus de contenu")

    return json.dumps({
        "tool": "generate_video_script",
        "platform": platform,
        "topic": topic,
        "duration_seconds": duration,
        "format": format_type,
        "cta": cta,
        "instruction": (
            f"Écris un script vidéo complet pour {platform.upper()} ({duration}s), "
            f"format '{format_type}', sujet : '{topic}'. "
            "Structure obligatoire : \n"
            "🎬 HOOK (3s) : phrase d'accroche irrésistible\n"
            "📖 DÉVELOPPEMENT : contenu principal avec indications de plan/transition\n"
            "💥 POINT CLÉ : le moment mémorable\n"
            "📣 CTA : appel à l'action → " + cta + "\n"
            "Ajoute aussi : indications de montage, effets sonores suggérés, "
            "textes à l'écran, expressions faciales clés."
        ),
    }, ensure_ascii=False)


def _handle_content_calendar(args: dict) -> str:
    brand_topic = args["brand_topic"]
    platforms = args["platforms"]
    days = args.get("days", 7)
    posts_per_day = args.get("posts_per_day", 1)
    content_mix = args.get("content_mix", "40% éducatif, 30% divertissant, 20% promotionnel, 10% UGC")

    return json.dumps({
        "tool": "create_content_calendar",
        "brand_topic": brand_topic,
        "platforms": platforms,
        "days": days,
        "posts_per_day": posts_per_day,
        "content_mix": content_mix,
        "instruction": (
            f"Crée un calendrier éditorial de {days} jours pour '{brand_topic}' "
            f"sur {', '.join(platforms).upper()}. "
            f"{posts_per_day} post(s)/jour. Mix : {content_mix}. "
            "Format tableau : Jour | Plateforme | Format | Sujet | Heure optimale | Thème | Objectif. "
            "Inclus aussi : thèmes récurrents hebdomadaires, idées de séries, moments forts à exploiter."
        ),
    }, ensure_ascii=False)


def _handle_canva_brief(args: dict) -> str:
    format_type = args["format"]
    topic = args["topic"]
    brand_name = args.get("brand_name", "Ma Marque")
    style_keywords = args.get("style_keywords", "moderne, professionnel")

    canva_dimensions = {
        "post_instagram": "1080 × 1080 px",
        "story_instagram": "1080 × 1920 px",
        "post_facebook": "1200 × 630 px",
        "bannière_linkedin": "1584 × 396 px",
        "miniature_youtube": "1280 × 720 px",
        "post_tiktok": "1080 × 1920 px",
        "flyer": "210 × 297 mm (A4)",
        "infographie": "800 × 2000 px",
    }
    dim = canva_dimensions.get(format_type, "1080 × 1080 px")

    return json.dumps({
        "tool": "generate_canva_brief",
        "format": format_type,
        "dimensions": dim,
        "topic": topic,
        "brand_name": brand_name,
        "style_keywords": style_keywords,
        "instruction": (
            f"Génère un brief Canva ultra-détaillé pour : "
            f"Format: {format_type} ({dim}), Sujet: '{topic}', "
            f"Marque: '{brand_name}', Style: {style_keywords}. "
            "Inclus : 1) Disposition des éléments (grille), 2) Hiérarchie typographique, "
            "3) Palette de couleurs exacte (hex), 4) Images/icônes à rechercher, "
            "5) Texte titre + sous-titre + corps, 6) Logo placement, "
            "7) Effets et filtres recommandés dans Canva, "
            "8) Templates Canva similaires à chercher."
        ),
    }, ensure_ascii=False)


def _handle_full_campaign(args: dict) -> str:
    campaign_topic = args["campaign_topic"]
    brand_name = args.get("brand_name", "Ma Marque")
    target_audience = args.get("target_audience", "audience générale")
    platforms = args["platforms"]
    campaign_goal = args["campaign_goal"]

    return json.dumps({
        "tool": "generate_full_campaign",
        "campaign_topic": campaign_topic,
        "brand_name": brand_name,
        "target_audience": target_audience,
        "platforms": platforms,
        "campaign_goal": campaign_goal,
        "instruction": (
            f"Crée une campagne de contenu COMPLÈTE pour '{brand_name}' autour de '{campaign_topic}'. "
            f"Audience : {target_audience}. Objectif : {campaign_goal}. "
            f"Plateformes : {', '.join(platforms)}. \n\n"
            "Génère pour CHAQUE plateforme :\n"
            "✍️ Texte adapté avec émojis\n"
            "#️⃣ 10-15 hashtags optimisés\n"
            "🎨 Brief visuel + prompt IA\n"
            "🎬 Script vidéo (si applicable : TikTok/Reels)\n\n"
            "Puis génère :\n"
            "📅 Calendrier de publication sur 7 jours\n"
            "📊 KPIs à suivre pour mesurer le succès\n"
            "💡 3 variations A/B à tester"
        ),
    }, ensure_ascii=False)
