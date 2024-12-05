
import os
import requests
from flask import Flask, redirect, request, jsonify

app = Flask(__name__)

# Your Trackimo API credentials
server_url = 'https://app.trackimo.com'
user_name = 'dan.uc.advisors@gmail.com'
password = 'BuleBule222'
client_id = '878b7a60-b504-44c5-bda9-bf6938c5fa29'
client_secret = '58d898c4769c6b9f78c8a39db2feca97'
redirect_uri = 'https://ivry100.onrender.com/callback'

# The route that triggers the OAuth login flow
@app.route('/')
def index():
    auth_url = f"{server_url}/api/v3/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=locations,notifications,devices,accounts,settings,geozones"
    return redirect(auth_url)

# OAuth callback route
@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Authorization failed: No code received", 400

    # Use the authorization code to get the access token
    access_token = do_login_and_get_access_token(code)

    # Redirect to /devices with the access token as a query parameter
    return redirect(f'/devices?access_token={access_token}')

# Function to get the access token
def do_login_and_get_access_token(code):
    # Request token using the authorization code
    token_url = f"{server_url}/api/v3/oauth2/token"
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    response = requests.post(token_url, data=data)
    response.raise_for_status()
    return response.json().get('access_token')

# The route that fetches the devices associated with the account
@app.route('/devices')
def get_devices():
    access_token = request.args.get('access_token')
    if not access_token:
        return jsonify({'error': 'Access token is missing.'}), 400

    # Replace 'account_id' with your actual Trackimo account ID
    account_id = "1367032"  # Replace with your actual account ID

    # Make the API request to Trackimo API for device information
    devices_resp = requests.get(
        f"{server_url}/api/v3/accounts/{account_id}/devices",
        headers={'Authorization': f'Bearer {access_token}'}
    )

    if devices_resp.status_code != 200:
        return jsonify({'error': 'Failed to fetch devices', 'status_code': devices_resp.status_code}), 500

    devices = devices_resp.json()
    if not devices:
        return jsonify({'error': 'No devices found in your account.'}), 404

    return jsonify(devices)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000), debug=True)
