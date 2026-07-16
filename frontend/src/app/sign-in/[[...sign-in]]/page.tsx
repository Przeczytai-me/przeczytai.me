import { SignIn } from "@clerk/nextjs";

const SignInPage = () => {
  return (
    <main className="flex flex-1 items-center justify-center">
      <SignIn
        fallbackRedirectUrl="/app"
        forceRedirectUrl="/app"
        signUpUrl="/sign-up"
      />
    </main>
  );
};

export default SignInPage;
