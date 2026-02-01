import React, { useState, useEffect } from "react";
import { NavLink, useNavigate, useLocation } from "react-router-dom";

import { assets } from "../assets/assets_frontend/assets";
import { useAuth } from "../../hooks/useAuth";

const Navbar = (): React.JSX.Element => {
  const nav = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [showMenu, setShowMenu] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  const navItems = [
    { path: "/", label: "Home", testId: "home-link" },
    { path: "/doctors", label: "All Doctors", testId: "doctors-link" },
    { path: "/about", label: "About", testId: "about-link" },
    { path: "/contact", label: "Contact", testId: "contact-link" },
  ];

  const handleLogout = async () => {
    try {
      await logout();
    } catch (err) {
      console.error("Logout error: ", err);
    } finally {
      nav("/login");
    }
  };

  const userMenuItems = [
    {
      label: "My Profile",
      onClick: () => nav("/user-profile"),
      testId: "user-profile-button",
    },
    {
      label: "My Appointments",
      onClick: () => nav("/my-appointments"),
      testId: "my-appointments-button",
    },
    {
      label: "Logout",
      onClick: handleLogout,
      testId: "logout-button",
    },
  ];

  // Close menus when route changes
  useEffect(() => {
    setShowMenu(false);
    setShowDropdown(false);
  }, [location]);

  // Close mobile menu when resizing up to desktop
  useEffect(() => {
    const handleResize = () => {
      // Tailwind's md breakpoint is 768px
      if (window.innerWidth >= 768) {
        setShowMenu(false);
        setShowDropdown(false);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <nav
      className="flex items-center justify-between text-sm py-4 mb-5 border-b border-border-strong"
      aria-label="Main navigation"
    >
      {/* Logo */}
      <button
        onClick={() => nav("/")}
        className="w-44 cursor-pointer bg-transparent border-none p-0"
        aria-label="Go to home page"
        type="button"
      >
        <img src={assets.logo} alt="DocAppoint Logo" className="w-full" />
      </button>

      {/* Desktop Navigation */}
      <ul className="hidden md:flex items-start gap-5 font-medium">
        {navItems.map((item) => (
          <li key={item.path}>
            <NavLink
              to={item.path}
              className={({ isActive }) =>
                `py-1 block ${isActive ? "text-primary font-semibold" : "text-foreground"}`
              }
              end={item.path === "/"}
              data-testid={`desktop-${item.testId}`}
            >
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>

      {/* Right side actions */}
      <div className="flex items-center gap-4">
        {user ? (
          <div className="relative group hidden md:flex">
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              onMouseEnter={() => setShowDropdown(true)}
              onMouseLeave={() => setShowDropdown(false)}
              className="flex items-center gap-2 bg-transparent border-none p-0 cursor-pointer"
              aria-label="User menu"
              aria-expanded={showDropdown}
              aria-haspopup="true"
              data-testid="user-menu-button"
              type="button"
            >
              <img
                className="w-8 h-8 rounded-full object-cover"
                src={assets.profile_pic}
                alt={`${user.firstName || "User"} profile`}
                data-testid="user-avatar"
              />
              <img
                className="w-2.5"
                src={assets.dropdown_icon}
                alt=""
                aria-hidden="true"
              />
            </button>

            {/* Dropdown menu */}
            <div
              className={`absolute top-full right-0 pt-2 text-base font-medium text-muted z-20 transition-all duration-200 ${
                showDropdown ? "opacity-100 visible" : "opacity-0 invisible"
              }`}
              role="menu"
              aria-hidden={!showDropdown}
              id="user-dropdown-menu"
              onMouseEnter={() => setShowDropdown(true)}
              onMouseLeave={() => setShowDropdown(false)}
              data-testid="user-dropdown-menu"
            >
              <div className="min-w-48 bg-surface rounded-lg shadow-lg flex flex-col gap-2 p-3">
                {userMenuItems.map((item) => (
                  <button
                    key={item.label}
                    onClick={() => {
                      item.onClick();
                      setShowDropdown(false);
                    }}
                    className="text-left px-3 py-2 hover:bg-gray-50 rounded hover:text-foreground cursor-pointer w-full bg-transparent border-none"
                    role="menuitem"
                    data-testid={item.testId}
                    type="button"
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <button
            onClick={() => {
              if (location.pathname === "/signup") {
                nav("/login");
              } else {
                nav("/signup");
              }
            }}
            className="bg-primary text-background px-6 py-2.5 rounded-full font-medium hidden md:block hover:bg-primary-dark transition-colors"
            data-testid="auth-toggle-button"
            type="button"
          >
            {location.pathname === "/login" ? "Create Account" : "Login"}
          </button>
        )}

        {/* Mobile menu button */}
        <button
          onClick={() => setShowMenu(true)}
          className="w-6 h-6 md:hidden bg-transparent border-none p-0"
          aria-label="Open menu"
          aria-expanded={showMenu}
          type="button"
        >
          <img
            src={assets.menu_icon}
            alt=""
            aria-hidden="true"
            className="w-full h-full"
          />
          <span className="sr-only">Menu</span>
        </button>

        {/* Mobile menu overlay */}
        {showMenu && (
          <div
            className="fixed inset-0 z-20 bg-black bg-opacity-50 md:hidden"
            onClick={() => setShowMenu(false)}
            role="button"
            aria-label="Close menu"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                setShowMenu(false);
              }
            }}
          />
        )}

        {/* Mobile menu panel */}
        <aside
          className={`fixed top-0 right-0 bottom-0 z-30 bg-white w-64 transform transition-transform duration-300 ease-in-out md:hidden ${
            showMenu ? "translate-x-0" : "translate-x-full"
          }`}
          aria-label="Mobile navigation menu"
          aria-modal="true"
          role="dialog"
          aria-hidden={!showMenu}
        >
          <div className="flex items-center justify-between px-5 py-6 border-b">
            <button
              onClick={() => {
                nav("/");
                setShowMenu(false);
              }}
              className="w-36 bg-transparent border-none p-0"
              aria-label="Go to home page"
              type="button"
            >
              <img src={assets.logo} alt="DocAppoint Logo" className="w-full" />
            </button>
            <button
              onClick={() => setShowMenu(false)}
              className="w-7 h-7 bg-transparent border-none p-0"
              aria-label="Close menu"
              type="button"
            >
              <img
                src={assets.cross_icon}
                alt="Close menu"
                className="w-full h-full"
              />
            </button>
          </div>

          <nav className="mt-5 px-5">
            <ul className="flex flex-col gap-2 text-lg font-medium">
              {navItems.map((item) => (
                <li key={item.path}>
                  <button
                    onClick={() => {
                      nav(item.path);
                      setShowMenu(false);
                    }}
                    className="w-full text-left px-4 py-3 rounded hover:bg-gray-50 bg-transparent border-none"
                    data-testid={`mobile-${item.testId}`}
                    type="button"
                  >
                    {item.label}
                  </button>
                </li>
              ))}
            </ul>

            {user ? (
              <>
                <div className="my-6 border-t"></div>
                <ul className="flex flex-col gap-2 text-lg font-medium">
                  {userMenuItems.map((item) => (
                    <li key={item.label}>
                      <button
                        onClick={() => {
                          item.onClick();
                          setShowMenu(false);
                        }}
                        className={`w-full text-left px-4 py-3 rounded hover:bg-gray-50 bg-transparent border-none ${
                          item.label === "Logout" ? "btn-cancel" : ""
                        }`}
                        data-testid={`mobile-${item.testId}`}
                        type="button"
                      >
                        {item.label}
                      </button>
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              <div className="mt-8 pt-6 border-t">
                <button
                  onClick={() => {
                    if (location.pathname === "/signup") {
                      nav("/login");
                    } else {
                      nav("/signup");
                    }
                    setShowMenu(false);
                  }}
                  className="w-full bg-primary text-background px-6 py-3 rounded-full font-medium hover:bg-primary-dark transition-colors"
                  type="button"
                >
                  {location.pathname === "/login" ? "Create Account" : "Login"}
                </button>
              </div>
            )}
          </nav>
        </aside>
      </div>
    </nav>
  );
};

export default Navbar;
