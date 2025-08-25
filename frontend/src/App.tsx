import React from "react";
import { Route, Routes } from "react-router-dom";
import {
  About,
  Appointments,
  Contact,
  Doctors,
  Home,
  Login,
  UserProfile,
  UserAppointment,
} from "./pages";
import { Footer, Navbar } from "./components";

const App = (): React.JSX.Element => {
  return (
    <div className="mx-4 sm:mx-[10%]">
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/doctors" element={<Doctors />} />
        <Route path="/doctors/:speciality" element={<Doctors />} />
        <Route path="/login" element={<Login />} />
        <Route path="/about" element={<About />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/user-profile" element={<UserProfile />} />
        <Route path="/appointment" element={<Appointments />} />
        <Route path="/my-appointments" element={<UserAppointment />} />
        <Route path="/appointment/:docId" element={<Appointments />} />
      </Routes>
      <Footer />
    </div>
  );
};

export default App;
