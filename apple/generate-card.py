import json
import os
import shutil
import hashlib
import zipfile
import tempfile
import subprocess
from pathlib import Path
import dotenv
import httpx
import random
from datetime import datetime, timezone, timedelta

dotenv.load_dotenv()

USER_ID = "3f5b1f18-a73b-4d91-8d18-96d0f489b1d5"

# --- CONFIG ---
PASS_JSON = {
    "formatVersion": 1,
    "passTypeIdentifier": os.getenv("APPLE_PASS_TYPE_ID"),
    "serialNumber": USER_ID,
    "organizationName": "Mon Organisation",
    "description": "Mon pass exemple",
    "logoText": "Mon Pass",
    "teamIdentifier": os.getenv("APPLE_TEAM_ID"),

    # Ajoutez ces deux lignes :
    "webServiceURL": f"{os.getenv('BASE_URL')}apple/webhook/",
    "authenticationToken": "securetoken123456789", # 16 char minimum


    "logoText": "Carte Fidélité",
    "foregroundColor": "rgb(255,255,255)",
    "backgroundColor": "rgb(0,122,255)",

    "barcode": {
        "format": "PKBarcodeFormatQR",
        "message": "1234567890",
        "messageEncoding": "iso-8859-1"
    },

    "storeCard": {
        "primaryFields": [
            {
                "key": "points",
                "label": "Points",
                "value": random.randint(0, 1000),
            }
        ],
        "secondaryFields": [
            {
                "key": "tier",
                "label": "Niveau",
                "value": "Gold"
            }
        ],
        "auxiliaryFields": [
            {
                "key": "member",
                "label": "Membre",
                "value": "John Doe"
            }
        ],
        "backFields": [
            {
                "key": "internalMessage",
                "label": "",
                "value": "🎉 Offre spéciale : -20% ce week-end !",
                "changeMessage": "%@"
            }
        ]
    },
    "locations": [
        {
            "latitude": 46.96574020385742,
            "longitude": -1.3155150413513184,
            "relevantText": "📍 Vous êtes près de notre boutique !"
        }
    ],
}
IMAGES = ["imgs/icon.png", "imgs/icon@2x.png", "imgs/strip.png"]  # mettez ici vos images existantes
OUTPUT_PKPASS = "monpass.pkpass"

# chemins vers vos certificats (PEM) générés depuis le .p12
PASS_CERT_PEM = "pass_cert.pem"
PASS_KEY_PEM = "pass_key.pem"
APPLE_WWDR_PEM = "AppleWWDRCA.pem"

# --- FIN CONFIG ---

def sha1_of_file(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# Ajoutez ici vos traductions (clé = identifiant, valeur = traduction)
I18N = {
    "fr": {
        "Points": "Points",
        "Niveau": "Niveau",
        "Membre": "Membre",
        "Conditions": "Conditions",
        "Valable dans tous les magasins.": "Valable dans tous les magasins.",
        "Votre carte a été mise à jour !": "Votre carte a été mise à jour !",
        "Carte Fidélité": "Carte Fidélité",
        "Mon Organisation": "Mon Organisation",
        "Mon pass exemple": "Mon pass exemple",
        "Mon Pass": "Mon Pass",
        "🎉 Offre spéciale : -20% ce week-end !": "🎉 Offre spéciale : -20% ce week-end !",
    },
    "en": {
        "Points": "Points",
        "Niveau": "Tier",
        "Membre": "Member",
        "Conditions": "Terms",
        "Valable dans tous les magasins.": "Valid in all stores.",
        "Votre carte a été mise à jour !": "Your card has been updated!",
        "Carte Fidélité": "Loyalty Card",
        "Mon Organisation": "My Organization",
        "Mon pass exemple": "My sample pass",
        "Mon Pass": "My Pass",
        "🎉 Offre spéciale : -20% ce week-end !": "🎉 Special offer: -20% this weekend!",
    }
}

def write_i18n_files(tmpdir):
    for lang, translations in I18N.items():
        lproj_dir = tmpdir / f"{lang}.lproj"
        lproj_dir.mkdir(exist_ok=True)
        strings_path = lproj_dir / "pass.strings"
        with open(strings_path, "w", encoding="utf-16") as f:
            for k, v in translations.items():
                f.write(f'"{k}" = "{v}";\n')

def make_pkpass():
    tmpdir = Path(tempfile.mkdtemp(prefix="passkit_"))
    try:
        # 1) écrire pass.json
        pass_json_path = tmpdir / "pass.json"
        with open(pass_json_path, "w", encoding="utf-8") as f:
            json.dump(PASS_JSON, f, ensure_ascii=False, indent=2)

        # 1b) écrire les fichiers d'internationalisation
        write_i18n_files(tmpdir)

        # 2) copier images
        for img in IMAGES:
            src = Path(img)
            if not src.exists():
                raise FileNotFoundError(f"Image introuvable: {img}")
            shutil.copy(src, tmpdir / src.name)

        # 3) générer manifest.json (SHA1 pour chaque fichier dans le dossier)
        manifest = {}
        for p in tmpdir.rglob("*"):
            if p.is_file():
                manifest[str(p.relative_to(tmpdir))] = sha1_of_file(p)

        manifest_path = tmpdir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)

        # 4) signer manifest.json -> crée le fichier 'signature' (calls openssl)
        signature_path = tmpdir / "signature"
        cmd = [
            "openssl", "smime", "-binary", "-sign",
            "-certfile", APPLE_WWDR_PEM,
            "-signer", PASS_CERT_PEM,
            "-inkey", PASS_KEY_PEM,
            "-in", str(manifest_path),
            "-out", str(signature_path),
            "-outform", "DER",
            "-nodetach",
        ]
        subprocess.run(cmd, check=True)

        # 5) zipper tout en .pkpass
        with zipfile.ZipFile(OUTPUT_PKPASS, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for p in tmpdir.rglob("*"):
                if p.is_file():
                    zf.write(p, arcname=p.relative_to(tmpdir))
        print(f"Créé: {OUTPUT_PKPASS}")

    finally:
        # nettoyage
        shutil.rmtree(tmpdir)
    
def push_update(push_token):
    url = f"https://api.push.apple.com/3/device/{push_token}"

    headers = {
        "apns-topic": os.getenv("APPLE_PASS_TYPE_ID")  # Important pour un Wallet pass
    }

    with httpx.Client(http2=True, cert=(PASS_CERT_PEM, PASS_KEY_PEM)) as client:
        response = client.post(url, headers=headers, json={
            "aps": {
                "content-available": 1,
                "alert": {
                    "title": "title notif 1",
                    "body": "body notif 1"
                }
            }
        })  # <-- body JSON vide
        print(f"Push response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response body: {response.text}")

        
if __name__ == "__main__":
    make_pkpass()

    with open("registrations.json", "r") as f:
        infos = json.load(f)
        push_token = infos["pushToken"]

        push_update(push_token)