from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import os
import glob

class MongoDB:
    """MongoDB connection and operations"""
    
    def __init__(self, uri=None, upload_folder='uploads'):
        if uri is None:
            uri = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
        
        try:
            self.client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            # Test the connection
            self.client.server_info()
            print("✓ MongoDB connected successfully")
        except Exception as e:
            print(f"✗ MongoDB connection failed: {e}")
            raise
        
        self.db = self.client['image_matcher']
        self.users = self.db['users']
        self.matches = self.db['match_history']
        
        # Upload folder for images
        self.upload_folder = upload_folder
        os.makedirs(self.upload_folder, exist_ok=True)
        
        # Create indexes for better performance
        try:
            self.users.create_index('login_id', unique=True)
            self.matches.create_index([('user_id', 1), ('created_at', -1)])
        except:
            pass  # Indexes might already exist
    
    def _get_next_image_number(self, user_id, base_name):
        """Get the next available image number for a user"""
        # Pattern to match: userid_basename_number.ext
        pattern = os.path.join(self.upload_folder, f"{user_id}_{base_name}_*.???")
        existing_files = glob.glob(pattern)
        
        if not existing_files:
            return 1
        
        # Extract numbers from existing files
        numbers = []
        for filepath in existing_files:
            filename = os.path.basename(filepath)
            try:
                # Extract number before extension
                # Format: userid_basename_NUMBER.ext
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
        user = self.users.find_one({'login_id': login_id})
        
        if not user:
            user_doc = {
                'login_id': login_id,
                'created_at': datetime.utcnow()
            }
            user_id = self.users.insert_one(user_doc).inserted_id
            user = self.users.find_one({'_id': user_id})
        
        return self._format_user(user)
    
    def get_user_by_id(self, user_id):
        """Get user by ObjectId"""
        try:
            user = self.users.find_one({'_id': ObjectId(user_id)})
            return self._format_user(user) if user else None
        except:
            return None
    
    def save_match(self, user_id, prompt, image_bytes, image_filename, 
                   match_score, explanation, feature_breakdown):
        """Save match result with image stored as file with incremental numbering"""
        # Get base name without extension
        base_name = os.path.splitext(image_filename)[0]
        # Clean the base name (remove special characters)
        base_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        base_name = base_name.replace(' ', '_')[:30]  # Limit length
        
        # Get extension
        ext = os.path.splitext(image_filename)[1] or '.jpg'
        
        # Get next available number
        next_num = self._get_next_image_number(user_id, base_name)
        
        # Create unique filename with incremental number
        new_filename = f"{user_id}_{base_name}_{next_num}{ext}"
        
        # Save image to disk
        image_path = os.path.join(self.upload_folder, new_filename)
        with open(image_path, 'wb') as f:
            f.write(image_bytes)
        
        print(f"✓ Saved image: {new_filename}")
        
        match_doc = {
            'user_id': ObjectId(user_id),
            'prompt': prompt,
            'image_filename': image_filename,  # Original filename
            'stored_filename': new_filename,   # Renamed filename on disk
            'image_path': image_path,
            'match_score': match_score,
            'explanation': explanation,
            'feature_breakdown': feature_breakdown,
            'created_at': datetime.utcnow()
        }
        
        match_id = self.matches.insert_one(match_doc).inserted_id
        return str(match_id)
    
    def get_user_matches(self, user_id):
        """Get all matches for a user"""
        try:
            matches = self.matches.find(
                {'user_id': ObjectId(user_id)}
            ).sort('created_at', -1)
            
            return [self._format_match(m) for m in matches]
        except:
            return []
    
    def get_match_by_id(self, match_id):
        """Get single match by ID"""
        try:
            match = self.matches.find_one({'_id': ObjectId(match_id)})
            return self._format_match(match) if match else None
        except:
            return None
    
    def delete_match(self, match_id):
        """Delete match and its associated image file"""
        try:
            match = self.matches.find_one({'_id': ObjectId(match_id)})
            if match:
                # Delete image file
                if 'image_path' in match and os.path.exists(match['image_path']):
                    os.remove(match['image_path'])
                    print(f"✓ Deleted image: {match.get('stored_filename', 'unknown')}")
                
                # Delete match document
                self.matches.delete_one({'_id': ObjectId(match_id)})
                return True
            return False
        except Exception as e:
            print(f"✗ Error deleting match: {e}")
            return False
    
    def _format_user(self, user):
        """Format user document for API response"""
        if not user:
            return None
        return {
            'id': str(user['_id']),
            'login_id': user['login_id'],
            'created_at': user['created_at'].isoformat()
        }
    
    def _format_match(self, match):
        """Format match document for API response"""
        if not match:
            return None
        return {
            'id': str(match['_id']),
            'user_id': str(match['user_id']),
            'prompt': match['prompt'],
            'image_filename': match['image_filename'],
            'stored_filename': match.get('stored_filename', ''),
            'image_path': match.get('image_path', ''),
            'match_score': match['match_score'],
            'explanation': match['explanation'],
            'feature_breakdown': match['feature_breakdown'],
            'created_at': match['created_at'].isoformat()
        }