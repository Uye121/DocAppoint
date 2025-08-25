import React, { useState } from "react";

// TODO: Follow https://clerk.com/blog/building-a-react-login-page-template
// To separate login & sign up page + add validation
const Login = (): React.JSX.Element => {
  const [state, setState] = useState<string>("Sign Up");
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [name, setName] = useState<string>("");

  const onSubmit = async (event) => {
    event.preventDefault();
  };

  return (
    <form className="min-h-[80vh] flex items-center">
      <div className="flex flex-col gap-3 m-auto items-start p-8 min-w-[340px] sm:min-w-96 border rounded-xl text-zinc-600 text-sm shadow-lg">
        <p className="text-2xl font-semibold">
          {state == "Sign Up" ? "Create Account" : "Login"}
        </p>
        <p>Please sign up/login to get started.</p>
        {state == "Sign Up" && (
          <div className="w-full">
            <p>Full Name</p>
            <input
              type="text"
              className="border border-zinc-300 rounded w-full p-2 mt-1"
              onChange={(e) => setName(e.target.value)}
              value={name}
              required
            />
          </div>
        )}
        <div className="w-full">
          <p>Email</p>
          <input
            type="text"
            className="border border-zinc-300 rounded w-full p-2 mt-1"
            onChange={(e) => setEmail(e.target.value)}
            value={email}
            required
          />
        </div>
        <div className="w-full">
          <p>Password</p>
          <input
            type="password"
            className="border border-zinc-300 rounded w-full p-2 mt-1"
            onChange={(e) => setPassword(e.target.value)}
            value={password}
            required
          />
        </div>
        <button className="bg-primary text-white w-full py-2 rounded-md text-base">
          {state == "Sign Up" ? "Create Account" : "Login"}
        </button>
        {state == "Sign Up" ? (
          <p>
            Already have an account? Login{" "}
            <span
              onClick={() => setState("Login")}
              className="text-primary underline cursor-pointer"
            >
              here
            </span>
            .
          </p>
        ) : (
          <p>
            Create a new account{" "}
            <span
              onClick={() => setState("Sign Up")}
              className="text-primary underline cursor-pointer"
            >
              here
            </span>
            .
          </p>
        )}
      </div>
    </form>
  );
};

export default Login;
