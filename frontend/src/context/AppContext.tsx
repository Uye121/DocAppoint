import React from "react";
import { doctors } from "../assets/assets_frontend/assets";
import type { AppContextValue } from "../types/app";
import { AppContext } from "./app-context";

interface AppContextProviderProps {
  children: React.ReactNode;
}

const AppContextProvider: React.FC<AppContextProviderProps> = ({
  children,
}) => {
  const currencySymbol = "$";
  const value: AppContextValue = {
    currencySymbol,
    doctors,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export default AppContextProvider;
