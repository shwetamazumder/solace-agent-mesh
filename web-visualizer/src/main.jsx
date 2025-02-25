import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./index.css";

fetch("config.json")
  .then((response) => response.json())
  .then((config) => {
    window.config = config;
  })
  .catch((error) => {
    console.log("Could not load config", error.message);
  })
  .finally(() => {
    ReactDOM.createRoot(document.getElementById("root")).render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    );
  });
