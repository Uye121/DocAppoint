import { it, expect } from "vitest";
import { renderWithRouter } from "../../../__tests__/utils";
import Header from "../Header";

it("links to #specialty section", () => {
  const { getByText } = renderWithRouter(<Header />);
  const link = getByText("Book Appointment").closest("a")!;
  expect(link.hash).toBe("#specialty");
});
