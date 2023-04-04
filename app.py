import os
from flask import Flask, redirect, request, session, url_for, render_template
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport import requests
from google.oauth2 import id_token
from google.auth import crypt, jwt
from werkzeug.utils import secure_filename
from google.oauth2.credentials import Credentials
from google.oauth2 import credentials
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from google_auth_oauthlib.flow import Flow

from googleapiclient.http import MediaFileUpload
from flask import Response


app = Flask(__name__)
app.config.from_pyfile('config.py')


@app.route('/auth')
def auth():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=['https://www.googleapis.com/auth/drive']
    )
    flow.redirect_uri = url_for('auth_callback', _external=True)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['oauth_state'] = state
    return redirect(authorization_url)


@app.route('/auth/callback')
def auth_callback():
    state = session['oauth_state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=['https://www.googleapis.com/auth/drive']
    )
    flow.redirect_uri = url_for('auth_callback', _external=True)
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    return redirect('/')


def credentials_to_dict(credentials):
    if isinstance(credentials, credentials.Credentials):
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
        }


@app.route('/')
def index():
    if 'credentials' not in session:
        return redirect('/auth')
    credentials = Credentials.from_dict(session['credentials'])
    service = build('drive', 'v3', credentials=credentials)
    try:
        files = service.files().list(
            q="'root' in parents",
            fields='nextPageToken, files(id, name, mimeType)',
            pageSize=10
        ).execute()
        return render_template('index.html', files=files.get('files', []))
    except HttpError as error:
        print(f'An error occurred: {error}')
        return 'An error occurred.' 

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'credentials' not in session:
        return redirect('/auth')
    credentials = Credentials.from_dict(session['credentials'])
    service = build('drive', 'v3', credentials=credentials)
    if request.method == 'POST':
        file = request.files['file']
        filename = secure_filename(file.filename)
        mimetype = file.content_type
        file_metadata = {
            'name': filename,
            'parents': ['18eC-KX5yFcgv2dmbOrVbgt-DdeWdwgLA'],
            'mimeType': mimetype
        }
        media = MediaFileUpload(
            file,
            mimetype=mimetype,
            resumable=True
        )
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        return redirect('/')
    return render_template('upload.html')

@app.route('/download/<file_id>')
def download(file_id):
    if 'credentials' not in session:
        return redirect('/auth')
    credentials = Credentials.from_dict(session['credentials'])
    service = build('drive', 'v3', credentials=credentials)
    file = service.files().get(fileId=file_id).execute()
    filename = file['name']
    mimetype = file['mimeType']
    request = service.files().get_media(fileId=file_id)
    media = request.execute()
    response = Response(media, mimetype)
    response.headers.set('Content-Disposition', f'attachment; filename="{filename}"')
    return response

if __name__ == '__main__':
    app.run(debug=True)
