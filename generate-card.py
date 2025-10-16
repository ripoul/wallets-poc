# google_wallet_multi_sites.py
# Exemple de base — adapter les champs aux besoins

from google.oauth2 import service_account
from googleapiclient.discovery import build
import time
import jwt  # pyjwt
import json
import dotenv
import os

dotenv.load_dotenv()

SERVICE_ACCOUNT_FILE = "service-account.json"
SCOPES = ["https://www.googleapis.com/auth/wallet_object.issuer"]
ISSUER_ID = os.getenv("ISSUER_ID")  # Remplacer par ton issuer ID
SERVICE_ACCOUNT_EMAIL = os.getenv("SERVICE_ACCOUNT_EMAIL")

# config multi-sites : id de classe souhaité par site, nom, couleur, ...
SITES = [
    {
        "site_key": "boutique-A",
        "class_id": f"{ISSUER_ID}.loyalty_boutiqueA",
        "site_name": "Boutique A",
        "logo_uri": "https://img.freepik.com/vecteurs-libre/vecteur-conception-degrade-colore-oiseau_343694-2506.jpg?semt=ais_hybrid&w=740&q=80",
    },
    {
        "site_key": "boutique-B",
        "class_id": f"{ISSUER_ID}.loyalty_boutiqueB",
        "site_name": "Boutique B",
        "logo_uri": "https://img.lovepik.com/element/45015/3146.png_860.png",
    },
]

def get_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("walletobjects", "v1", credentials=creds, cache_discovery=False)
    return service

def create_loyalty_class_if_missing(service, class_payload):
    try:
        # Essayer de récupérer la class (si existe)
        existing = service.loyaltyclass().get(resourceId=class_payload["id"]).execute()
        print("Classe exists:", class_payload["id"])
        #existing = service.loyaltyclass().patch(resourceId=class_payload["id"], body=class_payload).execute()
        return existing
    except Exception as e:
        # si n'existe pas -> créer
        print("Creating class:", class_payload["id"])
        created = service.loyaltyclass().insert(body=class_payload).execute()
        return created

def create_loyalty_object(service, object_payload):
    try:
        created = service.loyaltyobject().insert(body=object_payload).execute()
        return created
    except Exception as e:
        # Si l'objet existe déjà, on le récupère et on le met à jour (patch)
        if hasattr(e, "resp") and e.resp.status == 409 or "already exists" in str(e):
            print(f"Objet déjà existant: {object_payload['id']}, mise à jour...")
            # Patch uniquement les champs modifiables
            updated = service.loyaltyobject().patch(
                resourceId=object_payload["id"], body=object_payload
            ).execute()
            return updated
        else:
            print("Erreur création objet:", e)
            raise

def build_class_payload(site):
    """
    Construit le payload complet pour une LoyaltyClass Google Wallet.
    Inclut tous les champs requis et recommandés.
    """
    return {
        # ✅ Identifiant unique de la classe
        "id": site["class_id"],  # Format : {ISSUER_ID}.{nom_unique}

        # ✅ Nom du programme de fidélité (affiché sur la carte)
        "programName": f"{site['site_name']} Rewards",

        # ✅ Nom de l’émetteur (ton entreprise ou site)
        "issuerName": site["site_name"],

        # ✅ Nom du programme affiché dans le wallet
        "localizedProgramName": {
            "defaultValue": {
                "language": "fr",
                "value": f"Programme de fidélité {site['site_name']}"
            }
        },

        # ✅ Branding (logo, couleur, style)
        "logo": {
            "sourceUri": {"uri": site["logo_uri"]}
        },
        "hexBackgroundColor": "#4285F4",   # couleur principale (exemple : bleu Google)
        "heroImage": {  # image en haut de la carte (optionnelle mais recommandée)
            "sourceUri": {
                "uri": site.get("hero_image_uri", site["logo_uri"])
            }
        },

        # ✅ Points de contact
        "programLogo": {  # pour compatibilité avec anciennes versions
            "sourceUri": {"uri": site["logo_uri"]}
        },
        "homepageUri": {
            "uri": site.get("homepage_uri", "https://example.com"),
            "description": "Visitez notre boutique"
        },
        "termsAndConditionsUri": {
            "uri": site.get("terms_uri", "https://example.com/conditions")
        },
        "messages": [  # message de bienvenue
            {
                "header": "Bienvenue dans notre programme de fidélité !",
                "body": "Cumulez des points à chaque achat et profitez de récompenses exclusives.",
                "kind": "walletobjects#message"
            }
        ],

        # ✅ Informations sur le programme
        "rewardsTier": "Membre",
        "rewardsTierLabel": "Niveau",
        "reviewStatus": "underReview",  # "underReview" ou "approved" après validation Google

        # ✅ Configuration du barcode par défaut (si tu veux en générer pour tous les membres)
        "barcode": {
            "type": "qrCode",
            "value": "LOYALTY_DEFAULT",
            "alternateText": "Votre code fidélité"
        },

        # ✅ Champ dynamique pour les points
        "loyaltyPoints": {
            "label": "Points",
            "balanceType": "points"
        },

        # ✅ Format d’affichage du numéro de compte (personnalisable)
        "accountNameLabel": "Nom du client",
        "accountIdLabel": "Numéro de fidélité",

        # ✅ Localisation (si tu veux activer les notifications par proximité)
        "locations": [
            {
                "latitude": 48.8566,
                "longitude": 2.3522,
                "label": "Boutique principale"
            }
        ],

        # ✅ Liens supplémentaires (site, contact, promotions)
        "linksModuleData": {
            "uris": [
                {
                    "uri": site.get("homepage_uri", "https://example.com"),
                    "description": "Notre site",
                },
                {
                    "uri": site.get("contact_uri", "https://example.com/contact"),
                    "description": "Contactez-nous",
                }
            ]
        },

        # ✅ Templates d’affichage (optionnel mais utile pour personnaliser)
        "cardTitle": {
            "defaultValue": {"language": "fr", "value": site["site_name"]}
        },
        "header": {
            "defaultValue": {"language": "fr", "value": "Programme de fidélité"}
        },
        "localizedIssuerName": {
            "defaultValue": {
                "language": "fr",
                "value": site["site_name"]
            }
        },

        # ✅ Date de création (pour audit interne)
        "infoModuleData": {
            "labelValueRows": [
                {
                    "columns": [
                        {
                            "label": "Créé le",
                            "value": time.strftime("%d/%m/%Y")
                        }
                    ]
                }
            ]
        },

        # ✅ Type d’objet
        "kind": "walletobjects#loyaltyClass"
    }


