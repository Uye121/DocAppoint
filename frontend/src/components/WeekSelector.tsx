import {
  eachDayOfInterval,
  format,
  formatISO,
  addWeeks,
  endOfWeek,
  startOfWeek,
} from "date-fns";

interface WeekSelectorProps {
  selectedDay: string;
  onSelect: (isoDay: string) => void;
  goToCurrentWeek: () => void;
  weekOffset: number;
  onWeekChange: (offset: number) => void;
  maxWeekOffset?: number;
  minWeekOffset?: number;
}

const WeekSelector = ({
  selectedDay,
  onSelect,
  goToCurrentWeek,
  weekOffset,
  onWeekChange,
  maxWeekOffset = 2,
  minWeekOffset = 0,
}: WeekSelectorProps) => {
  const now = new Date();
  const todayStr = formatISO(now, { representation: "date" });
  const currentWeekStart = addWeeks(
    startOfWeek(now, { weekStartsOn: 1 }),
    weekOffset,
  );
  const currentWeekEnd = endOfWeek(currentWeekStart, { weekStartsOn: 1 });
  const days = eachDayOfInterval({
    start: currentWeekStart,
    end: currentWeekEnd,
  });

  return (
    <div>
      {/* Navigation buttons */}
      <div className="flex items-center justify-between mb-2">
        <button
          onClick={() => onWeekChange(-1)}
          disabled={weekOffset === minWeekOffset}
          className="px-3 py-1 text-sm rounded border hover:bg-gray-100 disabled:opacity-50"
        >
          &larr; Previous
        </button>
        <button
          onClick={goToCurrentWeek}
          className="px-3 py-1 text-sm rounded border hover:bg-gray-100"
        >
          Current Week
        </button>
        <button
          onClick={() => onWeekChange(1)}
          disabled={weekOffset === maxWeekOffset}
          className="px-3 py-1 text-sm rounded border hover:bg-gray-100 disabled:opacity-50"
        >
          Next &rarr;
        </button>
      </div>
      <div className="flex gap-2 justify-between">
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
                    : "border-transparent text-muted hover:text-foreground")
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
