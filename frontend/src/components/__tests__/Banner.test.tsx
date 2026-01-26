import { it, expect, vi } from "vitest";

import { renderWithRouter } from "../../../test/utils";
import Banner from "../Banner";

it("navigates to login and scrolls to top on button click", async () => {
  const scrollSpy = vi.fn();
  global.scrollTo = scrollSpy;

  const { getByText, findByText } = renderWithRouter(<Banner />, {
    initialEntries: ["/"],
  });

  const btn = getByText("Create account");
  btn.click();

  // wait for the new route to render
  expect(await findByText("login")).toBeInTheDocument();
  expect(scrollSpy).toHaveBeenCalledWith(0, 0);
});
