import json
import os
import shutil
import hashlib
import zipfile
import tempfile
import subprocess
from pathlib import Path
import dotenv

dotenv.load_dotenv()

USER_ID = "3f5b1f18-a73b-4d91-8d18-96d0f489b1d5"

# --- CONFIG ---
PASS_JSON = {
    "formatVersion": 1,
    "passTypeIdentifier": os.getenv("APPLE_PASS_TYPE_ID"),  # adapter
    "serialNumber": USER_ID,
    "organizationName": "Mon Organisation",
    "description": "Mon pass exemple",
    "logoText": "Mon Pass",
    "teamIdentifier": os.getenv("APPLE_TEAM_ID"),  # adapter


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
                "value": 120
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
                "key": "terms",
                "label": "Conditions",
                "value": "Valable dans tous les magasins."
            }
        ]
    }
}
IMAGES = ["imgs/icon.png", "imgs/icon@2x.png"]  # mettez ici vos images existantes
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

def make_pkpass():
    tmpdir = Path(tempfile.mkdtemp(prefix="passkit_"))
    try:
        # 1) écrire pass.json
        pass_json_path = tmpdir / "pass.json"
        with open(pass_json_path, "w", encoding="utf-8") as f:
            json.dump(PASS_JSON, f, ensure_ascii=False, indent=2)

        # 2) copier images
        for img in IMAGES:
            src = Path(img)
            if not src.exists():
                raise FileNotFoundError(f"Image introuvable: {img}")
            shutil.copy(src, tmpdir / src.name)

        # 3) générer manifest.json (SHA1 pour chaque fichier dans le dossier)
        manifest = {}
        for p in tmpdir.iterdir():
            if p.is_file():
                manifest[p.name] = sha1_of_file(p)

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
            for p in tmpdir.iterdir():
                zf.write(p, arcname=p.name)
        print(f"Créé: {OUTPUT_PKPASS}")

    finally:
        # nettoyage
        shutil.rmtree(tmpdir)

if __name__ == "__main__":
    make_pkpass()