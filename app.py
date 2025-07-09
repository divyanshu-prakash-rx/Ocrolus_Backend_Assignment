from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import os
from collections import defaultdict

app = Flask(__name__)