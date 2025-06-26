# 📚 Morpheme Highlighter

An AI-powered web tool that helps students improve their spelling, vocabulary, and morphological awareness. Users can paste text, click on words, and instantly see morpheme breakdowns, definitions, and related words.

## 🎯 Features

- **Interactive Text Analysis**: Paste any text and click on words to analyze them
- **AI-Powered Morphology**: Uses OpenAI GPT or Anthropic Claude for accurate morpheme analysis
- **Visual Breakdown**: See prefixes, roots, and suffixes with color-coded explanations
- **Related Words**: Discover etymologically related words
- **Example Sentences**: See words used in context
- **Responsive Design**: Works on desktop and mobile devices

## 🏗️ Project Structure

```
morpheme-highlighter/
├── frontend/           # React application
│   ├── src/
│   │   ├── components/
│   │   │   ├── MorphemeHighlighter.js
│   │   │   └── MorphemeHighlighter.css
│   │   ├── services/
│   │   │   └── api.js
│   │   └── ...
│   ├── package.json
│   └── README.md
├── backend/            # Flask API
│   ├── app.py
│   ├── requirements.txt
│   └── README.md
├── start-dev.sh        # Development startup script
└── README.md
```

## 🚀 Quick Start

### Option 1: Use the development script (Recommended)

```bash
./start-dev.sh
```

This will start both the Flask backend and React frontend automatically.

### Option 2: Manual setup

#### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. (Optional) Set up AI API keys:
```bash
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

5. Start the Flask server:
```bash
python app.py
```

The backend will be available at `http://localhost:5000`

#### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the React development server:
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## 🔧 API Endpoints

- `GET /api/health` - Health check
- `POST /api/analyze-morpheme` - Analyze word morphemes
  - Request: `{"word": "disrespectfully"}`
  - Response: JSON with morpheme breakdown

## 🤖 AI Integration

The application supports multiple AI providers:

1. **OpenAI GPT-3.5-turbo** (primary) - Fast and accurate analysis
2. **Anthropic Claude-3-Sonnet** (fallback) - Alternative AI provider
3. **Mock Data** (fallback) - Sample analysis for demonstration

## 📝 Example Usage

1. Paste text like: "The disrespectfully behaved student was unbelievable in class."
2. Click on "disrespectfully"
3. See the analysis:
   - **dis-** (prefix: not / opposite of)
   - **respect** (root: to show regard)
   - **-ful** (suffix: full of)
   - **-ly** (suffix: in a way that...)
   - Example: "He spoke disrespectfully to the teacher."
   - Related: respect, respectful, disrespect

## 🌐 Environment Variables

- `REACT_APP_API_URL` - Backend API URL (default: http://localhost:5000/api)
- `OPENAI_API_KEY` - Your OpenAI API key
- `ANTHROPIC_API_KEY` - Your Anthropic API key

## 🎨 Technologies Used

- **Frontend**: React, CSS3, JavaScript
- **Backend**: Flask, Python
- **AI**: OpenAI GPT, Anthropic Claude
- **Styling**: Modern CSS with gradients and animations

## 🚀 Production Deployment

For production deployment:

1. Set `debug=False` in `backend/app.py`
2. Use a production WSGI server like Gunicorn
3. Configure proper CORS settings
4. Set up environment variables securely
5. Build the React app with `npm run build`

## 📚 Educational Benefits

- **Morphological Awareness**: Understanding word structure
- **Vocabulary Building**: Learning related words and etymology
- **Spelling Improvement**: Understanding word formation patterns
- **Language Learning**: Support for ESL students
- **Early Literacy**: Helpful for young readers

Perfect for teachers, students, language learners, and anyone interested in understanding how words are built! 