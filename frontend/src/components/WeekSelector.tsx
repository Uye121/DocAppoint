import { format, formatISO } from "date-fns";

interface WeekSelectorProps {
  days: Date[];
  selectedDay: string;
  onSelect: (isoDay: string) => void;
}

const WeekSelector = ({ days, selectedDay, onSelect }: WeekSelectorProps) => {
  const now = new Date();
  const todayStr = formatISO(now, { representation: "date" });

  return (
    <div className="mb-4 border-b">
      <div className="flex gap-2">
        {days.map((day: Date) => {
          const dayKey = formatISO(day, { representation: "date" });
          const active = selectedDay === dayKey;
          const isPast = dayKey < todayStr;

          return (
            <button
              key={dayKey}
              disabled={isPast}
              onClick={() => onSelect(dayKey)}
              className={
                "px-4 py-2 text-sm font-medium border-b-2 transition " +
                (active
                  ? "border-primary text-primary"
                  : isPast
                    ? "border-transparent text-gray-300 cursor-not-allowed"
                    : "border-transparent text-gray-500 hover:text-gray-700")
              }
            >
              {format(day, "EEE d")}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default WeekSelector;
