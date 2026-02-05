import { api } from "./axios";

import type { User } from "../types/user";

export const getMe = () => api.get<User>("/users/me").then((res) => res.data);
