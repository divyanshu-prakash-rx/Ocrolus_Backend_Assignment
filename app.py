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

recently_viewed=defaultdict(list)

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
    
def add_recently_viewed(user_id,article_id):
    if user_id not in recently_viewed:
        recently_viewed[user_id] = []

    if article_id in recently_viewed[user_id]:
        recently_viewed[user_id].remove(article_id)

    recently_viewed[user_id].insert(0, article_id)
    recently_viewed[user_id] = recently_viewed[user_id][:10]

def recently_viewed_articles(user_id):
    return recently_viewed.get(user_id,[])

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


@app.route('/articles',methods=['GET','POST'])
@jwt_required()
def create_or_get_articles():
    try:
        
        current_user_id=get_jwt_identity()
        if request.method=='GET':
            query=Article.query.filter_by(user_id=int(current_user_id))
            query=query.order_by(Article.updated_at.desc())

            articles= [article.to_dict() for article in query.all()]

            return jsonify({
                'articles': articles
            })
        
        if request.method=='POST':
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
    
@app.route('/articles/<int:article_id>', methods=['GET','PUT','DELETE'])
@jwt_required()
def update_or_delete_articles(article_id):
    try:
        current_user_id=get_jwt_identity()
        article= Article.query.filter_by(id=article_id, user_id=current_user_id).first()
        if not article:
            return jsonify({'message': "Article Not Found"}),404
        
        if request.method=='GET':
            add_recently_viewed(current_user_id,article_id)

            return jsonify({'article': article.to_dict()}),200
        
        if request.method=='PUT':

            data=request.get_json()
            if 'title' in data:
                article.title = data['title']
            if 'content' in data:
                article.content = data['content']

            article.updated_at = datetime.now(timezone.utc)

            db.session.commit()

            return jsonify({'message': "Article Updated Successfully"})
        
        if request.method=='DELETE':
            db.session.delete(article)
            db.session.commit()
            return jsonify({'message':'Article Deleted Successfully'}),200

    except Exception as e:
        return jsonify({
            'error':str(e)
        }),400

@app.route('/user/recently_viewed',methods=['GET'])
@jwt_required()
def recent_articles():
    try:
        current_user_id = get_jwt_identity()
        
        recent_article_ids = recently_viewed_articles(current_user_id)
        
        if not recent_article_ids:
            return jsonify({'recently_viewed': []}), 200
        
        articles = []
        for article_id in recent_article_ids:
            article = Article.query.filter_by(id=article_id, user_id=current_user_id).first()
            if article:
                articles.append(article.to_dict())
        
        return jsonify({'recently_viewed': articles}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

     

    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
