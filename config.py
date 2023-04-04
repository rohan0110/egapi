import os

# Google Drive API credentials
CLIENT_ID = '27798276599-f0b46p3o9esq26j07p1uq35km28iqef6.apps.googleusercontent.com'
CLIENT_SECRET = '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'
REDIRECT_URI = 'http://localhost:5000/auth/callback'

# Flask secret key
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', '1234')
