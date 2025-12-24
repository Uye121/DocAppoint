import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App.tsx";
import AppContextProvider from "./context/AppContextProvider.js";
import { AuthProvider } from './context/AuthProvider.tsx';

createRoot(document.getElementById("root")!).render(
  <BrowserRouter>
    <AuthProvider>
      {/* <AppContextProvider> */}
        <App />
      {/* </AppContextProvider> */}
    </AuthProvider>
  </BrowserRouter>,
);
