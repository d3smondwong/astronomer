'use client';

import React from 'react';
import { Calendar as AntCalendar } from 'antd';
import dayjs, { Dayjs } from 'dayjs';
import { cn } from '@/lib/utils';

interface CalendarProps {
  mode?: 'single' | 'range';
  selected?: Date;
  onSelect?: (date: Date | undefined) => void;
  disabled?: ((date: Date) => boolean) | boolean;
  captionLayout?: string;
  className?: string;
}

const Calendar = React.forwardRef<HTMLDivElement, CalendarProps>(
  ({ selected, onSelect, disabled: disabledProp, className }, ref) => {
    const today = dayjs().startOf('day');
    const [value, setValue] = React.useState<Dayjs | undefined>(
      selected ? dayjs(selected) : undefined
    );

    const handleChange = (date: Dayjs) => {
      // Don't allow selecting future dates
      if (date.isAfter(today, 'day')) {
        return;
      }
      setValue(date);
      onSelect?.(date.toDate());
    };

    const isDisabledDate = (date: Dayjs): boolean => {
      // Disable future dates (anything after today)
      if (date.isAfter(today, 'day')) {
        return true;
      }

      // Apply custom disabled function if provided
      if (typeof disabledProp === 'function') {
        try {
          return disabledProp(date.toDate());
        } catch {
          return false;
        }
      }

      return disabledProp === true;
    };

    const handleYearChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      const year = parseInt(e.target.value, 10);

      if (value) {
        const newDate = value.year(year);
        // Ensure the date doesn't exceed today
        if (newDate.isAfter(today, 'day')) {
          setValue(today);
        } else {
          setValue(newDate);
        }
      } else {
        // If no date selected yet, default to January 1st of the selected year
        const newDate = dayjs(`${year}-01-01`);
        if (newDate.isAfter(today, 'day')) {
          setValue(today);
        } else {
          setValue(newDate);
        }
      }
    };

    const currentYear = value?.year() || today.year();

    // Generate year options from 1930 to current year
    const yearOptions = [];
    for (let year = today.year(); year >= 1930; year--) {
      yearOptions.push(year);
    }

    return (
      <div ref={ref} className={cn('p-3 bg-white rounded-md', className)}>
        <div className="mb-4">
          <label className="text-sm font-medium mb-2 block">Birth Year</label>
          <select
            value={currentYear}
            onChange={handleYearChange}
            className={cn(
              'w-full h-8 px-2 rounded border border-gray-300 bg-white text-sm',
              'focus:outline-none focus:ring-2 focus:ring-blue-500'
            )}
          >
            {yearOptions.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>
        <AntCalendar
          value={value}
          onChange={handleChange}
          disabledDate={isDisabledDate}
          fullscreen={false}
        />
      </div>
    );
  }
);

Calendar.displayName = 'Calendar';

export { Calendar };
