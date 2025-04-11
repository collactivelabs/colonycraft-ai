import React, { useState } from 'react';
import Header from './Header';
import Footer from './Footer';
import '../../styles/ContactPage.css';

const ContactPage = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });
  
  const [formStatus, setFormStatus] = useState({
    submitted: false,
    success: false,
    message: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate form
    if (!formData.name || !formData.email || !formData.message) {
      setFormStatus({
        submitted: true,
        success: false,
        message: 'Please fill in all required fields.'
      });
      return;
    }
    
    // In a real application, you would send this data to a backend API
    // For now, we'll just simulate a successful submission
    setTimeout(() => {
      setFormStatus({
        submitted: true,
        success: true,
        message: 'Thanks for your message! We\'ll get back to you soon.'
      });
      
      // Reset form after successful submission
      setFormData({
        name: '',
        email: '',
        subject: '',
        message: ''
      });
    }, 1000);
  };

  return (
    <div className="app">
      <Header />
      <main className="main-content">
        <div className="contact-container">
          <section className="contact-header">
            <h1>Contact Us</h1>
            <p className="lead">
              Have questions about ColonyCraft AI? We're here to help.
            </p>
          </section>

          <div className="contact-content">
            <section className="contact-info">
              <div className="contact-method">
                <div className="contact-icon"><span role="img" aria-label="Envelope emoji">✉️</span></div>
                <h3>Email</h3>
                <p>
                  <a href="mailto:support@colonycraft.ai">support@colonycraft.ai</a>
                </p>
              </div>
              
              <div className="contact-method">
                <div className="contact-icon"><span role="img" aria-label="Telephone receiver emoji">📞</span></div>
                <h3>Phone</h3>
                <p>+1 (555) 123-4567</p>
                <p className="contact-note">Monday-Friday, 9am-5pm PST</p>
              </div>
              
              <div className="contact-method">
                <div className="contact-icon"><span role="img" aria-label="Globe with meridians emoji">🌐</span></div>
                <h3>Social</h3>
                <div className="social-links">
                  <a href="https://twitter.com/colonycraft" target="_blank" rel="noopener noreferrer">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z"></path>
                    </svg>
                  </a>
                  <a href="https://github.com/colonycraft" target="_blank" rel="noopener noreferrer">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                    </svg>
                  </a>
                  <a href="https://linkedin.com/company/colonycraft" target="_blank" rel="noopener noreferrer">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                      <rect x="2" y="9" width="4" height="12"></rect>
                      <circle cx="4" cy="4" r="2"></circle>
                    </svg>
                  </a>
                </div>
              </div>

              <div className="contact-support">
                <h3>Support Resources</h3>
                <ul>
                  <li>
                    <a href="/faq">Frequently Asked Questions</a>
                  </li>
                  <li>
                    <a href="/docs">API Documentation</a>
                  </li>
                  <li>
                    <a href="/guides">User Guides</a>
                  </li>
                  <li>
                    <a href="/tutorials">Video Tutorials</a>
                  </li>
                </ul>
              </div>
            </section>

            <section className="contact-form">
              <h3>Send us a message</h3>
              
              {formStatus.submitted && (
                <div className={`form-message ${formStatus.success ? 'success' : 'error'}`}>
                  {formStatus.message}
                </div>
              )}
              
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="name">Your Name *</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="email">Email Address *</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="subject">Subject</label>
                  <input
                    type="text"
                    id="subject"
                    name="subject"
                    value={formData.subject}
                    onChange={handleChange}
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="message">Message *</label>
                  <textarea
                    id="message"
                    name="message"
                    rows="5"
                    value={formData.message}
                    onChange={handleChange}
                    required
                  ></textarea>
                </div>
                
                <button type="submit" className="submit-btn">
                  Send Message
                </button>
              </form>
            </section>
          </div>

          <section className="contact-faq">
            <h2>Frequently Asked Questions</h2>
            
            <div className="faq-list">
              <div className="faq-item">
                <h4>How do I reset my password?</h4>
                <p>
                  You can reset your password by clicking on the "Forgot Password" link on the login page.
                  You'll receive an email with instructions to create a new password.
                </p>
              </div>
              
              <div className="faq-item">
                <h4>Which LLM providers do you support?</h4>
                <p>
                  We currently support OpenAI (GPT models), Anthropic (Claude models), Google (Gemini models),
                  Mistral AI, and Ollama for open-source models.
                </p>
              </div>
              
              <div className="faq-item">
                <h4>How is my data handled?</h4>
                <p>
                  We prioritize your privacy and security. Your conversations can be saved locally or in your account,
                  but we do not use your data to train models or share it with third parties. For more details,
                  please review our <a href="/privacy">Privacy Policy</a>.
                </p>
              </div>
              
              <div className="faq-item">
                <h4>Do you offer enterprise plans?</h4>
                <p>
                  Yes, we offer enterprise plans with additional features like SSO integration, dedicated support,
                  custom model deployment, and team collaboration tools. Contact our sales team at
                  <a href="mailto:sales@colonycraft.ai"> sales@colonycraft.ai</a> for more information.
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default ContactPage;