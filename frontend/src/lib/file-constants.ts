export const supportedDocumentFileExtensions = [".txt", ".md"] as const;

export const supportedDocumentAccept =
  supportedDocumentFileExtensions.join(",");

export const getSupportedDocumentExtension = (fileName: string) => {
  const normalizedName = fileName.toLowerCase();

  return (
    supportedDocumentFileExtensions.find((extension) =>
      normalizedName.endsWith(extension),
    ) ?? null
  );
};

export const isSupportedDocumentFile = (file: File) => {
  return getSupportedDocumentExtension(file.name) !== null;
};
