import { createContext } from 'react';
import type { DoctorCtx } from '../types/doctor';

export const DoctorContext = createContext<DoctorCtx | undefined>(undefined);
