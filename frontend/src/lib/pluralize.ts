export type PolishWordForms = {
  one: string;
  few: string;
  many: string;
};

export const formatPolishCount = (count: number, forms: PolishWordForms) => {
  const lastDigit = count % 10;
  const lastTwoDigits = count % 100;
  const suffix =
    count === 1
      ? forms.one
      : lastDigit >= 2 &&
          lastDigit <= 4 &&
          (lastTwoDigits < 12 || lastTwoDigits > 14)
        ? forms.few
        : forms.many;

  return `${count} ${suffix}`;
};
