from flask import Flask, request, redirect, jsonify
import requests
import json

app = Flask(__name__)

# Update the redirect URI to the one provided by Render
redirect_uri = 'https://your-app-name.onrender.com/callback'

# Your Trackimo API credentials
server_url = 'https://app.trackimo.com'
user_name = 'trackimodemouser@trackimo.com'
password = 'A1abcdef'
client_id = 'bcf96758-9c87-4945-8c1e-e0bee2a4cb31'
client_secret = '5b95ce525f9e1a47bef42f4a85dd3500'

def do_login_and_get_access_token():
    resp = requests.post(
        f"{server_url}/api/internal/v2/user/login",
        headers={"Content-Type": "application/json"},
        json={"username": user_name, "password": password},
    )
    if resp.status_code != 200:
        raise Exception(f"Login failed: {resp.status_code} {resp.text}")
    cookies = dict(resp.cookies)

    oauth_resp = requests.get(
        f"{server_url}/api/v3/oauth2/auth",
        params={
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "locations,notifications,devices,accounts,settings,geozones",
        },
        cookies=cookies,
        allow_redirects=False,
    )
    if oauth_resp.status_code != 302:
        raise Exception(f"OAuth authorization failed: {oauth_resp.status_code} {oauth_resp.text}")

    location = oauth_resp.headers.get("Location")
    if not location:
        raise Exception("Authorization failed: Location header is missing in the response.")
    
    code = location.split("=")[1]

    token_resp = requests.post(
        f"{server_url}/api/v3/oauth2/token",
        headers={"Content-Type": "application/json"},
        json={"client_id": client_id, "client_secret": client_secret, "code": code},
        cookies=cookies,
    )
    if token_resp.status_code != 200:
        raise Exception(f"Token request failed: {token_resp.status_code} {token_resp.text}")

    return json.loads(token_resp.content).get('access_token')


@app.route('/')
def index():
    # This route starts the OAuth process
    access_token = do_login_and_get_access_token()
    return f"Authorization successful. Access Token: {access_token}"


@app.route('/callback')
def callback():
    # Callback route to handle OAuth response and retrieve the code
    code = request.args.get('code')
    if not code:
        return "Authorization failed: No code received", 400
    
    return f"Authorization successful. Code: {code}"


@app.route('/devices')
def get_devices():
    # This route retrieves the devices once we have an access token
    try:
        access_token = do_login_and_get_access_token()
        devices_resp = requests.get(
            f"{server_url}/api/v3/accounts/{user_name}/devices",
            headers={'Authorization': f'Bearer {access_token}'}
        )
        devices = devices_resp.json()
        if not devices:
            return jsonify({'error': 'No devices found in your account.'}), 404
        return jsonify(devices)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
