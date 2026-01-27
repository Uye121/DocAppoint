import axios from "axios";

interface ApiErrorData {
  message?: string;
  detail?: string;
  error?: string;
}

const isAxiosError = (err: unknown): err is import("axios").AxiosError => {
  return axios.isAxiosError(err);
};

export const getErrorMessage = (
  err: unknown,
  defaultMsg: string = "An unexpected error occurred",
): string => {
  // Axios error
  if (isAxiosError(err)) {
    const data = err?.response?.data as ApiErrorData | undefined;
    const apiMessage = data?.message || data?.detail || data?.error;

    if (apiMessage) return String(apiMessage);

    return err.message || `Request failed with status ${err.response?.status}`;
  }

  // standard error
  if (err instanceof Error) return err.message;
  // string error
  if (typeof err === "string") return err;
  // error object
  if (typeof err === "object" && err !== null && "message" in err) {
    return String((err as { message: unknown }).message);
  }
  return defaultMsg;
};
