import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

// Register Form Component
const RegisterForm = ({ onRegisterSuccess, switchToLogin }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const isMounted = useRef(true);

    // Set up the cleanup when component unmounts
    useEffect(() => {
        return () => {
            isMounted.current = false;
        };
    }, []);

    const validateForm = () => {
        if (!email || !password || !confirmPassword) {
            setError('Please fill in all required fields');
            return false;
        }

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return false;
        }

        // Simple email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            setError('Please enter a valid email address');
            return false;
        }

        // Password strength validation (at least 8 chars, including numbers and letters)
        if (password.length < 8) {
            setError('Password must be at least 8 characters long');
            return false;
        }

        const hasLetter = /[a-zA-Z]/.test(password);
        const hasNumber = /\d/.test(password);
        if (!hasLetter || !hasNumber) {
            setError('Password must contain both letters and numbers');
            return false;
        }

        return true;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        setLoading(true);
        setError(null);

        try {
            // Make API call to register endpoint
            const response = await axios.post(
                `${API_BASE_URL}/api/v1/register`,
                {
                    email: email,
                    password: password,
                    full_name: fullName || undefined // Only send if provided
                },
                { 
                    headers: { 'Content-Type': 'application/json' },
                    withCredentials: true
                }
            );

            if (response.data && response.data.access_token) {
                // Store the token in localStorage
                localStorage.setItem('api_token', response.data.access_token);

                // Call the onRegisterSuccess callback to inform the parent component
                onRegisterSuccess(response.data.access_token);
            } else {
                setError('Invalid response from server');
            }
        } catch (err) {
            console.error('Registration error:', err.response?.data);

            // Provide a friendly error message
            setError(err.response?.data?.detail || 'Registration failed. Please try again.');
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
                    <p>Create your account</p>
                </div>

                {error && (
                    <div className="login-error">
                        <span className="error-icon">!</span> {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="form-group">
                        <label htmlFor="email">Email*</label>
                        <input
                            type="email"
                            id="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="Enter your email"
                            disabled={loading}
                            autoComplete="email"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="fullName">Full Name (Optional)</label>
                        <input
                            type="text"
                            id="fullName"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            placeholder="Enter your full name"
                            disabled={loading}
                            autoComplete="name"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password*</label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Create a password"
                            disabled={loading}
                            autoComplete="new-password"
                            required
                        />
                        <small className="form-hint">
                            Must be at least 8 characters with letters and numbers
                        </small>
                    </div>

                    <div className="form-group">
                        <label htmlFor="confirmPassword">Confirm Password*</label>
                        <input
                            type="password"
                            id="confirmPassword"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            placeholder="Confirm your password"
                            disabled={loading}
                            autoComplete="new-password"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        className="login-button"
                        disabled={loading}
                    >
                        {loading ? 'Creating Account...' : 'Create Account'}
                    </button>
                </form>

                <div className="login-footer">
                    <p>Already have an account? <button onClick={switchToLogin} className="text-button">Sign In</button></p>
                </div>
            </div>
        </div>
    );
};

export default RegisterForm;