# -*-coding:utf-8-*-

# [START imports]
from flask import Flask
from requests_toolbelt.adapters import appengine
import sys

# [END imports]

reload(sys)
sys.setdefaultencoding('utf-8')
appengine.monkeypatch()

# [START create_app]
app = Flask(__name__)
# [END create_app]

from api import api_app
app.register_blueprint(api_app)
