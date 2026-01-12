import React from "react";
import { Banner, Header, SpecialtyMenu, TopDoctors } from "../components";
import { getMe } from "../api/auth";

const Home = (): React.JSX.Element => {
  getMe().then((data) => console.log(data));

  return (
    <div>
      <Header />
      <SpecialtyMenu />
      <TopDoctors />
      <Banner />
    </div>
  );
};

export default Home;
