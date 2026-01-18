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
  PatientOnboard,
  UserProfile,
  UserAppointment,
  Verify,
  VerifyEmail,
  ProviderHome,
  Landing,
} from "./pages";
import { Footer, Navbar, ProtectedRoutes, RoleGuard } from "./components";
import { SpecialitiesProvider, DoctorProvider } from "./context";

const App = (): React.JSX.Element => {
  return (
    <div className="mx-4 sm:mx-[10%]">
      <Navbar />
      <Routes>
        {/* public */}
        <Route path="/" element={<Landing />} />
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
            <Route
              path="/patient-home"
              element={
                <RoleGuard allowed={["patient"]}>
                  <Home />
                </RoleGuard>
              }
            />
            <Route path="/onboard" element={<PatientOnboard />} />
            <Route path="/doctors" element={<Doctors />} />
            <Route path="/doctors/:speciality" element={<Doctors />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/user-profile" element={<UserProfile />} />
            <Route path="/appointment" element={<Appointments />} />
            <Route path="/my-appointments" element={<UserAppointment />} />
            <Route path="/appointment/:docId" element={<Appointments />} />
            <Route
              path="/provider-home"
              element={
                <RoleGuard allowed={["provider"]}>
                  <ProviderHome />
                </RoleGuard>
              }
            />
          </Route>
        </Route>
      </Routes>
      <Footer />
    </div>
  );
};

export default App;
