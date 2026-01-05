export interface Speciality {
  id: number;
  name: string;
  image: string;
}

export interface SpecialitiesCtx {
  specialities: Speciality[] | null;
  loading: boolean;
  error: string | null;
  getSpecialities: () => Promise<void>;
}