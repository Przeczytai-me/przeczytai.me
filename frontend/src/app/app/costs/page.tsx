import { CostsDashboard } from "./costs-dashboard";

/**
 * Internal cost dashboard. Deliberately absent from appNavigationItems: the
 * route is reachable only by typing the URL, and the API behind it returns 403
 * to anyone outside ADMIN_USER_IDS, which this page renders as an ordinary
 * not-found. Nothing about this feature is visible to normal users.
 */
const CostsPage = () => <CostsDashboard />;

export default CostsPage;
