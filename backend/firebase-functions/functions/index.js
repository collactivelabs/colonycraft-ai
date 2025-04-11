const functions = require("firebase-functions/v2");
const {onRequest} = functions.https;
const logger = require("firebase-functions/logger");
const admin = require("firebase-admin");
const cors = require("cors")({
  origin: "*",
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization", "X-API-Key"],
  credentials: true,
});
const axios = require("axios");
const jwt = require("jsonwebtoken");

admin.initializeApp();

// Runtime options to specify Node.js 20
const runtimeOptions = {
  memory: "256MB", // Default memory
  timeoutSeconds: 60, // 60 seconds timeout
  minInstances: 0, // Scale to zero when not in use
  concurrency: 80, // Maximum concurrent executions
  cpu: 1, // CPU allocation
  region: "us-central1", // Region
  runtime: "nodejs20", // Using Node.js 20
  invoker: "public",
};

// Validate client token
const validateToken = (token) => {
  try {
    // Use only the environment variable for the secret key
    const secretKey = process.env.SECRET_KEY;

    if (!secretKey) {
      throw new Error("Secret key not configured");
    }

    const decoded = jwt.verify(token, secretKey);

    // Check if token is expired
    const now = Math.floor(Date.now() / 1000);
    if (decoded.exp <= now) {
      throw new Error("Token expired");
    }

    return decoded;
  } catch (error) {
    throw new Error(`Invalid token: ${error.message}`);
  }
};

// Anthropic LLM Function with token validation
exports.anthropicGenerate = onRequest(
  runtimeOptions, // Add runtime options here
  async (req, res) => {
    return cors(req, res, async () => {
      try {
        // Handle preflight request
        if (req.method === "OPTIONS") {
          res.set("Access-Control-Allow-Origin", "*");
          res.set("Access-Control-Allow-Methods", "POST, OPTIONS");
          res.set("Access-Control-Allow-Headers",
            "Content-Type, Authorization, X-API-Key");
          return res.status(204).send("");
        }

        // Only allow POST requests
        if (req.method !== "POST") {
          return res.status(405).json({
            error: "Method not allowed. Use POST.",
          });
        }

        // Validate the authorization token
        const authHeader = req.headers.authorization;
        if (!authHeader || !authHeader.startsWith("Bearer ")) {
          return res.status(401).json({
            error: "Missing or invalid authorization header",
          });
        }

        const token = authHeader.split(" ")[1];
        try {
          // Validate the token
          const decToken = validateToken(token);

          // You can use decodedToken.uid to identify the user
          console.log(`Request from user: ${decToken.sub}`);
        } catch (error) {
          return res.status(401).json({error: error.message});
        }

        // Extract request data
        const {model = "claude-3-sonnet-20240229",
          prompt, maxTokens = 1024, temperature = 0.7} = req.body;

        if (!prompt) {
          return res.status(400).json({error: "Prompt is required"});
        }

        // Get API key from environment variables
        const apiKey = process.env.ANTHROPIC_API_KEY;
        if (!apiKey) {
          return res.status(500).json({error: "API key not configured"});
        }

        // Make request to Anthropic API
        const response = await axios.post(
          "https://api.anthropic.com/v1/messages",
          {
            model,
            messages: [{role: "user", content: prompt}],
            max_tokens: maxTokens,
            temperature,
          },
          {
            headers: {
              "x-api-key": apiKey,
              "anthropic-version": "2023-06-01",
              "content-type": "application/json",
            },
          },
        );

        // Format and return the response
        const result = {
          text: response.data.content[0].text,
          model_info: {
            provider: "anthropic",
            model,
            version: "latest",
          },
          metadata: {
            usage: {
              input_tokens: response.data.usage.input_tokens,
              output_tokens: response.data.usage.output_tokens,
            },
            id: response.data.id,
          },
        };

        res.status(200).json(result);
      } catch (error) {
        console.error("Error calling Anthropic API:", error);

        // Return appropriate error response.
        const status = error.response ? error.response.status : 500;
        const message = error.response &&
          error.response.data &&
          error.response.data.error ?
          error.response.data.error.message :
          error.message;

        res.status(status).json({
          error: message,
        });
      }
    });
  },
);