def build_object_payload(site, user):
    # user = dict avec user_id, display_name, loyalty_number, points...
    object_id = f"{ISSUER_ID}.{site['site_key']}_{user['user_id']}"
    payload = {
        "id": object_id,
        "classId": site["class_id"],
        "state": "active",
        "accountId": user["loyalty_number"],
        "accountName": user.get("display_name", ""),
        "loyaltyPoints": {
            "balance": {"string": str(user.get("points", 0))},
            "label": "Points"
        },
        # barcode si besoin
        "barcode": {
            "type": "qrCode",
            "value": user["loyalty_number"]
        },
        # autres champs (messages, links, locations...) selon besoin
    }
    return payload

def get_private_key_from_service_account(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)
    return data["private_key"]

def generate_save_url(object_id, class_id, issuer_id, private_key):
    payload = {
        "iss": SERVICE_ACCOUNT_EMAIL,
        "aud": "google",
        "typ": "savetowallet",
        "iat": int(time.time()),
        "payload": {
            "loyaltyObjects": [
                {
                    "id": object_id,
                    "classId": class_id,
                }
            ]
        }
    }
    print("JWT payload:", json.dumps(payload))
    token = jwt.encode(payload, private_key, algorithm="RS256")
    return f"https://pay.google.com/gp/v/save/{token}"

def main():
    service = get_service()
    private_key = get_private_key_from_service_account(SERVICE_ACCOUNT_FILE)

    # 1) pour chaque site, créer la class si manquante
    for site in SITES:
        cls_payload = build_class_payload(site)
        create_loyalty_class_if_missing(service, cls_payload)

    # 2) pour chaque site, créer des objets pour les utilisateurs
    # Exemple : on boucle sur une liste d'utilisateurs à issuer
    users_for_sites = {
        "boutique-A": [
            {"user_id": "u1001", "display_name": "Alice", "loyalty_number": "A1001", "points": 120},
            {"user_id": "u1002", "display_name": "Bob", "loyalty_number": "A1002", "points": 30},
        ],
        "boutique-B": [
            {"user_id": "u2001", "display_name": "Claire", "loyalty_number": "B2001", "points": 420},
        ],
    }

    for site in SITES:
        key = site["site_key"]
        users = users_for_sites.get(key, [])
        for user in users:
            obj_payload = build_object_payload(site, user)
            print("object payload:", json.dumps(obj_payload))
            created_obj = create_loyalty_object(service, obj_payload)
            print("Created object:", created_obj.get("id"))
            # Générer le lien Add to Google Wallet pour cet utilisateur
            save_url = generate_save_url(
                object_id=created_obj["id"],
                class_id=site["class_id"],
                issuer_id=ISSUER_ID,
                private_key=private_key
            )
            print(f"Lien d'ajout pour {user['display_name']} : {save_url}")
            time.sleep(0.1)

if __name__ == "__main__":
    main()
