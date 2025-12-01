from google.oauth2 import service_account
from googleapiclient.discovery import build
import dotenv
import os

dotenv.load_dotenv()

SERVICE_ACCOUNT_FILE = "service-account.json"
SCOPES = ["https://www.googleapis.com/auth/wallet_object.issuer"]
ISSUER_ID = os.getenv("ISSUER_ID")  # Remplacer par ton issuer ID
SERVICE_ACCOUNT_EMAIL = os.getenv("SERVICE_ACCOUNT_EMAIL")

CLASS_ID = "loyalty_boutiqueA"
USER_ID = f"boutique-A_u1001"


def send_wallet_notification(object_id, message_header, message_body):
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("walletobjects", "v1", credentials=creds, cache_discovery=False)
    message = {
        "message": {
            "header": message_header,
            "body": message_body,
            "messageType": 'TEXT_AND_NOTIFY',
            'displayInterval': {
                'end': {"date": '2025-10-17T10:30:00.00+02:00'},
            }
        }
    }
    response = (
        service.loyaltyobject().addmessage(resourceId=object_id, body=message).execute()
    )
    print("Notification envoyée:", response)


def send_class_notification(class_id, message_header, message_body):
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("walletobjects", "v1", credentials=creds, cache_discovery=False)
    message = {
        "message": {
            "header": message_header,
            "body": message_body,
            "messageType": 'TEXT_AND_NOTIFY',
            'displayInterval': {
                'end': {"date": '2025-10-17T13:40:00.00+02:00'},
            }
        }
    }
    response = (
        service.loyaltyclass().addmessage(resourceId=class_id, body=message).execute()
    )
    print("Notification envoyée sur la classe:", response)


if __name__ == "__main__":
    # Exemple d'envoi de notification
    # send_wallet_notification(
    #    object_id=f"{ISSUER_ID}.{USER_ID}",
    #    message_header="TMP3 Nouveau bonus !",
    #    message_body="Vous avez reçu 50 points supplémentaires.",
    # )
    #send_class_notification(
    #   class_id=f"{ISSUER_ID}.{CLASS_ID}",
    #   message_header="Info programme 2",
    #   message_body="Découvrez nos nouveaux avantages VIP !",
    #)
    pass