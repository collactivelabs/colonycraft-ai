import React from 'react';

export default function Header() {
    return (
        <header className="app-header">
            <div className="header-container">
                <div className="logo">
                    <h1>Colony<span>Craft</span></h1>
                </div>
                <nav className="main-nav">
                    <ul>
                        <li><a href="/" className="active">Home</a></li>
                        <li><a href="/about">About</a></li>
                        <li><a href="/contact">Contact</a></li>
                    </ul>
                </nav>
            </div>
        </header>
    );
}
