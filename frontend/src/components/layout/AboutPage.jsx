import React from 'react';
import Header from './Header';
import Footer from './Footer';
import '../../styles/AboutPage.css';

const AboutPage = () => {
  return (
    <div className="app">
      <Header />
      <main className="main-content">
        <div className="about-container">
          <section className="about-hero">
            <div className="about-hero-content">
              <h1>About Colony<span>Craft</span> AI</h1>
              <p className="lead">
                A secure, unified gateway to multiple Large Language Models
              </p>
            </div>
          </section>

          <section className="about-section">
            <h2>Our Mission</h2>
            <p>
              ColonyCraft AI aims to democratize access to advanced artificial intelligence by providing
              a secure, reliable, and intuitive platform that connects users to a variety of large language models.
              We believe that AI should be accessible, transparent, and under user control, with robust
              protections for privacy and security.
            </p>
          </section>

          <section className="about-section">
            <h2>The Platform</h2>
            <p>
              ColonyCraft AI is a full-stack application that provides seamless access to multiple
              Large Language Models (LLMs) through a unified API gateway. We've integrated leading models from
              OpenAI, Anthropic, Google, Mistral, and open-source alternatives like Ollama, giving you
              the freedom to choose the right model for your needs.
            </p>
            
            <div className="feature-grid">
              <div className="feature-card">
                <div className="feature-icon"><span role="img" aria-label="Lock emoji">🔒</span></div>
                <h3>Secure Access</h3>
                <p>Enterprise-grade authentication and API key management to keep your data safe.</p>
              </div>
              
              <div className="feature-card">
                <div className="feature-icon"><span role="img" aria-label="Anticlockwise arrows button emoji">🔄</span></div>
                <p>Switch seamlessly between different LLM providers with a consistent interface.</p>
                <h3>Multi-Model Support</h3>
              </div>
              
              <div className="feature-card">
                <div className="feature-icon"><span role="img" aria-label="High voltage emoji">⚡</span></div>
                <h3>Optimized Performance</h3>
                <p>Rate limiting, caching, and background processing for responsive experiences.</p>
              </div>
              
              <div className="feature-card">
                <div className="feature-icon"><span role="img" aria-label="Floppy disk emoji">💾</span></div>
                <h3>Conversation Management</h3>
                <p>Save, categorize, and export your conversations for future reference.</p>
              </div>
            </div>
          </section>

          <section className="about-section">
            <h2>Technology Stack</h2>
            <p>
              Our platform is built with modern technologies designed for reliability, security, and scalability:
            </p>
            
            <div className="tech-stack">
              <div className="tech-category">
                <h3>Frontend</h3>
                <ul>
                  <li>React</li>
                  <li>Responsive CSS</li>
                  <li>Markdown Rendering</li>
                  <li>Theme System</li>
                </ul>
              </div>
              
              <div className="tech-category">
                <h3>Backend</h3>
                <ul>
                  <li>FastAPI (Python)</li>
                  <li>JWT Authentication</li>
                  <li>PostgreSQL</li>
                  <li>Redis Cache</li>
                </ul>
              </div>
              
              <div className="tech-category">
                <h3>LLM Integration</h3>
                <ul>
                  <li>OpenAI</li>
                  <li>Anthropic Claude</li>
                  <li>Google Gemini</li>
                  <li>Mistral AI</li>
                  <li>Ollama</li>
                </ul>
              </div>
              
              <div className="tech-category">
                <h3>Infrastructure</h3>
                <ul>
                  <li>Docker</li>
                  <li>Celery</li>
                  <li>Firebase Functions</li>
                  <li>Redis</li>
                </ul>
              </div>
            </div>
          </section>

          <section className="about-section">
            <h2>Our Team</h2>
            <p>
              ColonyCraft AI is developed by a team of engineers passionate about making AI tools
              more accessible, secure, and powerful. Our diverse backgrounds span machine learning,
              web development, security, and user experience design.
            </p>
            
            <div className="team-values">
              <div className="value-item">
                <h3>Privacy-Focused</h3>
                <p>We believe your data and conversations should remain private and secure.</p>
              </div>
              
              <div className="value-item">
                <h3>User-Centric</h3>
                <p>Every feature we build starts with user needs and experience in mind.</p>
              </div>
              
              <div className="value-item">
                <h3>Transparent</h3>
                <p>We're committed to being open about how our platform works and evolves.</p>
              </div>
              
              <div className="value-item">
                <h3>Adaptable</h3>
                <p>We continuously integrate new models and capabilities as the AI landscape evolves.</p>
              </div>
            </div>
          </section>

          <section className="about-section">
            <h2>Future Roadmap</h2>
            <p>
              We're constantly working to improve ColonyCraft AI with new features and capabilities:
            </p>
            
            <ul className="roadmap-list">
              <li>Multi-modal support for images and audio</li>
              <li>Vector search integration for knowledge bases</li>
              <li>Function calling capabilities</li>
              <li>Retrieval-augmented generation (RAG)</li>
              <li>Advanced analytics and monitoring</li>
              <li>Team collaboration features</li>
            </ul>
            
            <p className="note">
              Have a feature request or suggestion? We'd love to hear from you on our <a href="/contact">Contact page</a>.
            </p>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default AboutPage;