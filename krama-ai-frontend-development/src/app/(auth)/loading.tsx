import { Skeleton } from "@/components/ui/skeleton";

export default function AuthLoading() {
  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-background">
      <div className="w-full max-w-md p-6 space-y-6" aria-busy="true" aria-label="Loading">
        <div className="flex justify-center">
          <Skeleton className="h-10 w-40 rounded-xl" />
        </div>
        <Skeleton className="h-[380px] w-full rounded-xl" />
      </div>
    </div>
  );
}
