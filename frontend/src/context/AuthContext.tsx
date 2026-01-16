import { createContext } from "react";
import type { AuthCtx } from "../types/auth";

export const AuthContext = createContext<AuthCtx | undefined>(undefined);
