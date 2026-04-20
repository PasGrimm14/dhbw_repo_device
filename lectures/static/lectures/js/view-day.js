import {
  getDateString,
  isDateInPast,
  parseTimeToMinutes,
  hasEventsOnDate,
} from "./util/dates.js";
import { formatDayHeader } from "./util/formatters.js";

// Get cohort IDs and plan data from the template (passed from Django view)
const COURSE_IDS = window.COHORT_IDS || [];
const COHORTS_DATA = window.COHORTS_DATA || {};
const DAY_VIEW_INITIAL_DATE = window.DAY_VIEW_INITIAL_DATE || "";

let currentDate = new Date();
let timeRange = null; // { startMinutes, endMinutes } aligned to full hours

const MINUTES_PER_SLOT = 15; // grid granularity: 1 row = 15 minutes

function minutesToRow(minutes) {
  // Row 1 = course headers, Row 2 = first slot
  return 2 + Math.round((minutes - timeRange.startMinutes) / MINUTES_PER_SLOT);
}

function parseInitialDate(value) {
  if (!value) return null;

  const compact = value.trim();
  if (/^\d{8}$/.test(compact)) {
    const day = Number(compact.slice(0, 2));
    const month = Number(compact.slice(2, 4));
    const year = Number(compact.slice(4, 8));
    if (!year || !month || !day) return null;
    return new Date(year, month - 1, day);
  }

  const parts = compact.split("-");
  if (parts.length !== 3) return null;

  const year = Number(parts[0]);
  const month = Number(parts[1]);
  const day = Number(parts[2]);
  if (!year || !month || !day) return null;

  return new Date(year, month - 1, day);
}

function getInitialDateFromPath() {
  const match = window.location.pathname.match(/\/view-day\/(\d{8})\/?$/);
  if (!match) return null;
  return parseInitialDate(match[1]);
}

function isSameCalendarDate(a, b) {
  return (
    a.getDate() === b.getDate() &&
    a.getMonth() === b.getMonth() &&
    a.getFullYear() === b.getFullYear()
  );
}

async function loadCourseData() {
  // Return data from the server context instead of making API calls
  const courseDataArray = COURSE_IDS.map(
    (id) => COHORTS_DATA[id] || { weeks: [] },
  );
  return courseDataArray;
}

/**
 * Return all sessions from the provided course data that occur on the currentDate.
 *
 * The function compares each session's `date` string to the string produced by
 * calling `getDateString(currentDate)` and collects matching sessions.
 *
 * @param {Object} courseData - Root object containing course schedule information.
 * @param {Array<Object>} courseData.weeks - Array of week objects.
 * @param {Array<Object>} courseData.weeks[].sessions - Array of session objects for the week.
 * @param {string} courseData.weeks[].sessions[].date - Date string for the session (format expected to match getDateString output).
 * @returns {Array<Object>} An array of session objects scheduled for today (may be empty).
 *
 * @example
 * // returns sessions whose `date` equals getDateString(currentDate)
 * const todays = filterTodaySessions(courseData);
 */
function filterTodaySessions(courseData) {
  const todayString = getDateString(currentDate);
  const todaySessions = [];

  for (const week of courseData.weeks) {
    for (const session of week.sessions) {
      if (session.date === todayString) {
        todaySessions.push(session);
      }
    }
  }

  return todaySessions;
}

function computeTimeRange(coursesData) {
  const todayString = getDateString(currentDate);
  let minMinutes = Infinity;
  let maxMinutes = -Infinity;

  for (const courseData of coursesData) {
    for (const week of courseData.weeks) {
      for (const session of week.sessions) {
        if (session.date === todayString) {
          const [start, end] = session.time.split("-");
          minMinutes = Math.min(minMinutes, parseTimeToMinutes(start));
          maxMinutes = Math.max(maxMinutes, parseTimeToMinutes(end));
        }
      }
    }
  }

  if (minMinutes === Infinity) return null;

  return {
    startMinutes: Math.floor(minMinutes / 60) * 60,
    endMinutes: Math.ceil(maxMinutes / 60) * 60,
  };
}

function renderHourLabels() {
  const timetable = document.getElementById("timetable");
  const existing = timetable.querySelectorAll(".hour-label, .hour-line");
  for (const el of existing) el.remove();

  if (!timeRange) return;

  const slotsPerHour = 60 / MINUTES_PER_SLOT;
  const startHour = timeRange.startMinutes / 60;
  const endHour = timeRange.endMinutes / 60;

  for (let h = startHour; h < endHour; h++) {
    const slotRow = minutesToRow(h * 60);

    // Full-width separator line at the top of each hour
    const line = document.createElement("div");
    line.className = "hour-line";
    line.style.gridColumn = "1 / -1";
    line.style.gridRow = String(slotRow);
    timetable.appendChild(line);

    // Hour label in column 1, spanning the full hour
    const label = document.createElement("div");
    label.className = "hour-label";
    label.style.gridColumn = "1";
    label.style.gridRow = `${slotRow} / ${slotRow + slotsPerHour}`;
    label.textContent = `${String(h).padStart(2, "0")}:00`;
    timetable.appendChild(label);
  }
}

