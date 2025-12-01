from flask import Flask, send_file

app = Flask(__name__)

@app.route('/pass')
def serve_pass():
    return send_file(
        'monpass.pkpass',
        mimetype='application/vnd.apple.pkpass',
        as_attachment=True,
        download_name='monpass.pkpass'
    )

if __name__ == '__main__':
    app.run(debug=True)
