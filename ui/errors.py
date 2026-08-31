"""
Turn technical exceptions into clear, actionable French messages
for the Streamlit UI. Never shows a raw traceback to the end user.
"""

from typing import Tuple


def humanize_error(exc: Exception) -> Tuple[str, str, str]:
    """Return (title, detail, hint) in French for a given exception."""
    text = str(exc)
    low = text.lower()

    if "profile not found" in low or "not found for company" in low:
        return (
            "Profil d'entreprise introuvable",
            "Aucune fiche entreprise n'a été trouvée pour cet identifiant.",
            "Créez d'abord l'entreprise depuis le menu latéral, puis relancez l'analyse.",
        )

    if "existe déjà" in text:
        return (
            "Cette entreprise existe déjà",
            text,
            "Choisissez un identifiant différent ou sélectionnez l'entreprise existante dans le menu latéral.",
        )

    if "column mapping incomplete" in low or "required field" in low:
        return (
            "Fichier incompatible",
            "Certaines colonnes obligatoires n'ont pas pu être identifiées dans le fichier importé.",
            "Vérifiez que votre fichier contient bien les colonnes nécessaires "
            "(identifiant client / commande, etc.) puis réessayez.",
        )

    if "too many rejected rows" in low or "import aborted" in low:
        return (
            "Trop de lignes invalides",
            "Une trop grande partie du fichier n'a pas pu être importée car les données "
            "étaient incomplètes ou incorrectes.",
            "Corrigez le fichier source (valeurs manquantes ou mal formatées) et réessayez.",
        )

    if "csv has no header" in low:
        return (
            "Fichier vide ou mal formé",
            "Le fichier ne contient pas de ligne d'en-tête exploitable.",
            "Vérifiez que le fichier CSV possède bien une première ligne avec les noms de colonnes.",
        )

    if "file not found" in low:
        return (
            "Fichier introuvable",
            "Le fichier importé n'a pas pu être localisé sur le serveur.",
            "Réessayez l'import depuis le formulaire.",
        )

    if "onnx" in low or "sha256" in low or "corrupted download" in low:
        return (
            "Base de connaissances momentanément indisponible",
            "Le modèle utilisé pour rechercher les bonnes pratiques marketing n'a pas pu "
            "être téléchargé (connexion réseau instable ou fichier corrompu).",
            "Réessayez dans quelques instants. Si le problème persiste, vérifiez la connexion "
            "réseau du serveur.",
        )

    if "groq_api_key" in low or "api key" in low:
        return (
            "Assistant IA indisponible",
            "La clé d'accès au modèle de langage n'est pas configurée.",
            "Eleva continue de fonctionner en mode règles de secours ; contactez l'administrateur "
            "pour activer les recommandations enrichies par IA.",
        )

    # Generic fallback — still no raw traceback shown.
    return (
        "Une erreur est survenue",
        text if len(text) < 300 else "Le détail technique n'a pas pu être affiché.",
        "Si le problème persiste, vérifiez vos données ou contactez l'équipe technique.",
    )
