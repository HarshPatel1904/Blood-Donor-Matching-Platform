export const BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];

export const DEFAULT_LOCALITIES = [
  "Navrangpura",
  "Satellite",
  "Vastrapur",
  "Maninagar",
  "Bopal",
  "Thaltej",
  "Chandkheda",
  "Paldi",
  "Gota",
  "SG Highway",
];

export const URGENCY_LEVELS = [
  { value: "normal", label: "Normal" },
  { value: "urgent", label: "Urgent" },
  { value: "critical", label: "Critical (Emergency)" },
];

export function getDefaultRequiredDate() {
  const tomorrow = new Date(Date.now() + 24 * 60 * 60 * 1000);
  return tomorrow.toISOString().split("T")[0];
}
