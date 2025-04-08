import React, { useState } from 'react';
import LoginForm from './Login';
import RegisterForm from './Register';

const AuthContainer = ({ onLoginSuccess }) => {
    const [isLoginView, setIsLoginView] = useState(true);

    const switchToRegister = () => {
        setIsLoginView(false);
    };

    const switchToLogin = () => {
        setIsLoginView(true);
    };

    return (
        <div className="auth-container">
            {isLoginView ? (
                <LoginForm 
                    onLoginSuccess={onLoginSuccess} 
                    switchToRegister={switchToRegister} 
                />
            ) : (
                <RegisterForm 
                    onRegisterSuccess={onLoginSuccess} 
                    switchToLogin={switchToLogin} 
                />
            )}
        </div>
    );
};

export default AuthContainer;