function updateGridTemplate() {
  const timetable = document.getElementById("timetable");
  const numCourses = COURSE_IDS.length;
  timetable.style.gridTemplateColumns = `5em repeat(${numCourses}, 1fr)`;

  if (!timeRange) return;

  const totalSlots = (timeRange.endMinutes - timeRange.startMinutes) / MINUTES_PER_SLOT;
  const rootFontSize = parseFloat(getComputedStyle(document.documentElement).fontSize);
  const headerRowHeight = 4 * rootFontSize;

  // Distribute remaining height equally across all slots (proportional by time)
  const availableTotal = timetable.getBoundingClientRect().height;
  const slotHeight = (availableTotal - headerRowHeight) / totalSlots;

  const rowSizes = [`${headerRowHeight}px`, ...Array(totalSlots).fill(`${slotHeight}px`)];
  timetable.style.gridTemplateRows = rowSizes.join(" ");
}

function renderCourseEvents(courseData, courseIndex) {
  const todaySessions = filterTodaySessions(courseData);
  const timetable = document.getElementById("timetable");
  const gridColumn = courseIndex + 2;

  for (const session of todaySessions) {
    const [startTime, endTime] = session.time.split("-");
    const startRow = minutesToRow(parseTimeToMinutes(startTime));
    const endRow = minutesToRow(parseTimeToMinutes(endTime));
    const row = `${startRow} / ${endRow}`;

    const eventDiv = document.createElement("div");
    eventDiv.className = `event event-${(courseIndex % 5) + 1}`;
    eventDiv.style.gridRow = row;
    eventDiv.style.gridColumn = gridColumn;

    if (isDateInPast(currentDate, endTime)) {
      eventDiv.classList.add("event-passed");
    }

    const detailsSpan = document.createElement("span");
    detailsSpan.className = "event-details";

    const moduleStrong = document.createElement("strong");
    moduleStrong.textContent = session.module;
    detailsSpan.appendChild(moduleStrong);

    const timeSpan = document.createElement("span");
    timeSpan.textContent = session.time;
    detailsSpan.appendChild(timeSpan);

    const roomSpan = document.createElement("span");
    roomSpan.className = "event-room";
    // ensure readability of session rooms through striping unnecessary information
    roomSpan.textContent = session.room
      .replace("Hörsaal", "")
      .replace("HN Online-Veranstaltung", "Online");

    if (session.is_exam) {
      const examHint = document.createElement("span");
      examHint.className = "event-exam-hint";
      examHint.textContent = "Klausur";
      detailsSpan.appendChild(examHint);
    }

    eventDiv.appendChild(detailsSpan);
    eventDiv.appendChild(roomSpan);

    timetable.appendChild(eventDiv);
  }
}

function clearExistingEvents() {
  const timetable = document.getElementById("timetable");
  const toRemove = timetable.querySelectorAll(".event, .hour-label, .hour-line");
  for (const el of toRemove) el.remove();
}

function updateDateHeader() {
  const formattedDate = formatDayHeader(currentDate);
  const dateElement = document.getElementById("current-date");
  if (dateElement) {
    dateElement.textContent = formattedDate;
  }
}

async function changeDate(days) {
  const coursesData = await loadCourseData();
  const direction = days > 0 ? 1 : -1;

  currentDate.setDate(currentDate.getDate() + days);

  // Skip Sundays and Saturdays without events
  while (
    currentDate.getDay() === 0 ||
    (currentDate.getDay() === 6 && !hasEventsOnDate(currentDate, coursesData))
  ) {
    currentDate.setDate(currentDate.getDate() + direction);
  }

  if (isSameCalendarDate(currentDate, new Date())) {
    toggleTimeOverlayVisibility(true);
  } else {
    toggleTimeOverlayVisibility(false);
  }

  updateDateHeader();
  renderTimetable();
}

/**
 * Initializes navigation controls for a calendar view.
 *
 * Queries the document for elements with the class "calendar-control" and, if
 * at least two such elements exist, attaches click event listeners to the
 * first two:
 *  - the first element triggers changeDate(-1) (previous)
 *  - the second element triggers changeDate(1)  (next)
 *
 * No action is taken if fewer than two ".calendar-control" elements are found.
 * Side effects: attaches event listeners to DOM elements. Calling this function
 * multiple times may register duplicate listeners unless they are removed first.
 *
 * Requires a changeDate(delta) function to be available in scope.
 *
 * @returns {void}
 * @example
 * // After rendering calendar controls into the DOM:
 * setupNavigationButtons();
 */
async function jumpToToday() {
  currentDate = new Date();
  toggleTimeOverlayVisibility(true);
  updateDateHeader();
  await renderTimetable();
}