// OpenAI LLM Function
exports.openaiGenerate = onRequest(
  runtimeOptions, // Add runtime options here
  async (req, res) => {
    return cors(req, res, async () => {
      try {
        // Handle preflight request
        if (req.method === "OPTIONS") {
          res.set("Access-Control-Allow-Origin", "*");
          res.set("Access-Control-Allow-Methods", "POST, OPTIONS");
          res.set("Access-Control-Allow-Headers",
            "Content-Type, Authorization, X-API-Key");
          return res.status(204).send("");
        }

        // Only allow POST requests
        if (req.method !== "POST") {
          return res.status(405).json({
            error: "Method not allowed. Use POST.",
          });
        }

        // Validate the authorization token
        const authHeader = req.headers.authorization;
        if (!authHeader || !authHeader.startsWith("Bearer ")) {
          return res.status(401).json({
            error: "Missing or invalid authorization header",
          });
        }

        const token = authHeader.split(" ")[1];
        try {
          // Validate the token
          const decToken = validateToken(token);
          // You can use decodedToken.uid to identify the user
          console.log(`Request from user: ${decToken.sub}`);
        } catch (error) {
          return res.status(401).json({error: error.message});
        }

        // Check if the request body is empty
        if (!req.body) {
          return res.status(400).json({error: "Request body is empty"});
        }

        // Extract request data
        const {model = "gpt-4o",
          prompt, maxTokens = 1024, temperature = 0.7} = req.body;

        if (!prompt) {
          return res.status(400).json({error: "Prompt is required"});
        }

        // Get API key from environment variables
        const apiKey = process.env.OPENAI_API_KEY;
        if (!apiKey) {
          return res.status(500).json({error: "API key not configured"});
        }

        // Make request to OpenAI API
        const response = await axios.post(
          "https://api.openai.com/v1/chat/completions",
          {
            model,
            messages: [{role: "user", content: prompt}],
            max_tokens: maxTokens,
            temperature,
          },
          {
            headers: {
              "Authorization": `Bearer ${apiKey}`,
              "Content-Type": "application/json",
            },
          },
        );

        // Format and return the response
        const result = {
          text: response.data.choices[0].message.content,
          model_info: {
            provider: "openai",
            model,
            version: "latest",
          },
          metadata: {
            usage: response.data.usage,
            id: response.data.id,
          },
        };

        res.status(200).json(result);
      } catch (error) {
        console.error("Error calling OpenAI API:", error);

        // Return appropriate error response
        const status = error.response ? error.response.status : 500;
        const message = error.response &&
          error.response.data &&
          error.response.data.error ?
          error.response.data.error.message :
          error.message;

        res.status(status).json({
          error: message,
          details: error.message,
        });
      }
    });
  },
);

