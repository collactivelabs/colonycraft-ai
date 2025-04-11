import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import ThemeToggle from '../ui/ThemeToggle';

export default function Header() {
    const location = useLocation();
    
    return (
        <header className="app-header">
            <div className="header-container">
                <div className="logo">
                    <h1>Colony<span>Craft</span> AI</h1>
                </div>
                <nav className="main-nav">
                    <ul>
                        <li>
                            <Link 
                                to="/" 
                                className={location.pathname === '/' ? 'active' : ''}
                            >
                                Home
                            </Link>
                        </li>
                        <li>
                            <Link 
                                to="/about" 
                                className={location.pathname === '/about' ? 'active' : ''}
                            >
                                About
                            </Link>
                        </li>
                        <li>
                            <Link 
                                to="/contact" 
                                className={location.pathname === '/contact' ? 'active' : ''}
                            >
                                Contact
                            </Link>
                        </li>
                    </ul>
                </nav>
                <ThemeToggle />
            </div>
        </header>
    );
}
