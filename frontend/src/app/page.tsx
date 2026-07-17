import { auth } from "@clerk/nextjs/server";
import { LandingPage } from "./_components/landing-page";

const Home = async () => {
  const { userId } = await auth();

  return <LandingPage isSignedIn={Boolean(userId)} />;
};

export default Home;
