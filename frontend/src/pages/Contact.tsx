import React from "react";
import { assets } from "../assets/assets_frontend/assets";

const Contact = (): React.JSX.Element => {
  return (
    <div>
      <div className="text-center text-2xl pt-10 text-gray-500">
        <p className="text-gray-700 font-semibold">CONTACT US</p>
      </div>
      <div className="my-10 flex flex-col justify-center md:flex-row gap-10 mb-28 text-sm">
        <img
          className="w-full md:max-w-[360px]"
          src={assets.contact_image}
          alt="contact iamge"
        />
        <div className="flex flex-col justify-center items-start gap-6">
          <p className="font-semibold text-lg text-gray-600">Our Office</p>
          <p className="text-gray-500">
            123 Broadway Blvd. <br />
            Suite 100, Washington, USA
          </p>
          <p className="text-gray-500">
            Tel: (123)456-7890 <br />
            Email: 123@docappoint.com
          </p>
          <p className="font-semibold text-lg text-gray-600">
            Career at DocAppoint
          </p>
          <p className="text-gray-500">
            Learn more about our teams and job openings.
          </p>
          <button className="border border-black px-8 py-4 text-sm hover:bg-black hover:text-white transition-all duration-500">
            Explroe Jobs
          </button>
        </div>
      </div>
    </div>
  );
};

export default Contact;
