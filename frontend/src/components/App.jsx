// React component for LLM chat
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import '../styles/App.css';
import AuthContainer from './auth/AuthContainer';
import Header from './layout/Header';
import Footer from './layout/Footer';
import ThemeToggle from './ui/ThemeToggle';
import ConversationManager from './conversation/ConversationManager';
import ChatInterface from './conversation/ChatInterface';
import { showExportDialog } from '../utils/exportConversation';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;
const FIREBASE_FUNCTIONS_URL = process.env.REACT_APP_FIREBASE_FUNCTIONS_URL;

const LLMChat = () => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [clientToken, setClientToken] = useState(null);
    const [tokenExpiry, setTokenExpiry] = useState(0);
    const [providers, setProviders] = useState([]);
    const [selectedProvider, setSelectedProvider] = useState('');
    const [selectedModel, setSelectedModel] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Check for existing token on component mount
    useEffect(() => {
        const storedToken = localStorage.getItem('api_token');
        if (storedToken) {
            setClientToken(storedToken);
            setIsAuthenticated(true);
        }
    }, []);

    // Handle successful login
    const handleLoginSuccess = (token) => {
        setClientToken(token);
        setIsAuthenticated(true);
    };

    // Handle logout
    const handleLogout = useCallback(() => {
        localStorage.removeItem('api_token');
        setClientToken(null);
        setIsAuthenticated(false);
        setProviders([]);
        setSelectedProvider('');
        setSelectedModel('');
    }, []);

    // Fetch client token from API
    const fetchClientToken = useCallback(async () => {
        try {
            const response = await axios.post(
                `${API_BASE_URL}/api/v1/auth/client-token`,
                {},
                {
                    headers: {
                        'Authorization': `Bearer ${clientToken}`,
                        'Content-Type': 'application/json'
                    },
                    withCredentials: true
                }
            );

            setClientToken(response.data.access_token);
            setTokenExpiry(response.data.expires_at);
            return response.data.access_token;
        } catch (err) {
            console.error('Error fetching client token:', err);
            setError('Authentication failed. Please log in again.');

            // If client token fetch fails, log the user out
            if (err.response?.status === 401) {
                handleLogout();
            }

            return null;
        }
    }, [clientToken, handleLogout]);

    // Fetch providers from API gateway
    const fetchProviders = useCallback(async () => {
        try {
            const response = await axios.get(
                `${API_BASE_URL}/api/v1/llm/providers`,
                {
                    headers: {
                        'Authorization': `Bearer ${clientToken}`,
                        'Content-Type': 'application/json'
                    },
                    withCredentials: true
                }
            );

            setProviders(response.data);

            if (response.data.length > 0) {
                setSelectedProvider(response.data[0].name);

                if (response.data[0].models.length > 0) {
                    setSelectedModel(response.data[0].models[0].id);
                }
            }
        } catch (err) {
            console.error('Error fetching providers:', err);
            setError('Failed to load LLM providers.');

            // If providers fetch fails due to authentication, log the user out
            if (err.response?.status === 401) {
                handleLogout();
            }
        }
    }, [clientToken, handleLogout]);

    // Check if token is valid or needs refresh
    const ensureValidToken = async () => {
        const now = Math.floor(Date.now() / 1000);

        // If token is missing or will expire in less than 60 seconds, get a new one
        if (!clientToken || (tokenExpiry && tokenExpiry - now < 60)) {
            return await fetchClientToken();
        }

        return clientToken;
    };

    // Generate response using Firebase Functions
    const generateResponse = async (prompt) => {
        if (!prompt.trim() || !selectedProvider || !selectedModel) {
            setError('Please enter a prompt and select a model.');
            return null;
        }

        setLoading(true);
        setError(null);

        try {
            // Make sure we have a valid token
            const token = await ensureValidToken();

            if (!token) {
                setLoading(false);
                return null;
            }

            // Call the appropriate Firebase function based on the provider
            let functionUrl;
            if (selectedProvider === 'anthropic') {
                functionUrl = `${FIREBASE_FUNCTIONS_URL}/anthropicGenerate`;
            } else if (selectedProvider === 'openai') {
                functionUrl = `${FIREBASE_FUNCTIONS_URL}/openaiGenerate`;
            } else if (selectedProvider === 'ollama') {
                functionUrl = `${FIREBASE_FUNCTIONS_URL}/ollamaGenerate`;
            } else if (selectedProvider === 'mistral') {
                functionUrl = `${FIREBASE_FUNCTIONS_URL}/mistralGenerate`;
            } else if (selectedProvider === 'google') {
                functionUrl = `${FIREBASE_FUNCTIONS_URL}/googleGenerate`;
            } else {
                throw new Error(`Unsupported provider: ${selectedProvider}`);
            }

            // Mock response for development if Firebase Functions URL is not set
            if (!FIREBASE_FUNCTIONS_URL) {
                // Simulate API delay
                await new Promise(resolve => setTimeout(resolve, 1500));

                // Return mock data
                const mockResponse = {
                    text: `This is a sample response for the prompt: "${prompt}"\n\nSince this is a development environment without a configured Firebase function URL, we're generating this mock response instead of calling an actual LLM API.`,
                    model_info: {
                        provider: selectedProvider,
                        model: selectedModel,
                        version: 'mock'
                    },
                    metadata: {
                        usage: {
                            input_tokens: prompt.length / 4, // Approximate token count
                            output_tokens: 50 // Fixed output token count for mock
                        },
                        id: 'mock_response_id'
                    }
                };

                setLoading(false);
                return mockResponse;
            }

            // Make the request to Firebase Function
            const response = await axios.post(
                functionUrl,
                {
                    model: selectedModel,
                    prompt: prompt,
                    maxTokens: 1024,  // Default or let user configure
                    temperature: 0.7  // Default or let user configure
                },
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                    // withCredentials option removed for Firebase Functions calls
                }
            );

            setLoading(false);
            return response.data;
        } catch (err) {
            console.error('Error generating response:', err);
            setError(err.response?.data?.error || 'Failed to generate response.');

            // If generation fails due to authentication, log the user out
            if (err.response?.status === 401) {
                handleLogout();
            }
            
            setLoading(false);
            throw err;
        }
    };

    // Handle provider change
    const handleProviderChange = (provider) => {
        setSelectedProvider(provider);
        // Reset model when provider changes
        const providerData = providers.find(p => p.name === provider);
        if (providerData && providerData.models.length > 0) {
            setSelectedModel(providerData.models[0].id);
        } else {
            setSelectedModel('');
        }
    };

    // Handle conversation management
    const [currentConversation, setCurrentConversation] = useState(null);
    
    // Handle loading a saved conversation
    const handleLoadConversation = (conversation) => {
        setCurrentConversation(conversation);
        
        // Set provider and model if available
        if (conversation.model_info) {
            setSelectedProvider(conversation.model_info.provider);
            setSelectedModel(conversation.model_info.model);
        }
    };

    // Handle saving a conversation
    const handleSaveConversation = (savedConversation) => {
        // This is handled by the ConversationManager component
        console.log('Conversation saved:', savedConversation.id);
    };

    // Handle exporting a conversation
    const handleExportConversation = (conversation) => {
        showExportDialog(conversation);
    };

    // Initialize providers when authenticated
    useEffect(() => {
        if (isAuthenticated) {
            fetchProviders();

            // Set up periodic token refresh
            const tokenRefreshInterval = setInterval(async () => {
                const now = Math.floor(Date.now() / 1000);

                // Refresh token if it's going to expire within 60 seconds
                if (tokenExpiry && tokenExpiry - now < 60) {
                    await fetchClientToken();
                }
            }, 30000); // Check every 30 seconds

            return () => {
                clearInterval(tokenRefreshInterval);
            };
        }
    }, [isAuthenticated, tokenExpiry, fetchClientToken, fetchProviders]);

    // Render login or register form if not authenticated
    if (!isAuthenticated) {
        return (
            <div className="app">
                <Header />
                <main className="main-content">
                    <AuthContainer onLoginSuccess={handleLoginSuccess} />
                </main>
                <Footer />
            </div>
        );
    }

    // Render chat interface if authenticated
    return (
        <div className="app">
            <header className="app-header">
                <div className="header-container">
                    <div className="logo">
                        <h1>Colony<span>Craft</span> AI</h1>
                    </div>
                    <nav className="main-nav">
                        <ul>
                            <li><a href="/" className="active">Home</a></li>
                            <li><a href="/about">About</a></li>
                            <li><a href="/contact">Contact</a></li>
                            <li><button type="button" onClick={(e) => { e.preventDefault(); handleLogout(); }} className="logout-link">Logout</button></li>
                        </ul>
                    </nav>
                    <ThemeToggle />
                </div>
            </header>

            <main className="main-content">
                <div className="llm-chat-container">
                    <h2>AI Chat Assistant</h2>

                    <ConversationManager 
                        currentConversation={currentConversation}
                        onLoadConversation={handleLoadConversation}
                        onSaveConversation={handleSaveConversation}
                        onExportConversation={handleExportConversation}
                    />

                    <ChatInterface 
                        providers={providers}
                        selectedProvider={selectedProvider}
                        selectedModel={selectedModel}
                        onProviderChange={handleProviderChange}
                        onModelChange={setSelectedModel}
                        onGenerateResponse={generateResponse}
                        loading={loading}
                        error={error}
                    />
                </div>
            </main>

            <Footer />
        </div>
    );
};

export default LLMChat;