# Webcafe AI

A modern web application with a React frontend and Flask backend.

## Project Structure

```
webcafeland/
├── backend/           # Flask backend
│   ├── app.py        # Main Flask application
│   ├── requirements.txt
│   └── README.md
├── src/              # React frontend
│   ├── views/
│   ├── services/
│   └── ...
├── start-dev.sh      # Development startup script
└── README.md
```

## Quick Start

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

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the Flask server:
```bash
python app.py
```

The backend will be available at `http://localhost:5000`

#### Frontend Setup

1. Install dependencies:
```bash
npm install
```

2. Start the React development server:
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/color` - Get current color
- `POST /api/color` - Update color (send JSON: `{"color": "blue"}`)
- `GET /api/messages` - Get all messages
- `POST /api/messages` - Add new message (send JSON: `{"message": "Hello"}`)

## Environment Variables

You can configure the API URL by setting the `REACT_APP_API_URL` environment variable:

```bash
export REACT_APP_API_URL=http://localhost:5000/api
```

## Features

- **Color Toggle**: Click the button to change the color box between red and blue
- **Backend Integration**: Color state is persisted on the Flask backend
- **Error Handling**: Displays error messages if backend communication fails
- **Loading States**: Shows loading indicator while fetching data

## Development

- The Flask app runs in debug mode by default
- React app includes hot reloading for development
- CORS is enabled on the Flask backend for local development

## Production Deployment

For production deployment:

1. Set `debug=False` in `backend/app.py`
2. Use a production WSGI server like Gunicorn
3. Configure proper CORS settings
4. Use a production database instead of in-memory storage
5. Set up proper environment variables