import { describe, it } from "vitest";
import { render } from "@testing-library/react";
import DoctorCard from "../DoctorCard";

const props = {
  image: "dr.jpg",
  firstName: "a",
  lastName: "b",
  education: "MD",
  speciality: "Neurology",
  yearsOfExperience: 10,
  about: "Short bio",
  fees: "150",
};

describe("DoctorCard", () => {
  it("shows doctor data and fallback image", () => {
    const { getByText } = render(<DoctorCard {...props} />);
    expect(getByText("a b")).toBeInTheDocument();
    expect(getByText("MD – Neurology")).toBeInTheDocument();
    expect(getByText("10")).toBeInTheDocument();
    expect(getByText("$150")).toBeInTheDocument();
  });

  it("uses fallback image when none provided", () => {
    const { getByAltText } = render(<DoctorCard {...props} image={null} />);
    const img = getByAltText("Doctor") as HTMLImageElement;
    expect(img.src).toContain("doc0");
  });
});
