export const VERIFY_STATUS = {
  LOADING: 'Loading',
  FAILURE: 'Failure',
  SUCCESSFUL: 'Successful',
} as const;
export type VerifyStatus = typeof VERIFY_STATUS[keyof typeof VERIFY_STATUS];