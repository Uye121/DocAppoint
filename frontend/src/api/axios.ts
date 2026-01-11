import axios from "axios";
import type { AxiosInstance, AxiosRequestConfig } from "axios";
import type { TokenPair } from "../types/auth";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

/* --------------- request interceptor --------------- */
api.interceptors.request.use((config) => {
  const access = localStorage.getItem("access");
  if (access) config.headers.Authorization = `Bearer ${access}`;
  return config;
});

/* --------------- response interceptor --------------- */
let isRefreshing: boolean = false;
let failedQueue: Array<(token: string | null) => void> = [];

const processQueue = (token: string | null) => {
  failedQueue.forEach((cb) => cb(token));
  failedQueue = []
};

api.interceptors.response.use(
  (res) => res, // Success path
  async (err) => {
    const originalRequest: AxiosRequestConfig & { _retry?: boolean } = err.config;

    // Intercept unauthorized access and try to refresh the access token
    if (err.response?.status === 401 && !originalRequest._retry) {
      // Move other request to queue if currently refreshing
      if (isRefreshing) {
        return new Promise<string>((resolve) => {
          failedQueue.push((token) => {
            if (token) originalRequest.headers!.Authorization = `Bearer ${token}`;

            resolve(api(originalRequest))
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;
      const refresh = localStorage.getItem("refresh");

      try {
        const { data } = await axios.post<TokenPair>(
          `${BASE_URL}/auth/token/refresh`,
          { refresh }
        );

        localStorage.setItem("access", data.access);
        api.defaults.headers.common["Authorization"] = `Bearer ${data.access}`;
        // Give the new valid access token token to all requests in failedQueue
        processQueue(data.access);
        // Resolve and re-execute the original request with the new token to
        // complete the request
        return api(originalRequest);
      } catch {
        processQueue(null); // empties failedQueue
        localStorage.clear();
        window.location.href = "/login";
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(err);
  }
);
