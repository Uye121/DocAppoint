export interface Hospital {
  id: number;
  name: string;
  address: string;
  phoneNumber: string;
  timezone: string;
  isRemoved: boolean;
  removedAt: string | null;
}

export interface HospitalTiny {
  id: number;
  name: string;
  address: string;
  timezone: string;
}