function setupNavigationButtons() {
  const buttons = document.querySelectorAll(".calendar-control");
  if (buttons.length >= 2) {
    // Remove any existing listeners by replacing the nodes with clones
    const prevButton = buttons[0];
    const nextButton = buttons[1];

    // Verify parent nodes exist
    if (!prevButton.parentNode || !nextButton.parentNode) {
      console.error("Calendar control buttons missing parent nodes");
      return;
    }

    const newPrevButton = prevButton.cloneNode(true);
    const newNextButton = nextButton.cloneNode(true);

    prevButton.parentNode.replaceChild(newPrevButton, prevButton);
    nextButton.parentNode.replaceChild(newNextButton, nextButton);

    // Attach fresh listeners to the cloned buttons
    newPrevButton.addEventListener("click", () => changeDate(-1));
    newNextButton.addEventListener("click", () => changeDate(1));
  }

  const todayButton = document.getElementById("todayButton");
  if (todayButton) {
    todayButton.addEventListener("click", () => jumpToToday());
  }
}

async function renderTimetable() {
  try {
    clearExistingEvents();
    const coursesData = await loadCourseData();

    timeRange = computeTimeRange(coursesData);
    updateGridTemplate();
    renderHourLabels();

    let index = 0;
    for (const courseData of coursesData) {
      renderCourseEvents(courseData, index);
      index++;
    }
  } catch (error) {
    alert("Failed to load course data:", error);
  }
}

async function initializeTimetable() {
  const initialDate =
    parseInitialDate(DAY_VIEW_INITIAL_DATE) || getInitialDateFromPath();
  if (initialDate) {
    currentDate = initialDate;
  }

  updateDateHeader();
  setupNavigationButtons();
  await renderTimetable();
}

// Wait for DOM to be ready before initializing
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeTimetable);
} else {
  await initializeTimetable();
}

// -- CURRENT TIME OVERLAY --

/**
 * Toggle visibility of the current time overlay and its label.
 *
 * This function adds or removes the "hidden" CSS class on the elements with IDs
 * "currentTimeIndicator", "currentTimeOverlay" and "currentTimeLabel".
 * When `visible` is true (default), the "hidden" class is removed so the elements become visible;
 * when false, the "hidden" class is added so the elements are hidden.
 *
 * Note: The function assumes elements with the given IDs exist in the DOM. If
 * they are not present, attempts to access their classList may throw an error.
 *
 * @param {boolean} [visible=true] - Whether the overlay and label should be shown (true) or hidden (false).
 * @returns {void}
 *
 * @example
 * // Show the overlay (default)
 * toggleTimeOverlayVisibility();
 *
 * @example
 * // Hide the overlay
 * toggleTimeOverlayVisibility(false);
 */
function toggleTimeOverlayVisibility(visible = true) {
  const indicator = document.getElementById("currentTimeIndicator");
  const overlay = document.getElementById("currentTimeOverlay");
  const timeLabel = document.getElementById("currentTimeLabel");

  if (visible) {
    indicator.classList.remove("hidden");
    overlay.classList.remove("hidden");
    timeLabel.classList.remove("hidden");
  } else {
    indicator.classList.add("hidden");
    overlay.classList.add("hidden");
    timeLabel.classList.add("hidden");
  }
}

function updateCurrentTimeOverlay() {
  const now = new Date();
  const currentHour = now.getHours();
  const currentMinute = now.getMinutes();

  const totalMinutes = currentHour * 60 + currentMinute;

  const overlay = document.getElementById("currentTimeOverlay");
  const timeLabel = document.getElementById("currentTimeLabel");

  const timeString = now.toLocaleTimeString("de-DE", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  timeLabel.textContent = timeString;

  if (!timeRange || totalMinutes < timeRange.startMinutes || totalMinutes >= timeRange.endMinutes) {
    overlay.style.display = "none";
    return;
  }

  const timetable = document.getElementById("timetable");
  if (!timetable) return;

  const rootFontSize = parseFloat(getComputedStyle(document.documentElement).fontSize);
  const headerRowHeight = 4 * rootFontSize;
  const totalSlots = (timeRange.endMinutes - timeRange.startMinutes) / MINUTES_PER_SLOT;
  const slotHeight = (timetable.getBoundingClientRect().height - headerRowHeight) / totalSlots;

  const minutesFromStart = totalMinutes - timeRange.startMinutes;
  const topPosition = headerRowHeight + (minutesFromStart / MINUTES_PER_SLOT) * slotHeight;

  overlay.style.display = "block";
  overlay.style.top = topPosition + "px";
}

// Update immediately on page load
updateCurrentTimeOverlay();

// Update every minute after page load
setInterval(updateCurrentTimeOverlay, 60000);

// Recalculate row heights when the window is resized
window.addEventListener("resize", () => {
  updateGridTemplate();
  updateCurrentTimeOverlay();
});
