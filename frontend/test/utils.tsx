import { ReactNode } from "react";
import { render } from "@testing-library/react";
import React from "react";

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
