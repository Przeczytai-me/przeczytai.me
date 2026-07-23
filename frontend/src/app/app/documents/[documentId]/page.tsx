import { DocumentReader } from "./document-reader";

type DocumentPageProps = {
  params: Promise<{ documentId: string }>;
};

const DocumentPage = async ({ params }: DocumentPageProps) => {
  const { documentId } = await params;
  return <DocumentReader documentId={documentId} />;
};

export default DocumentPage;
