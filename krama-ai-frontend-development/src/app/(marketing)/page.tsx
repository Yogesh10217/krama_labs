import { Hero } from "@/features/marketing/sections/hero";
import { TrustSection } from "@/features/marketing/sections/trust";
import { FeaturesSection } from "@/features/marketing/sections/features";
import { HowItWorksSection } from "@/features/marketing/sections/how-it-works";
import { ProductPreviewSection } from "@/features/marketing/sections/product-preview";
import { WhyKramaSection } from "@/features/marketing/sections/why-krama";
import { CtaSection } from "@/features/marketing/sections/cta";

export default function LandingPage() {
  return (
    <>
      <Hero />
      <TrustSection />
      <FeaturesSection />
      <HowItWorksSection />
      <ProductPreviewSection />
      <WhyKramaSection />
      <CtaSection />
    </>
  );
}
