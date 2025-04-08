import React, { useState } from 'react';

const SimpleApp = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = () => {
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
  };

  if (!isLoggedIn) {
    return (
      <div style={{ padding: "20px", maxWidth: "500px", margin: "0 auto" }}>
        <h1>ColonyCraft AI - Login</h1>
        <p>Please log in to access the application.</p>
        <button onClick={handleLogin}>Sign In</button>
        <p>Don't have an account? <button>Sign Up</button></p>
      </div>
    );
  }

  return (
    <div style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h1>ColonyCraft AI</h1>
        <button onClick={handleLogout}>Logout</button>
      </header>
      <main>
        <h2>AI Chat Interface</h2>
        <p>Welcome! You are now logged in.</p>
      </main>
    </div>
  );
};

export default SimpleApp;