// Ollama LLM Function (Proxies to Backend)
exports.ollamaGenerate = onRequest(
  runtimeOptions,
  async (req, res) => {
    return cors(req, res, async () => {
      try {
        // Handle preflight request
        if (req.method === "OPTIONS") {
          res.set("Access-Control-Allow-Origin", "*");
          res.set("Access-Control-Allow-Methods", "POST, OPTIONS");
          res.set("Access-Control-Allow-Headers",
            "Content-Type, Authorization"); // No X-API-Key needed for proxy
          return res.status(204).send("");
        }

        // Only allow POST requests
        if (req.method !== "POST") {
          return res.status(405).json({
            error: "Method not allowed. Use POST.",
          });
        }

        // Validate the authorization token
        const authHeader = req.headers.authorization;
        if (!authHeader || !authHeader.startsWith("Bearer ")) {
          return res.status(401).json({
            error: "Missing or invalid authorization header",
          });
        }

        const token = authHeader.split(" ")[1];
        try {
          // Validate the token
          const decodedToken = validateToken(token);
          // Log user making the request
          logger.info(`Ollama request initiated by user: ${decodedToken.sub}`);
          logger.info("Token verified successfully for ollamaGenerate");
        } catch (error) {
          logger.error(`Token validation failed: ${error.message}`);
          return res.status(401).json({error: error.message});
        }

        // Extract request data
        const {model, prompt, options} = req.body;

        if (!model) {
          return res.status(400).json({error: "Model is required"});
        }
        if (!prompt) {
          return res.status(400).json({error: "Prompt is required"});
        }

        // --- Proxy the request to the backend API ---
        const backendApiUrl = process.env.BACKEND_API_URL ||
          "http://localhost:8000";
        const backendEndpoint = `${backendApiUrl}/api/v1/llm/generate`;

        const backendPayload = {
          provider: "ollama", // Specify ollama provider
          model,
          prompt,
          options: options || {}, // Pass through any additional options
        };

        logger.info(`Proxying Ollama request to backend: ${backendEndpoint}`);

        // Use the validated token to authenticate with the backend
        const backendResponse = await axios.post(
          backendEndpoint,
          backendPayload,
          {
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${token}`,
            },
          },
        );

        // Forward the backend response to the client
        res.status(backendResponse.status).json(backendResponse.data);
      } catch (error) {
        logger.error("Error proxying Ollama request to backend:", error);

        if (axios.isAxiosError(error) && error.response) {
          // Forward the backend error response
          logger.error(`Backend error response: ${error.response.status} - ` +
            `${JSON.stringify(error.response.data)}`);
          res.status(error.response.status).json(error.response.data);
        } else {
          // General server error
          res.status(500).json({
            error: "Error occurred while processing the Ollama request.",
            details: error.message,
          });
        }
      }
    });
  },
);

// Function to handle Mistral AI generation requests
exports.mistralGenerate = onRequest(
  runtimeOptions,
  async (req, res) => {
    cors(req, res, async () => {
      logger.info("mistralGenerate function invoked");

      // Handle preflight request
      if (req.method === "OPTIONS") {
        res.set("Access-Control-Allow-Origin", "*");
        res.set("Access-Control-Allow-Methods", "POST, OPTIONS");
        res.set("Access-Control-Allow-Headers",
          "Content-Type, Authorization, X-API-Key");
        return res.status(204).send("");
      }

      // Only allow POST requests
      if (req.method !== "POST") {
        return res.status(405).json({
          error: "Method not allowed. Use POST.",
        });
      }

      const authHeader = req.headers.authorization;
      let token = null;
      if (authHeader) {
        const parts = authHeader.split(" ");
        if (parts.length === 2) {
          token = parts[1];
        }
      }

      if (!token) {
        logger.warn("Authorization token missing or header format incorrect");
        res.status(401).send("Unauthorized");
        return;
      }

      try {
        // Verify the token
        try {
          // Validate the token
          const decodedToken = validateToken(token);
          // Log user making the request
          logger.info(`Mistral request initiated by user: ${decodedToken.sub}`);
          logger.info("Token verified successfully for mistralGenerate");
        } catch (error) {
          logger.error(`Token validation failed: ${error.message}`);
          return res.status(401).json({error: error.message});
        }

        // Extract request data
        const {model, prompt, options} = req.body;
        if (!model || !prompt) {
          logger.warn("Missing model or prompt in request body");
          res.status(400).send("Bad Request: Missing model or prompt");
          return;
        }

        const backendApiUrl = process.env.BACKEND_API_URL ||
          "http://localhost:8000";

        const backendEndpoint = `${backendApiUrl}/api/v1/llm/generate`;
        const backendPayload = {
          provider: "mistral", // Set provider to mistral
          model: model,
          prompt: prompt,
          options: options || {},
        };

        logger.info(
          `Forwarding request to backend: ${backendEndpoint}`,
          {token: token, payload: backendPayload},
        );

        const backendResponse = await axios.post(
          backendEndpoint,
          backendPayload,
          {
            headers: {
              "Authorization": `Bearer ${token}`, // Forward the original token
              "Content-Type": "application/json",
            },
          },
        );

        logger.info(
          "Received response from backend",
          {status: backendResponse.status, payload: backendResponse.data},
        );
        res.status(backendResponse.status).json(backendResponse.data);
      } catch (error) {
        logger.error("Error in mistralGenerate function:", error);
        if (error.code === "auth/id-token-expired" ||
          error.code === "auth/argument-error") {
          res.status(401).send("Unauthorized: Invalid or expired token");
        } else if (error.response) {
          // Error from backend API
          logger.error(
            "Backend API error:",
            {status: error.response.status, data: error.response.data},
          );
          res.status(error.response.status).json(error.response.data);
        } else {
          res.status(500).send("Internal Server Error");
        }
      }
    });
  },
);

// V2 syntax for onRequest with region and runtime options
exports.googleGenerate = onRequest(
  runtimeOptions,
  (req, res) => {
    cors(req, res, async () => {
      logger.info("googleGenerate function invoked");

      // Handle preflight request
      if (req.method === "OPTIONS") {
        res.set("Access-Control-Allow-Origin", "*");
        res.set("Access-Control-Allow-Methods", "POST, OPTIONS");
        res.set("Access-Control-Allow-Headers",
          "Content-Type, Authorization, X-API-Key");
        return res.status(204).send("");
      }

      // Only allow POST requests
      if (req.method !== "POST") {
        return res.status(405).json({
          error: "Method not allowed. Use POST.",
        });
      }

      // --- Authentication --- Get and verify token ---
      const authHeader = req.headers.authorization;
      let token = null;
      if (authHeader) {
        const parts = authHeader.split(" ");
        if (parts.length === 2) {
          token = parts[1];
        }
      }
      if (!token) {
        logger.warn("Authorization token missing or incorrect format");
        res.status(401).send("Unauthorized: Token required");
        return;
      }

      // Validate token
      try {
        // Validate the token
        const decodedToken = validateToken(token);
        // Log user making the request
        logger.info(
          `Google Gemini request initiated by user: ${decodedToken.sub}`,
        );
        logger.info("Token verified successfully for googleGenerate");
      } catch (error) {
        logger.error(`Token validation failed: ${error.message}`);
        return res.status(401).json({error: error.message});
      }
      // --- End Authentication ---

      const {prompt, options} = req.body;

      if (!prompt) {
        logger.warn("googleGenerate: Missing prompt argument.");
        res.status(400).json({error: "Prompt is required"});
        return;
      }

      // Get API key from environment variables
      const apiKey = process.env.GEMINI_API_KEY;
      logger.info(`GEMINI API key: ${apiKey}`);
      if (!apiKey) {
        return res.status(500).json({error: "API key not configured"});
      }

      try {
        const llmRequest = {
          provider: "google",
          prompt: prompt,
          // Default model
          model: (options && options.model) || "gemini-1.5-flash",
          options: options || {},
        };

        logger.info(
          `Calling backend for Google Gemini: model=${llmRequest.model}`,
        );
        // Use the same makeBackendRequest helper (assuming it exists and works)
        // NOTE: makeBackendRequest was removed in a previous step,
        // re-implementing direct call logic here for consistency
        const backendApiUrl = process.env.BACKEND_API_URL ||
          "http://localhost:8000";
        const backendEndpoint = `${backendApiUrl}/api/v1/llm/generate`;

        const backendResponse = await axios.post(
          backendEndpoint,
          llmRequest,
          {
            headers: {
              "Authorization": `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            timeout: 120000, // Increased timeout
          },
        );

        logger.info("Backend response received (Google Gemini).");
        res.status(backendResponse.status).json(backendResponse.data);
      } catch (error) {
        logger.error("Error in googleGenerate function:", error);
        // Handle errors from backend or other issues
        if (error.response) {
          logger.error(
            "Backend API error (Google Gemini):",
            {status: error.response.status, data: error.response.data},
          );
          res.status(error.response.status).json(error.response.data);
        } else {
          res.status(500).json({
            error: "Internal Server Error",
            details: error.message || "An unexpected error occurred",
          });
        }
      }
    });
  },
);

