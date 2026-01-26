import { assets } from "../assets/assets_frontend/assets";

interface DoctorCardProps {
  image: string | null | undefined;
  firstName: string;
  lastName: string;
  education: string;
  speciality: string | null;
  yearsOfExperience: number;
  about: string;
  fees: string;
}

const DoctorCard = ({
  image,
  firstName,
  lastName,
  education,
  speciality,
  yearsOfExperience,
  about,
  fees,
}: DoctorCardProps) => (
  <div className="flex flex-col sm:flex-row gap-4">
    <div>
      <img
        className="bg-primary w-full sm:max-w-72 rounded-lg"
        src={image || assets.doc0}
        alt="Doctor"
      />
    </div>

    <div className="flex-1 border border-gray-400 rounded-lg p-8 py-7 bg-white mx-2 sm:mx-0 mt-[-80px] sm:mt-0">
      <p className="flex items-center gap-2 text-2xl font-medium text-gray-900">
        {firstName} {lastName}
        <img className="w-5" src={assets.verified_icon} alt="verified" />
      </p>

      <div className="flex items-center gap-2 text-sm mt-1 text-gray-600">
        <span>
          {education} – {speciality}
        </span>
        <span className="py-0.5 px-2 border text-xs rounded-full">
          {yearsOfExperience}
        </span>
      </div>

      <div className="mt-3">
        <p className="flex items-center gap-1 text-sm font-medium text-gray-900">
          About <img src={assets.info_icon} alt="info" />
        </p>
        <p className="text-sm text-gray-500 max-w-[700px] mt-1">{about}</p>
      </div>

      <p className="text-gray-500 font-medium mt-4">
        Appointment fee: <span className="text-gray-600">${fees}</span>
      </p>
    </div>
  </div>
);

export default DoctorCard;
