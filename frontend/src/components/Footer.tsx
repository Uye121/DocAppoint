import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { assets } from "../assets/assets_frontend/assets";

const Footer = (): React.JSX.Element => {
  const nav = useNavigate();

  return (
    <div className="md:mx-10">
      <div className="flex flex-col sm:grid grid-cols-[3fr_1fr_1fr] gap-14 my-10 mt-40 text-sm">
        <div>
          <button
            onClick={() => nav("/")}
            className="cursor-pointer"
            aria-label="Go to home page"
            type="button"
          >
            <img className="mb-5 w-40" src={assets.logo} alt="logo" />
          </button>
          <p className="w-full md:w-2/3 text-gray-600 leading-6">
            Some dummy text about the company
          </p>
        </div>
        <div>
          <p className="text-xl font-medium mb-5">COMPANY</p>
          <ul className="flex flex-col gap-2 text-gray-600">
            <li>
              <Link to="/">Home</Link>
            </li>
            <li>
              <Link to="/about">About Us</Link>
            </li>
            <li>
              <Link to="/contact">Contact Us</Link>
            </li>
          </ul>
        </div>
        <div>
          <p className="text-xl font-medium mb-5">Get In Touch</p>
          <ul className="flex flex-col gap-2 text-gray-600">
            <li>+1-234-567-0000</li>
            <li>someemail@gmail.com</li>
          </ul>
        </div>
      </div>
      <div>
        <p className="py-5 text-sm text-center">
          Copyright 2025@DocAppoint - All Right Reserved.
        </p>
      </div>
    </div>
  );
};

export default Footer;
