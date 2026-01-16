module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:@typescript-eslint/recommended",
    "prettier", // disables ESLint rules that conflict with Prettier
  ],
  ignorePatterns: ["dist", ".eslintrc.js"],
  parser: "@typescript-eslint/parser",
  plugins: ["react-refresh"],
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    ecmaFeatures: { jsx: true },
  },
  rules: {
    "react-refresh/only-export-components": [
      "warn",
      { allowConstantExport: true },
    ],
  },
  settings: { react: { version: "detect" } },
};