// Endpoint to list available providers and models (proxies to backend)
exports.listProviders = onRequest(
  runtimeOptions, // Add runtime options here
  async (req, res) => {
    return cors(req, res, async () => {
      // Handle preflight request
      if (req.method === "OPTIONS") {
        res.set("Access-Control-Allow-Origin", "*");
        res.set("Access-Control-Allow-Methods", "GET, OPTIONS"); // Allow GET
        res.set("Access-Control-Allow-Headers",
          "Authorization"); // Only Authorization needed
        return res.status(204).send("");
      }

      // Only allow GET requests
      if (req.method !== "GET") {
        return res.status(405).json({error: "Method not allowed. Use GET."});
      }

      // Validate the authorization token (required to access backend endpoint)
      const authHeader = req.headers.authorization;
      let token = null;
      if (authHeader) {
        const parts = authHeader.split(" ");
        if (parts.length === 2) {
          token = parts[1];
        }
      }

      if (!token) {
        logger.warn("Authorization token missing or header format incorrect");
        res.status(401).send("Unauthorized");
        return;
      }

      try {
        const decodedToken = validateToken(token);
        logger.info(
          `List providers request by user: ${decodedToken.sub}`,
          {token: token},
        );
      } catch (error) {
        logger.error(
          `Token validation failed for listProviders: ${error.message}`,
          {token: token},
        );
        return res.status(401).json({error: error.message});
      }

      // --- Proxy the request to the backend API ---
      const backendApiUrl = process.env.BACKEND_API_URL || "http://localhost:8000";
      const backendEndpoint = `${backendApiUrl}/api/v1/llm/providers`;

      logger.info(
        `Proxying listProviders request to backend: ${backendEndpoint}`,
        {token: token},
      );

      try {
        const backendResponse = await axios.get(
          backendEndpoint,
          {
            headers: {
              "Authorization": `Bearer ${token}`, // Forward validated token
            },
          },
        );
        res.status(backendResponse.status).json(backendResponse.data);
      } catch (error) {
        logger.error("Error proxying listProviders request to backend:", error);
        if (axios.isAxiosError(error) && error.response) {
          logger.error(`Backend error response: ${error.response.status} - ` +
            `${JSON.stringify(error.response.data)}`);
          res.status(error.response.status).json(error.response.data);
        } else {
          res.status(500).json({
            error: "An unexpected error occurred while listing providers.",
            details: error.message,
          });
        }
      }
    });
  },
);

// Simple test function
exports.helloWorld = onRequest((request, response) => {
  logger.info("Hello logs!", {structuredData: true});
  response.send("Hello from Firebase!");
});
