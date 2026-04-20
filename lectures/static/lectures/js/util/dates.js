/**
 * Converts a Date object to a string in YYYY-MM-DD format.
 *
 * @param {Date} date - The date to convert
 * @returns {string} Date string in YYYY-MM-DD format
 */
export function getDateString(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/**
 * Checks if a given date and time are in the past.
 *
 * @param {Date} date - The date to check
 * @param {string} timeString - Time string in HH:MM format
 * @returns {boolean} True if the datetime is in the past
 */
export function isDateInPast(date, timeString) {
  const [hours, minutes] = timeString.split(":").map(Number);
  const checkDate = new Date(date);
  checkDate.setHours(hours, minutes, 0, 0);
  return checkDate < new Date();
}

/**
 * Converts a time string to minutes from midnight.
 *
 * @param {string} timeString - Time string in HH:MM format
 * @returns {number} Minutes from midnight
 */
export function parseTimeToMinutes(timeString) {
  const [hours, minutes] = timeString.split(":").map(Number);
  return hours * 60 + minutes;
}

/**
 * Check if a given date has any events scheduled across all courses.
 *
 * @param {Date} date - The date to check for events
 * @param {Array<Object>} coursesData - Array of course data objects
 * @returns {boolean} True if at least one event exists on the date, false otherwise
 */
export function hasEventsOnDate(date, coursesData) {
  const dateString = getDateString(date);

  for (const courseData of coursesData) {
    for (const week of courseData.weeks) {
      for (const session of week.sessions) {
        if (session.date === dateString) {
          return true;
        }
      }
    }
  }

  return false;
}
