export const supportedDocumentFileExtensions = [".txt", ".md"] as const;

export const supportedDocumentMimeTypes = [
  "text/plain",
  "text/markdown",
] as const;

export const supportedDocumentAccept = [
  ...supportedDocumentFileExtensions,
  ...supportedDocumentMimeTypes,
].join(",");

export const isSupportedDocumentFile = (file: File) => {
  const normalizedName = file.name.toLowerCase();

  return (
    supportedDocumentFileExtensions.some((extension) =>
      normalizedName.endsWith(extension),
    ) || supportedDocumentMimeTypes.some((mimeType) => file.type === mimeType)
  );
};
