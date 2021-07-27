import os
from dotenv import load_dotenv

load_dotenv()

BIP39 = os.environ.get('BIP39')
CONFIGURATION_GUIDE_URL = os.environ.get(
  'CONFIGURATION_GUIDE_URL', 'https://slashpass.co/configure'
)
DATABASE_URL = os.environ.get('DATABASE_URL')
DEMO_SERVER = os.environ.get('DEMO_SERVER', 'http://0.0.0.0:8090/')
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
SENTRY_DSN = os.environ.get('SENTRY_DSN')
SIGNING_SECRET = os.environ.get('SIGNING_SECRET')
SLACK_SERVER = os.environ.get('SLACK_SERVER')
SLACK_APP_ID = os.environ.get('SLACK_APP_ID')
SLACK_CLIENT_ID = os.environ.get('SLACK_CLIENT_ID')
SLACK_CLIENT_SECRET = os.environ.get('SLACK_CLIENT_SECRET')
HOMEPAGE = os.environ.get('HOMEPAGE', 'https://slashpass.co')
