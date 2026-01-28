import clsx from "clsx";
import { formatInTimeZone } from "date-fns-tz";

import type { AppointmentListItem } from "../types/appointment";
import { assets } from "../assets/assets_frontend/assets";

interface AppointmentCardProps {
  item: AppointmentListItem;
  isPast?: boolean;
}

const AppointmentCard = ({ item, isPast = false }: AppointmentCardProps) => {
  const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  const canPayOrCancel = (status: string) =>
    status === "CONFIRMED" || status === "COMPLETED";

  const getStatusStyles = (status: string) => {
    switch (status) {
      case "REQUESTED":
        return "bg-status-requested";
      case "CONFIRMED":
        return "bg-status-confirmed";
      case "COMPLETED":
        return "bg-status-completed";
      case "RESCHEDULED":
        return "bg-status-rescheduled";
      case "CANCELLED":
        return "bg-status-cancelled";
      default:
        return "bg-surface text-muted";
    }
  };

  return (
    <article
      className={clsx(
        "flex items-center gap-4 p-4 bg-background border-border rounded-lg",
        !isPast && "hover:card-hover transition-all duration-200",
        isPast && "bg-surface",
      )}
    >
      {/* Provider Image */}
      <div className="shrink-0">
        <img
          className="w-20 h-20 rounded-lg object-cover bg-indigo-50"
          src={item.providerImage || assets.profile_pic}
          alt={`${item.providerName}'s profile`}
          loading="lazy"
          width={80}
          height={80}
        />
      </div>

      {/* Appointment Details */}
      <div className="flex-1 min-w-0">
        <h3 className="text-foreground font-semibold text-(length:--font-size-base) truncate">
          {item.providerName}
        </h3>

        <div className="space-y-1 mt-1 text-(length:--font-size-sm)">
          <p className="text-muted">
            {formatInTimeZone(
              item.appointmentStartDatetimeUtc,
              userTimeZone,
              "EEEE, MMM d 'at' h:mm a",
            )}
          </p>
          <p className="text-muted-foreground line-clamp-2">{item.reason}</p>
        </div>
      </div>

      {/* Status/Actions */}
      <div className="shrink-0 flex flex-col items-end gap-2">
        {!isPast && canPayOrCancel(item.status) ? (
          <>
            <button
              className="btn btn-primary px-3 py-1.5 text-(length:--font-size-xs) border rounded hover:bg-primary hover:text-white transition"
              aria-label={`Pay for appointment with ${item.providerName}`}
            >
              Pay Now
            </button>
            <button
              className="btn btn-danger px-3 py-1.5 text-(length:--font-size-xs) border rounded bg-red-50 text-red-700 hover:bg-red-600 hover:text-white transition"
              aria-label={`Cancel appointment with ${item.providerName}`}
            >
              Cancel
            </button>
          </>
        ) : (
          <span
            className={clsx(
              "px-3 py-1 rounded-md text-(length:--font-size-xs) font-medium",
              getStatusStyles(item.status),
            )}
          >
            {item.status}
          </span>
        )}
      </div>
    </article>
  );
};
export default AppointmentCard;
