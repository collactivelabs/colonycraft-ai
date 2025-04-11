import React from 'react';
import { Link } from 'react-router-dom';

export default function Footer() {
    return (
        <footer className="app-footer">
            <div className="footer-container">
                <p>&copy; {new Date().getFullYear()} ColonyCraft AI. All rights reserved.</p>
                <div className="footer-links">
                    <Link to="/terms">Terms</Link>
                    <Link to="/privacy">Privacy</Link>
                    <Link to="/contact">Contact</Link>
                </div>
            </div>
        </footer>
    );
}
