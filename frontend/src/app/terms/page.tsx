import type { Metadata } from "next";
import { PublicPolicyPage } from "@/app/_components/public-policy-page";
import { dictionary } from "@/i18n/dictionaries";

const copy = dictionary.legal.terms;

export const metadata: Metadata = copy.metadata;

// TODO(PRZ-25): Replace this product-information draft with approved terms.
const TermsPage = () => <PublicPolicyPage copy={copy} />;

export default TermsPage;
