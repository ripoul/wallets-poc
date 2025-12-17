# Apple

## Prerequisites

- Apple Developer account and an activated Pass Type ID (com.apple.pass.<your_id>). To create a pass type id go [here](https://developer.apple.com/account/resources/identifiers/) section `Pass Type Ids`
- Pass signing certificate (issued by Apple) for your Pass Type ID, exported as .p12. [Create the certificate here](https://developer.apple.com/account/resources/certificates/list). To export as .p12, download the generated certificate and "install" it.
- Export the .p12 to PEM format:
```sh
openssl pkcs12 -legacy -in certs.p12 -nodes -clcerts -nokeys -out pass_cert.pem
openssl pkcs12 -legacy -in certs.p12 -nodes -clcerts -nocerts -out pass_key.pem
```
- Download [here](https://developer.apple.com/account/resources/certificates/add) (at the bottom of the page) the WWDRCA certificate and install it. Then export it in PEM format.
- Find your team ID in your apple dev profile [here](https://developer.apple.com/account/resources/certificates/add) on the top right corner and fill the `.env` file.

You should now have the following files:
- pass_cert.pem
- pass_key.pem
- AppleWWDRCA.pem

## Run it

Run an ngrok on port 5000. Put the url of the ngrok in the .env as baseUrl.

### Generate a card

```sh
python -m venv venv
source venv/bin/activate
pip install -r req.txt
python generate-card.py # will create a pkpass
python app.py # start an flask server to host the card file
```

### Update a card

Just uncomment the update section of generate-card.py after someone installed the card.

## Docs

- [pass formating](https://developer.apple.com/library/archive/documentation/UserExperience/Conceptual/PassKit_PG/Creating.html)
- [pass.json fields](https://developer.apple.com/documentation/walletpasses/pass)
- [pkpass validator](https://pkpassvalidator.azurewebsites.net/)