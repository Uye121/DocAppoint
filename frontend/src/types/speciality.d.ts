export interface Speciality {
  id: number;
  name: string;
  image: string;
}

export interface SpecialityCtx {
  specialities: Speciality[] | null;
  loading: boolean;
  error: string | null;
  getSpecialities: () => Promise<Speciality[]>;
}
