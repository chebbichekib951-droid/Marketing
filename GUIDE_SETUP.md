# Guide de Configuration - Agent IA Compléments Alimentaires

## Ce que fait cet agent

| Fonctionnalité | Description |
|---|---|
| Post Instagram | Génère caption + hashtags + image → Publie automatiquement |
| Post TikTok | Génère script vidéo + miniature → Envoie par email |
| Article de Blog | Génère article SEO complet → Publie en brouillon Shopify |
| Image Produit | Génère une image HD professionnelle → Envoie par email |

---

## Clés API nécessaires

### 1. Claude (pour générer les textes)
- Aller sur : console.anthropic.com
- Créer un compte → "API Keys" → "Create Key"
- Copier la clé (commence par `sk-ant-...`)

### 2. OpenAI / DALL-E (pour générer les images)
- Aller sur : platform.openai.com
- Créer un compte → "API Keys" → "Create new secret key"
- Copier la clé (commence par `sk-...`)

### 3. Meta (pour poster sur Instagram)
- Avoir un **compte Instagram Business** ou Créateur
- Connecter Instagram à une **Page Facebook**
- Aller sur : developers.facebook.com
- Créer une app → Ajouter "Instagram Graph API"
- Générer un token d'accès longue durée (90 jours)
- Récupérer ton **Instagram User ID** (numérique)

### 4. Shopify (pour les articles de blog)
- Dans Shopify Admin : **Paramètres → Apps et canaux de vente → Développer des apps**
- Cliquer sur **"Créer une app"** → Donner un nom (ex: "Agent IA Blog")
- Dans l'app : **"Configuration de l'API Admin"** → Cocher `write_content` et `read_content`
- Installer l'app → Copier le **Token d'accès Admin API** (commence par `shpat_...`)
- Remplacer `VOTRE_SHOPIFY_ACCESS_TOKEN`
- Remplacer `VOTRE-STORE` par le sous-domaine de ta boutique (ex: `ma-boutique`)
- **Trouver ton Blog ID** : Dans Shopify Admin → Blog → l'ID est dans l'URL de la page
- Remplacer `VOTRE_BLOG_ID` par cet ID numérique

---

## Installation n8n

### Étape 1 - Importer le workflow
1. Ouvrir n8n
2. Cliquer sur **"+"** pour créer un workflow
3. Cliquer sur les **3 points** (⋮) en haut à droite
4. Choisir **"Import from File"**
5. Sélectionner le fichier `n8n_workflow_complement_alimentaire.json`

### Étape 2 - Remplacer les clés API
Chercher et remplacer dans chaque nœud HTTP :

| Texte à remplacer | Par |
|---|---|
| `VOTRE_CLE_API_CLAUDE` | Ta clé Claude API |
| `VOTRE_CLE_API_OPENAI` | Ta clé OpenAI API |
| `VOTRE_IG_USER_ID` | Ton Instagram User ID (numérique) |
| `VOTRE_META_ACCESS_TOKEN` | Ton Meta Access Token |
| `VOTRE-STORE.myshopify.com` | Ton URL Shopify |
| `VOTRE_SHOPIFY_ACCESS_TOKEN` | Ton token API Admin Shopify |
| `VOTRE_BLOG_ID` | L'ID de ton blog Shopify |

### Étape 3 - Activer le workflow
1. Cliquer sur **"Active"** (bouton en haut à droite)
2. Cliquer sur **"Test Workflow"** pour tester
3. Le formulaire s'ouvre → Remplir et valider

---

## Installation Make (anciennement Integromat)

### Étape 1 - Importer le blueprint
1. Ouvrir Make.com
2. Cliquer sur **"Create a new scenario"**
3. Cliquer sur les **3 points** (⋮) en bas à gauche
4. Choisir **"Import Blueprint"**
5. Sélectionner le fichier `make_blueprint_complement_alimentaire.json`

### Étape 2 - Configurer le Webhook
1. Cliquer sur le module **"Webhook"** (1er module)
2. Cliquer sur **"Add"** pour créer un nouveau webhook
3. Copier l'URL du webhook → C'est l'URL à appeler pour déclencher l'agent

### Étape 3 - Remplacer les clés API
Dans chaque module HTTP, remplacer les valeurs :

| Texte à remplacer | Par |
|---|---|
| `VOTRE_CLE_API_CLAUDE` | Ta clé Claude API |
| `VOTRE_CLE_API_OPENAI` | Ta clé OpenAI API |
| `VOTRE_IG_USER_ID` | Ton Instagram User ID |
| `VOTRE_META_ACCESS_TOKEN` | Ton Meta Access Token |
| `VOTRE-STORE.myshopify.com` | Ton URL Shopify |
| `VOTRE_SHOPIFY_ACCESS_TOKEN` | Ton token API Admin Shopify |
| `VOTRE_BLOG_ID` | L'ID de ton blog Shopify |
| `VOTRE_EMAIL@email.com` | Ton email pour recevoir les résultats |

### Étape 4 - Déclencher le scénario
Envoyer une requête POST au webhook avec ce format :
```json
{
  "type_contenu": "Post Instagram",
  "produit": "Whey Protéine Vanille",
  "ton": "Motivant et énergique",
  "infos": "Promotion -20% ce weekend"
}
```

---

## Comment utiliser l'agent

### Dans n8n
1. Aller sur l'URL du formulaire (n8n te donne une URL)
2. Remplir le formulaire :
   - **Type de contenu** : Instagram / TikTok / Blog / Image
   - **Produit** : nom du produit ou sujet
   - **Ton** : le style de communication
   - **Infos** : détails supplémentaires (optionnel)
3. Cliquer sur Envoyer → L'agent crée et publie automatiquement

### Dans Make
- Utiliser un module "Google Forms" ou "Typeform" en déclencheur
- Ou appeler le webhook directement via une autre automatisation

---

## Limitations importantes

| Limitation | Solution |
|---|---|
| TikTok : pas de publication directe de vidéo | L'agent génère le script + miniature et t'envoie tout par email |
| Images DALL-E : URL expire en 1h | Télécharger l'image immédiatement après génération |
| Meta Token : expire tous les 90 jours | Renouveler le token régulièrement sur developers.facebook.com |
| Shopify : article publié en brouillon | Vérifier et valider manuellement avant publication dans Shopify Admin |

---

## Coûts estimés par contenu créé

| Contenu | Claude | DALL-E | Total estimé |
|---|---|---|---|
| Post Instagram | ~0.02€ | ~0.04€ | ~0.06€ |
| Post TikTok | ~0.03€ | ~0.04€ | ~0.07€ |
| Article Blog | ~0.08€ | - | ~0.08€ |
| Image Produit | ~0.01€ | ~0.08€ (HD) | ~0.09€ |

---

## Support

En cas de problème :
- **n8n** : docs.n8n.io
- **Make** : make.com/help
- **Claude API** : docs.anthropic.com
- **Meta Graph API** : developers.facebook.com/docs/instagram-api
