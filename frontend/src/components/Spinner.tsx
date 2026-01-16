import React from "react";
import { SyncLoader } from "react-spinners";

interface SpinnerProps {
  loadingText?: string;
}

const Spinner = ({
  loadingText = "Loading data...",
}: SpinnerProps): React.JSX.Element => (
  <div className="flex flex-col items-center">
    <SyncLoader size={30} color="#38BDF8" loading />
    <p className="mt-4 text-zinc-600">{loadingText}</p>
  </div>
);

export default Spinner;
