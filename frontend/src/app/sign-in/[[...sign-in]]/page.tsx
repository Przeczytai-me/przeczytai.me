import { SignIn } from "@clerk/nextjs";
import { AuthPageCard } from "@/app/_components/auth-page-card";
import { clerkAuthAppearance } from "@/app/_components/clerk-auth-appearance";
import { dictionary } from "@/i18n/dictionaries";

const SignInPage = () => {
  const t = dictionary.auth.signIn;

  return (
    <AuthPageCard title={t.title} description={t.description}>
      <SignIn
        appearance={clerkAuthAppearance}
        fallbackRedirectUrl="/app"
        forceRedirectUrl="/app"
        signUpUrl="/sign-up"
      />
    </AuthPageCard>
  );
};

export default SignInPage;
