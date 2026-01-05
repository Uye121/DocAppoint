import React from "react";
import { Outlet, Route, Routes } from "react-router-dom";
import {
  About,
  Appointments,
  Contact,
  Doctors,
  Home,
  Signup,
  Login,
  UserProfile,
  UserAppointment,
  Verify,
  VerifyEmail,
} from "./pages";
import { Footer, Navbar, ProtectedRoutes } from "./components";
import { SpecialitiesProvider, DoctorProvider } from "./context";

const App = (): React.JSX.Element => {
  return (
    <div className="mx-4 sm:mx-[10%]">
      <Navbar />
      <Routes>
        {/* public */}
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/verify" element={<Verify />} />
        <Route path="/verify-email" element={<VerifyEmail />} />

        {/* protected */}
        <Route element={<ProtectedRoutes />}>
          <Route
            element={
              <SpecialitiesProvider>
                <DoctorProvider>
                  <Outlet />
                </DoctorProvider>
              </SpecialitiesProvider>
            }
          >
            <Route path="/" element={<Home />} />
            <Route path="/doctors" element={<Doctors />} />
            <Route path="/doctors/:speciality" element={<Doctors />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/user-profile" element={<UserProfile />} />
            <Route path="/appointment" element={<Appointments />} />
            <Route path="/my-appointments" element={<UserAppointment />} />
            <Route path="/appointment/:docId" element={<Appointments />} />
          </Route>
        </Route>
      </Routes>
      <Footer />
    </div>
  );
};

export default App;
