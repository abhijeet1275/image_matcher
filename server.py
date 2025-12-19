from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import torch
import open_clip
from PIL import Image
import io
import os
from dotenv import load_dotenv
from explainable_matcher import ExplainableImageMatcher
from mongo_models import MongoDB

# Load environment variables
load_dotenv()

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize MongoDB with connection string from .env
mongo_db = MongoDB(uri=os.getenv('MONGODB_URI'), upload_folder=UPLOAD_FOLDER)

# --- Model Setup (Load once at startup) ---
print("--- Starting Model Setup ---")
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

try:
    model, _, preprocess = open_clip.create_model_and_transforms(
        'ViT-B-32',
        pretrained='laion2b_s34b_b79k'
    )
    model.to(device)
    tokenizer = open_clip.get_tokenizer('ViT-B-32')
    
    # Initialize explainable matcher
    explainer = ExplainableImageMatcher(model, tokenizer, preprocess, device)
    
    print(f"Model loaded successfully on {device}.")
    print("--- Backend server is ready ---")
except Exception as e:
    print(f"ERROR: Failed to load model: {e}")
    exit(1)


# ============ AUTHENTICATION ENDPOINTS ============

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login or create user with just a login ID"""
    data = request.get_json()
    
    if not data or 'login_id' not in data:
        return jsonify({'error': 'Login ID is required'}), 400
    
    login_id = data['login_id'].strip()
    
    if not login_id:
        return jsonify({'error': 'Login ID cannot be empty'}), 400
    
    user = mongo_db.create_or_get_user(login_id)
    
    return jsonify({
        'message': 'Login successful',
        'user': user
    }), 200


@app.route('/api/auth/check/<login_id>', methods=['GET'])
def check_user(login_id):
    """Check if user exists"""
    user = mongo_db.users.find_one({'login_id': login_id})
    
    if user:
        return jsonify({'exists': True, 'user': mongo_db._format_user(user)}), 200
    else:
        return jsonify({'exists': False}), 404


# ============ MATCH ENDPOINTS ============

@app.route('/api/match', methods=['POST'])
def match_image_with_prompt():
    """Quick match endpoint (no storage)"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    if 'prompt' not in request.form:
        return jsonify({'error': 'No prompt provided'}), 400

    image_file = request.files['image']
    prompt_text = request.form['prompt']

    try:
        image_bytes = image_file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        image_tensor = preprocess(image).unsqueeze(0).to(device)
        text = tokenizer([prompt_text]).to(device)

        with torch.no_grad():
            image_features = model.encode_image(image_tensor)
            text_features = model.encode_text(text)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            similarity = (image_features @ text_features.T)

        score = similarity.item() * 100
        return jsonify({'similarity': f"{score:.2f}"})

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to process image and prompt'}), 500


@app.route('/api/explain', methods=['POST'])
def explain_match():
    """Explainable match with storage for logged-in users"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    if 'prompt' not in request.form:
        return jsonify({'error': 'No prompt provided'}), 400

    image_file = request.files['image']
    prompt_text = request.form['prompt']
    user_id = request.form.get('user_id')  # Optional: store if user is logged in

    try:
        image_bytes = image_file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Get explainable results
        result = explainer.explain_match(image, prompt_text)
        
        # If user is logged in, save to database and file system
        if user_id:
            user = mongo_db.get_user_by_id(user_id)
            if user:
                match_id = mongo_db.save_match(
                    user_id=user_id,
                    prompt=prompt_text,
                    image_bytes=image_bytes,
                    image_filename=image_file.filename,
                    match_score=result['final_score'],
                    explanation=result['explanation_text'],
                    feature_breakdown=result['feature_breakdown']
                )
                
                result['saved'] = True
                result['match_id'] = match_id
        
        return jsonify(result)

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to explain match: {str(e)}'}), 500


# ============ HISTORY ENDPOINTS ============

@app.route('/api/history/<user_id>', methods=['GET'])
def get_user_history(user_id):
    """Get match history for a user"""
    user = mongo_db.get_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    matches = mongo_db.get_user_matches(user_id)
    
    return jsonify({
        'user': user,
        'matches': matches
    }), 200


@app.route('/api/history/match/<match_id>', methods=['GET'])
def get_match_detail(match_id):
    """Get detailed information about a specific match"""
    match = mongo_db.get_match_by_id(match_id)
    
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    return jsonify(match), 200


@app.route('/api/history/match/<match_id>', methods=['DELETE'])
def delete_match(match_id):
    """Delete a match from history"""
    success = mongo_db.delete_match(match_id)
    
    if not success:
        return jsonify({'error': 'Match not found or deletion failed'}), 404
    
    return jsonify({'message': 'Match deleted successfully'}), 200


@app.route('/uploads/<filename>')
def serve_image(filename):
    """Serve uploaded images from the uploads folder"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(port=5001, debug=True)