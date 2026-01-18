export interface Hospital {
  id: number;
  name: string;
  address: string;
  phoneNumber: string;
  timezone: string;
  isRemoved: boolean;
  removedAt: string | null;
}
