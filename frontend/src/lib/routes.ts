export const getDocumentId = (pathname: string) => {
  const match = pathname.match(/^\/app\/documents\/([^/]+)/);
  return match?.[1];
};
