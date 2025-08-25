export interface ISpeciality {
  speciality: string;
  image: string;
}

export interface IDoctor {
  _id: string;
  name: string;
  image: string;
  speciality: string;
  degree: string;
  experience: string;
  about: string;
  fees: number;
  address: {
    line1: string;
    line2: string;
  };
}

export interface TimeSlotType {
  datetime: Date;
  time: string;
}

export interface AppContextValue {
  currencySymbol: string;
  doctors: IDoctor[];
}
