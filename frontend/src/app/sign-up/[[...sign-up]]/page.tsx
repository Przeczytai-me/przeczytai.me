import { SignUp } from "@clerk/nextjs";
import { AuthPageCard } from "@/app/_components/auth-page-card";
import { clerkAuthAppearance } from "@/app/_components/clerk-auth-appearance";
import { dictionary } from "@/i18n/dictionaries";

const SignUpPage = () => {
  const t = dictionary.auth.signUp;

  return (
    <AuthPageCard title={t.title} description={t.description}>
      <SignUp
        appearance={clerkAuthAppearance}
        fallbackRedirectUrl="/app"
        forceRedirectUrl="/app"
        signInUrl="/sign-in"
      />
    </AuthPageCard>
  );
};

export default SignUpPage;
