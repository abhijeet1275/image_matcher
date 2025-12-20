from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import glob
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    login_id = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    matches = db.relationship('Match', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'login_id': self.login_id,
            'created_at': self.created_at.isoformat()
        }


class Match(db.Model):
    __tablename__ = 'matches'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    match_score = db.Column(db.Float, nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    feature_breakdown = db.Column(db.Text, nullable=False)  # Store as JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'prompt': self.prompt,
            'image_filename': self.image_filename,
            'stored_filename': self.stored_filename,
            'image_path': self.image_path,
            'match_score': self.match_score,
            'explanation': self.explanation,
            'feature_breakdown': json.loads(self.feature_breakdown),
            'created_at': self.created_at.isoformat()
        }


class PostgresDB:
    """PostgreSQL database operations"""
    
    def __init__(self, app=None, upload_folder='uploads'):
        self.upload_folder = upload_folder
        os.makedirs(self.upload_folder, exist_ok=True)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        db.init_app(app)
        with app.app_context():
            db.create_all()
            print("✓ PostgreSQL database initialized")
    
    def _get_next_image_number(self, user_id, base_name):
        """Get the next available image number for a user"""
        pattern = os.path.join(self.upload_folder, f"{user_id}_{base_name}_*.???")
        existing_files = glob.glob(pattern)
        
        if not existing_files:
            return 1
        
        numbers = []
        for filepath in existing_files:
            filename = os.path.basename(filepath)
            try:
                parts = filename.rsplit('_', 1)
                if len(parts) == 2:
                    num_with_ext = parts[1]
                    num_str = num_with_ext.split('.')[0]
                    numbers.append(int(num_str))
            except:
                continue
        
        return max(numbers) + 1 if numbers else 1
    
    def create_or_get_user(self, login_id):
        """Create new user or get existing one"""
        user = User.query.filter_by(login_id=login_id).first()
        
        if not user:
            user = User(login_id=login_id)
            db.session.add(user)
            db.session.commit()
            print(f"✓ Created new user: {login_id}")
        
        return user.to_dict()
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            user = User.query.get(int(user_id))
            return user.to_dict() if user else None
        except:
            return None
    
    def save_match(self, user_id, prompt, image_bytes, image_filename, 
                   match_score, explanation, feature_breakdown):
        """Save match result with image stored as file"""
        # Get base name without extension
        base_name = os.path.splitext(image_filename)[0]
        base_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        base_name = base_name.replace(' ', '_')[:30]
        
        ext = os.path.splitext(image_filename)[1] or '.jpg'
        next_num = self._get_next_image_number(user_id, base_name)
        new_filename = f"{user_id}_{base_name}_{next_num}{ext}"
        
        # Save image to disk
        image_path = os.path.join(self.upload_folder, new_filename)
        with open(image_path, 'wb') as f:
            f.write(image_bytes)
        
        print(f"✓ Saved image: {new_filename}")
        
        # Create match record
        match = Match(
            user_id=int(user_id),
            prompt=prompt,
            image_filename=image_filename,
            stored_filename=new_filename,
            image_path=image_path,
            match_score=match_score,
            explanation=explanation,
            feature_breakdown=json.dumps(feature_breakdown)  # Convert to JSON string
        )
        
        db.session.add(match)
        db.session.commit()
        
        return str(match.id)
    
    def get_user_matches(self, user_id):
        """Get all matches for a user"""
        try:
            matches = Match.query.filter_by(user_id=int(user_id)).order_by(Match.created_at.desc()).all()
            return [match.to_dict() for match in matches]
        except:
            return []
    
    def get_match_by_id(self, match_id):
        """Get single match by ID"""
        try:
            match = Match.query.get(int(match_id))
            return match.to_dict() if match else None
        except:
            return None
    
    def delete_match(self, match_id):
        """Delete match and its associated image file"""
        try:
            match = Match.query.get(int(match_id))
            if match:
                # Delete image file
                if match.image_path and os.path.exists(match.image_path):
                    os.remove(match.image_path)
                    print(f"✓ Deleted image: {match.stored_filename}")
                
                # Delete match record
                db.session.delete(match)
                db.session.commit()
                return True
            return False
        except Exception as e:
            print(f"✗ Error deleting match: {e}")
            db.session.rollback()
            return False