import { AppShell } from "./app-shell";

const PrivateAppLayout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => {
  return <AppShell>{children}</AppShell>;
};

export default PrivateAppLayout;
