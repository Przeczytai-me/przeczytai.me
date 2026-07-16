import { SignUp } from "@clerk/nextjs";

const SignUpPage = () => {
  return (
    <main className="flex flex-1 items-center justify-center">
      <SignUp
        fallbackRedirectUrl="/app"
        forceRedirectUrl="/app"
        signInUrl="/sign-in"
      />
    </main>
  );
};

export default SignUpPage;
