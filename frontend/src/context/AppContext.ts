import React from "react";
import { type AppContextValue } from "../types/app";

export const AppContext = React.createContext<AppContextValue>({
  doctors: [],
  currencySymbol: "$",
});
