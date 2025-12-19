# Image & Prompt Matcher

An AI-powered application that matches images with text prompts using CLIP (Contrastive Language-Image Pre-training). Features explainable AI that breaks down matching scores by analyzing individual prompt features.

## 🚀 Features

- **Image-Text Matching**: Upload images and get similarity scores with text prompts
- **Explainable AI**: Detailed breakdown showing why each image matches (or doesn't match)
- **User Authentication**: Simple login system (no password required)
- **Match History**: Save and review past matches with full explanations
- **Cloud Storage**: All data stored in MongoDB Atlas (images + metadata)

## 🛠️ Tech Stack

**Backend:**
- Python 3.12
- Flask (REST API)
- PyTorch + OpenCLIP (CLIP ViT-B/32 model)
- MongoDB + GridFS (cloud storage)

**Frontend:**
- React.js
- Axios for API calls
- CSS3 (custom styling)

## 📋 Prerequisites

- Python 3.10 or higher
- Node.js 16+ and npm
- MongoDB Atlas account (free tier works)
- 4GB+ RAM (for CLIP model)

## 🔧 Installation & Setup

### 1. Clone the Repository

\`\`\`bash
git clone https://github.com/YOUR_USERNAME/image-matcher.git
cd image-matcher
\`\`\`

### 2. Backend Setup

\`\`\`bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
\`\`\`

### 3. MongoDB Atlas Setup

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Create a new cluster (M0 FREE tier)
3. Go to **Database Access** → Add new user with read/write permissions
4. Go to **Network Access** → Add IP Address → Allow access from anywhere (0.0.0.0/0)
5. Go to **Database** → **Connect** → **Drivers** → Copy connection string

### 4. Environment Configuration

\`\`\`bash
# Create .env file from example
cp .env.example .env

# Edit .env and add your MongoDB connection string
# Replace <password> with your actual database password
\`\`\`

Example `.env`:
\`\`\`
MONGODB_URI=mongodb+srv://myuser:mypassword@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
\`\`\`

### 5. Frontend Setup

\`\`\`bash
cd image-matcher-app
npm install
\`\`\`

## 🚀 Running the Application

### Start Backend Server

\`\`\`bash
# From project root directory
python server.py
\`\`\`

Server runs on: `http://localhost:5001`

### Start Frontend

\`\`\`bash
# In a new terminal
cd image-matcher-app
npm start
\`\`\`

Frontend runs on: `http://localhost:3000`

## 📖 Usage

1. **Login**: Enter any username (no password needed)
2. **Enter Prompt**: Describe what you're looking for (e.g., "modern kitchen with white cabinets")
3. **Upload Images**: Select one or multiple images
4. **Click Match**: Get similarity scores with detailed explanations
5. **View History**: Access all your past matches with stored images and explanations

## 🏗️ Project Structure

\`\`\`
image-matcher/
├── server.py                 # Flask backend server
├── explainable_matcher.py    # CLIP + explainability logic
├── mongo_models.py           # MongoDB operations
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── README.md                # This file
└── image-matcher-app/       # React frontend
    ├── public/
    ├── src/
    │   ├── components/
    │   │   ├── ImageUploader.js
    │   │   ├── PromptInput.js
    │   │   └── Login.js
    │   ├── App.js
    │   ├── App.css
    │   └── index.js
    └── package.json
\`\`\`

## 🔑 API Endpoints

### Authentication
- `POST /api/auth/login` - Login/create user
- `GET /api/auth/check/<login_id>` - Check if user exists

### Matching
- `POST /api/match` - Quick match (no storage)
- `POST /api/explain` - Match with explanation + storage

### History
- `GET /api/history/<user_id>` - Get user's match history
- `GET /api/history/match/<match_id>` - Get specific match details
- `DELETE /api/history/match/<match_id>` - Delete match

### Images
- `GET /api/image/<image_id>` - Serve image from MongoDB GridFS

## 🚢 Deployment

### Deploy Backend (Render/Railway)

1. Push code to GitHub
2. Connect your repo to Render/Railway
3. Set environment variable: `MONGODB_URI`
4. Deploy!

### Deploy Frontend (Vercel/Netlify)

1. Update API URL in `App.js` to your backend URL
2. Connect repo to Vercel/Netlify
3. Deploy!

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Notes

- CLIP model (~350MB) downloads automatically on first run
- MongoDB Atlas free tier: 512MB storage (good for ~500-1000 images)
- Images stored in MongoDB GridFS (no local storage issues)

## 🐛 Troubleshooting

**MongoDB Connection Error:**
- Check your connection string in `.env`
- Ensure IP whitelist allows your IP (or use 0.0.0.0/0)
- Verify database user credentials

**Model Loading Issues:**
- Ensure you have stable internet (for first-time download)
- Check available RAM (needs 4GB+)

**CORS Errors:**
- Verify backend is running on port 5001
- Check frontend API URLs match backend port

## 📄 License

MIT License - feel free to use for your projects!

## 👥 Team

Add your team members here!

## 🙏 Acknowledgments

- OpenAI CLIP model
- OpenCLIP implementation
- MongoDB Atlas for cloud database
\`\`\`

## Step 5: Update React `.gitignore`

````gitignore
# filepath: /Users/abhijeetkumar/Desktop/image_matcher/image-matcher-app/.gitignore
# Dependencies
node_modules/
/.pnp
.pnp.js

# Testing
/coverage

# Production
/build

# Misc
.DS_Store
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

npm-debug.log*
yarn-debug.log*
yarn-error.log*