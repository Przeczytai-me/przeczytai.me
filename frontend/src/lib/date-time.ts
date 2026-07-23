const polishDateTimeFormatter = new Intl.DateTimeFormat("pl-PL", {
  dateStyle: "medium",
  timeStyle: "short",
});

export const formatPolishDateTime = (value: string | number | Date) =>
  polishDateTimeFormatter.format(new Date(value));
