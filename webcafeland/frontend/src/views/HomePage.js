import React, { useState, useEffect } from 'react';
import './HomePage.css';
import apiService from '../services/api';

const HomePage = () => {
    const [isBlue, setIsBlue] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        // Load initial color from backend
        loadColor();
    }, []);

    const loadColor = async () => {
        try {
            setLoading(true);
            const response = await apiService.getColor();
            setIsBlue(response.color === 'blue');
            setError(null);
        } catch (err) {
            console.error('Failed to load color:', err);
            setError('Failed to load color from server');
        } finally {
            setLoading(false);
        }
    };

    const toggleColor = async () => {
        try {
            const newColor = isBlue ? 'red' : 'blue';
            await apiService.updateColor(newColor);
            setIsBlue(!isBlue);
            setError(null);
        } catch (err) {
            console.error('Failed to update color:', err);
            setError('Failed to update color on server');
        }
    };

    if (loading) {
        return (
            <div className="cafe-homepage">
                <h1>Welcome to Webcafe AI</h1>
                <p>Loading...</p>
            </div>
        );
    }

    return (
        <div className="cafe-homepage">
            <h1>Welcome to Webcafe AI</h1>
            <p>Your go-to solution for AI-driven web applications.</p>
            {error && <p className="error-message">{error}</p>}
            <div className={`cafe-color-box ${isBlue ? 'cafe-blue' : 'cafe-red'}`}></div>
            <button className="cafe-button" onClick={toggleColor}>
                Change Color
            </button>
            <p className="backend-info">
                Connected to Flask backend at {process.env.REACT_APP_API_URL || 'http://localhost:5000'}
            </p>
        </div>
    );
};

export default HomePage;