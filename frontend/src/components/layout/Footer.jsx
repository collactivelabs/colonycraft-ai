import React from 'react';

export default function Footer() {
    return (
        <footer className="app-footer">
            <div className="footer-container">
                <p>&copy; {new Date().getFullYear()} ColonyCraft. All rights reserved.</p>
                <div className="footer-links">
                    <a href="/terms">Terms</a>
                    <a href="/privacy">Privacy</a>
                </div>
            </div>
        </footer>
    );
}
