"use client";

import { useClerk } from "@clerk/nextjs";

export const SignOutButton = ({
  className,
  children = "Wyloguj",
}: {
  className?: string;
  children?: React.ReactNode;
}) => {
  const { signOut } = useClerk();

  return (
    <button
      type="button"
      className={className}
      onClick={() => signOut({ redirectUrl: "/" })}
    >
      {children}
    </button>
  );
};
