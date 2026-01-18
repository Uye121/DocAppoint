import { formatInTimeZone } from "date-fns-tz";
import type { Slot } from "../types/appointment";

interface SlotListProps {
  slots: Slot[];
  userTz: string;
  selectedId: string | null;
  onSelect: (slot: Slot) => void;
}

const SlotList = ({ slots, userTz, selectedId, onSelect }: SlotListProps) => {
  if (!slots.length)
    return (
      <p className="text-center text-gray-500">No available slots this day.</p>
    );

  return (
    <div className="space-y-2">
      {slots.map((slot) => {
        const isFree = slot.status === "FREE";
        const hospitalTz = slot.hospitalTimezone ?? "America/New_York";

        const hospitalNow = formatInTimeZone(
          new Date(),
          hospitalTz,
          "yyyy-MM-dd HH:mm:ss",
        );
        const hospitalStart = formatInTimeZone(
          slot.start,
          hospitalTz,
          "yyyy-MM-dd HH:mm:ss",
        );
        const isPast = hospitalStart < hospitalNow;

        const startLocal = formatInTimeZone(slot.start, userTz, "HH:mm");
        const endLocal = formatInTimeZone(slot.end, userTz, "HH:mm");

        return (
          <button
            key={slot.id}
            disabled={!isFree || isPast}
            onClick={() => isFree && !isPast && onSelect(slot)}
            className={
              "w-full rounded border px-4 py-3 text-left text-sm " +
              (selectedId === slot.id
                ? "border-primary bg-primary/10"
                : isFree && !isPast
                  ? "border-gray-200 hover:border-gray-400"
                  : "border-red-300 bg-red-50 text-red-700 cursor-not-allowed")
            }
          >
            <div className="flex justify-between items-center">
              <span>
                {startLocal} – {endLocal}
              </span>
              <span className="text-xs text-gray-500">{slot.hospitalName}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
};

export default SlotList;
