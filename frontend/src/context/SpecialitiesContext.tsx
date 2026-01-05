import { createContext } from 'react';
import type { SpecialitiesCtx } from '../types/specialities';

export const SpecialitiesContext = createContext<SpecialitiesCtx | undefined>(undefined);
