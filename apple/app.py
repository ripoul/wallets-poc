from flask import Flask, send_file, request, jsonify
from datetime import datetime, timezone
import json

app = Flask(__name__)

@app.route('/pass')
def serve_pass():
    return send_file(
        'monpass.pkpass',
        mimetype='application/vnd.apple.pkpass',
        as_attachment=True,
        download_name='monpass.pkpass'
    )


# call delete when a user uninstalls the pass
@app.route("/apple/webhook/v1/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>/<serialNumber>", methods=['POST'])
def register_device(deviceLibraryIdentifier, passTypeIdentifier, serialNumber):
    print("______________________")
    print("New device registration:")
    print(f"Device Library Identifier: {deviceLibraryIdentifier}")
    print(f"Pass Type Identifier: {passTypeIdentifier}")
    print(f"Serial Number: {serialNumber}")
    print("Push Token:", request.json.get("pushToken"))
    to_write = {
        "deviceLibraryIdentifier": deviceLibraryIdentifier,
        "passTypeIdentifier": passTypeIdentifier,
        "serialNumber": serialNumber,
        "pushToken": request.json.get("pushToken"),
    }
    with open("registrations.json", "a") as log_file:
        json.dump(to_write, log_file)
    return '', 201

@app.route("/apple/webhook/v1/passes/<passTypeIdentifier>/<serialNumber>", methods=['GET'])
def get_pass(passTypeIdentifier, serialNumber):
    print(f"Getting pass for pass type {passTypeIdentifier} and serial number {serialNumber}")
    return send_file(
        'monpass.pkpass',
        mimetype='application/vnd.apple.pkpass',
        as_attachment=True,
        download_name='monpass.pkpass'
    )

@app.route("/apple/webhook/v1/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>", methods=['GET'])
def get_serial_numbers(deviceLibraryIdentifier, passTypeIdentifier):
    print(f"Getting serial numbers for device {deviceLibraryIdentifier} and pass type {passTypeIdentifier}")
    last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open("registrations.json", "r") as log_file:
        log = json.load(log_file)
    
    response = {
        "lastUpdated": last_updated,
        "serialNumbers": [log["serialNumber"]]
    }
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)
