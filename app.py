from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timezone
import os
from collections import defaultdict

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'Strong_secret_key' 
db = SQLAlchemy(app)
jwt = JWTManager(app)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def set_password(self, password):
        self.password = password
    
    def check_password(self, password):
        return self.password == password
    
class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    

@app.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'message': "Username and Password required"}),404
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message':'Username already exists'}),400

        username=data['username']
        password = data['password']

        user = User(username=username)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        
        access_token=create_access_token(identity=str(user.id))

        return jsonify({
            'message':"User registered successfully",
            'user':user.username,
            'access_token':access_token
        }),200
    
    except Exception as e:
        return jsonify({'error': str(e)}),400
    
@app.route('/auth/login',methods=['POST'])
def login():
    try:
        data=request.get_json()
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'message': "Username and Password required"})
        username=data['username']
        password=data['password']
        user=User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({'message': 'Invalid Username or Password'}),401
        
        access_token=create_access_token(identity=str(user.id))

        return jsonify({
            'message':'login successful',
            'user':user.username,
            'access_token': access_token
        }),200

    except Exception as e:
        return jsonify({'error': str(e)}),400


@app.route('/articles',methods=['GET','POST','PUT','DELETE'])
@jwt_required()
def articles():
    try:
        if request.method=='GET':
            current_user_id=get_jwt_identity()
            query=Article.query.filter_by(user_id=int(current_user_id))
            query=query.order_by(Article.updated_at.desc())

            articles= [article.to_dict() for article in query.all()]

            return jsonify({
                'articles': articles
            })
        if request.method=='POST':
            current_user_id=get_jwt_identity()
            data=request.get_json()
            if not data or not data.get('content') or not data.get('title'):
                return jsonify({'message':'Title or Content missing'}), 400
            title=data['title']
            content=data['content']
            article=Article(
                user_id=int(current_user_id),
                title=title,
                content=content
            )
            db.session.add(article)
            db.session.commit()
            return jsonify({'message':"Article Created"}), 201
           

    except Exception as e:
        return jsonify({'error': str(e)}), 500
     

    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
