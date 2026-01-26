import React, { ReactElement, ReactNode } from "react";
import { render } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";

import { AuthCtx } from "../src/types/auth";
import { AuthContext } from "../src/context";

export const renderHookInProvider = (
  hook: () => unknown,
  {
    provider: Provider,
    props = {},
  }: { provider: React.FC<{ children: ReactNode }>; props?: object },
) => {
  let result: unknown;
  const Test = () => {
    result = hook();
    return null;
  };
  render(
    <Provider {...props}>
      <Test />
    </Provider>,
  );
  return result;
};

export const renderWithRouter = (
  ui: ReactElement,
  {
    path = "/",
    initialEntries = [path],
    authValue,
    providers = [],
  }: {
    path?: string;
    initialEntries?: string[];
    authValue?: Partial<AuthCtx>;
    providers?: Array<React.FC<{ children: ReactNode }>>;
  } = {},
) => {
  function Wrapper({ children }: { children: ReactNode }) {
    const defaultAuth: AuthCtx = {
      user: null,
      loading: false,
      login: vi.fn(),
      signup: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    };

    let tree = children;
    for (const Prov of providers) {
      tree = <Prov>{tree}</Prov>;
    }

    tree = (
      <AuthContext.Provider value={{ ...defaultAuth, ...authValue }}>
        {tree}
      </AuthContext.Provider>
    );

    return (
      <MemoryRouter initialEntries={initialEntries}>
        <Routes>
          <Route path={path} element={tree} />
          <Route path="/login" element={<div>login</div>} />
          <Route path="/" element={<div>home</div>} />
          <Route path="/onboard" element={<div>onboard</div>} />
        </Routes>
      </MemoryRouter>
    );
  }
  return render(ui, { wrapper: Wrapper });
};
