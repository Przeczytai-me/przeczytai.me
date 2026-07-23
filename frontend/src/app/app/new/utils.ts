const previewLineLimit = 8;
const previewCharacterLimit = 1_200;

export const newDocumentCharacterLimit = 10_000;

export const getDocumentPreview = (text: string) => {
  const lines = text.split(/\r?\n/);
  const firstLines = lines.slice(0, previewLineLimit).join("\n");
  const previewText = firstLines.slice(0, previewCharacterLimit);

  return {
    isTruncated:
      lines.length > previewLineLimit ||
      firstLines.length > previewCharacterLimit,
    text: previewText,
  };
};

export const formatFileSize = (size: number) => {
  if (size < 1_024) {
    return `${size.toLocaleString("pl-PL")} B`;
  }

  return `${(size / 1_024).toLocaleString("pl-PL", {
    maximumFractionDigits: 1,
  })} KB`;
};
