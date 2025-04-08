import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

// Login Form Component
const LoginForm = ({ onLoginSuccess, switchToRegister }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const isMounted = useRef(true);

    // Set up the cleanup when component unmounts
    useEffect(() => {
        return () => {
            isMounted.current = false;
        };
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!email || !password) {
            setError('Please enter both email and password');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            // This is where you would typically make a real API call to authenticate
            const response = await axios.post(
                `${API_BASE_URL}/api/v1/login`,
                new URLSearchParams({
                    username: email,
                    password: password,
                }),
                { 
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    withCredentials: true
                }
            );

            if (response.data && response.data.access_token) {
                // Store the token in localStorage
                localStorage.setItem('api_token', response.data.access_token);

                // Call the onLoginSuccess callback to inform the parent component
                onLoginSuccess(response.data.access_token);
            } else {
                setError('Invalid response from server');
            }
        } catch (err) {
            console.error('Login error:', err.response?.data);

            // Provide a friendly error message
            setError(err.response?.data?.detail || 'Authentication failed. Please try again.');

            // For demo purposes only - allow login even when API fails
            // In a real app, you would remove this code
            if (email === 'demo@colonycraft.com' && password === 'demo123') {
                const demoToken = 'demo_token_' + Math.random().toString(36).substring(2);
                localStorage.setItem('api_token', demoToken);
                onLoginSuccess(demoToken);
            }
        } finally {
            // Only update state if component is still mounted
            if (isMounted.current) {
                setLoading(false);
            }
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <div className="login-header">
                    <h1>Colony<span>Craft</span></h1>
                    <p>Sign in to access AI models</p>
                </div>

                {error && (
                    <div className="login-error">
                        <span className="error-icon">!</span> {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input
                            type="email"
                            id="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="Enter your email"
                            disabled={loading}
                            autoComplete="email"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter your password"
                            disabled={loading}
                            autoComplete="current-password"
                        />
                    </div>

                    <button
                        type="submit"
                        className="login-button"
                        disabled={loading}
                    >
                        {loading ? 'Signing in...' : 'Sign In'}
                    </button>
                </form>

                <div className="login-footer">
                    <p>Don't have an account? <button onClick={switchToRegister} className="text-button">Sign Up</button></p>
                    <p className="demo-credentials">For demo, use: <code>demo@colonycraft.com</code> / <code>demo123</code></p>
                </div>
            </div>
        </div>
    );
};

export default LoginForm;
