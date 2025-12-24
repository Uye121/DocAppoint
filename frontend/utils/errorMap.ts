const FIELD_LABELS: Record<string, string> = {
  email: "Email",
  username: "Username",
  password: "Password",
  firstName: "Firstname",
  lastName: "Lastname",
  non_field_errors: "General",
};

export const formatErrors = (errs: Record<string, string[]>): string =>
  Object.entries(errs)
    .map(([key, arr]) => {
      const label = FIELD_LABELS[key] ?? key;
      return `${label}: ${arr.join(", ")}`;
    })
    .join("; ");
