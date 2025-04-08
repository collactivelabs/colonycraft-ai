const functions = require("firebase-functions/v2");
const {onRequest} = functions.https;
const logger = require("firebase-functions/logger");
const {initializeApp} = require("firebase-admin/app");
const cors = require("cors")({
  origin: "*",
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization", "X-API-Key"],
  credentials: true,
});
const axios = require("axios");
const jwt = require("jsonwebtoken");

initializeApp();

// Runtime options to specify Node.js 20
const runtimeOptions = {
  memory: "256MiB", // Default memory
  timeoutSeconds: 60, // 60 seconds timeout
  minInstances: 0, // Scale to zero when not in use
  concurrency: 80, // Maximum concurrent executions
  cpu: 1, // CPU allocation
  region: "us-central1", // Region
  runtime: "nodejs20", // Using Node.js 20
};

// Validate client token
const validateToken = (token) => {
  try {
    // Use the same secret key as your FastAPI backend
    const decoded = jwt.verify(token, process.env.SECRET_KEY);

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
          return res.status(405).json({error: "Method not allowed. Use POST."});
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
  });

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
            error: "Method not allowed. Use POST."});
        }

        // Validate the authorization token
        const authHeader = req.headers.authorization;
        if (!authHeader || !authHeader.startsWith("Bearer ")) {
          return res.status(401).json({
            error: "Missing or invalid authorization header"});
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
        const {
          model = "gpt-4o",
          prompt,
          maxTokens = 1024,
          temperature = 0.7,
        } = req.body;

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
        });
      }
    });
  });

// Get Available LLM Providers
exports.listProviders = onRequest(
  runtimeOptions, // Add runtime options here
  (req, res) => {
    return cors(req, res, () => {
    // Handle preflight request
      if (req.method === "OPTIONS") {
        res.set("Access-Control-Allow-Origin", "*");
        res.set("Access-Control-Allow-Methods", "GET, OPTIONS");
        res.set("Access-Control-Allow-Headers",
          "Content-Type, Authorization, X-API-Key");
        return res.status(204).send("");
      }

      // Only allow GET requests
      if (req.method !== "GET") {
        return res.status(405).json({error: "Method not allowed. Use GET."});
      }

      const providers = [
        {
          name: "anthropic",
          models: [
            {
              id: "claude-3-haiku-20240307",
              name: "Claude 3 Haiku",
              provider: "anthropic",
              description: "Fastest and most compact Claude model",
            },
            {
              id: "claude-3-sonnet-20240229",
              name: "Claude 3 Sonnet",
              provider: "anthropic",
              description: "Balanced model for most tasks",
            },
            {
              id: "claude-3-opus-20240229",
              name: "Claude 3 Opus",
              provider: "anthropic",
              description: "Most powerful Claude model for complex tasks",
            },
          ],
        },
        {
          name: "openai",
          models: [
            {
              id: "gpt-4o",
              name: "GPT-4o",
              provider: "openai",
              description: "Most capable GPT-4o model",
            },
            {
              id: "gpt-4-turbo",
              name: "GPT-4 Turbo",
              provider: "openai",
              description: "More efficient version of GPT-4",
            },
            {
              id: "gpt-3.5-turbo",
              name: "GPT-3.5 Turbo",
              provider: "openai",
              description: "Efficient model balancing cost and capability",
            },
          ],
        },
      ];

      res.status(200).json(providers);
    });
  });

// Simple test function
exports.helloWorld = onRequest((request, response) => {
  logger.info("Hello logs!", {structuredData: true});
  response.send("Hello from Firebase!");
});
