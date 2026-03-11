import axios from "axios";

interface ApiErrorData {
  message?: string | string[];
  detail?: string;
  error?: string;
  non_field_errors?: string[];
  [key: string]: unknown;
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
    const data = err?.response?.data;

    if (typeof data === "string") {
      return data;
    }

    if (data && typeof data === "object") {
      const errorData = data as ApiErrorData;

      const fieldErrors = Object.values(errorData).find((value) =>
        Array.isArray(value),
      );
      if (fieldErrors && fieldErrors.length > 0) {
        return String(fieldErrors[0]);
      }

      if (errorData.message) {
        return Array.isArray(errorData.message)
          ? errorData.message[0]
          : errorData.message;
      }
      if (errorData.detail) return errorData.detail;
      if (errorData.error) return errorData.error;
      if (errorData.non_field_errors?.[0]) return errorData.non_field_errors[0];
    }

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
