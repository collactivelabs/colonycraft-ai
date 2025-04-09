module.exports = {
  env: {
    es6: true,
    node: true
  },
  parserOptions: {
    ecmaVersion: 2020 // Allows modern ECMAScript features
  },
  extends: [
    "eslint:recommended",
    "google" // Use Google's style guide
  ],
  rules: {
    "quotes": ["error", "double"],
    "max-len": ["warn", { "code": 120 }], // Allow longer lines
    "object-curly-spacing": ["error", "always"], // Enforce spacing in objects
    "indent": ["error", 2], // Enforce 2-space indentation
    "require-jsdoc": "off", // Disable requirement for JSDoc comments
    "valid-jsdoc": "off", // Disable validation of JSDoc comments
    "comma-dangle": ["error", "never"] // Disallow trailing commas
  }
};
