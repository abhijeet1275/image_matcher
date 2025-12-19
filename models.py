from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    """User model - simple login ID only, no password"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    login_id = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to match history
    matches = db.relationship('MatchHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.login_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'login_id': self.login_id,
            'created_at': self.created_at.isoformat()
        }


class MatchHistory(db.Model):
    """Store match results for each user"""
    __tablename__ = 'match_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)  # Store image file path
    match_score = db.Column(db.Float, nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    feature_breakdown = db.Column(db.Text, nullable=False)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MatchHistory {self.id} - User {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'prompt': self.prompt,
            'image_filename': self.image_filename,
            'image_path': self.image_path,
            'match_score': self.match_score,
            'explanation': self.explanation,
            'feature_breakdown': json.loads(self.feature_breakdown),
            'created_at': self.created_at.isoformat()
        }