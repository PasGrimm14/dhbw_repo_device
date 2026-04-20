/**
 * Formats a date for display as a day header.
 *
 * @param {Date} date - The date to format
 * @returns {string} Formatted date string (e.g., "Montag, 16. Februar 2026")
 */
export function formatDayHeader(date) {
  const options = {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  };
  return date.toLocaleDateString("de-DE", options);
}
