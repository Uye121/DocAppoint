import React from "react";
import { Banner, Header, SpecialtyMenu, TopDoctors } from "../components";

const Home = (): React.JSX.Element => {
  return (
    <div data-testid="patient-home">
      <Header />
      <SpecialtyMenu />
      <TopDoctors />
      <Banner />
    </div>
  );
};

export default Home;
