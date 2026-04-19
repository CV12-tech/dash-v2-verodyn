import { Skeleton } from '@/components/ui/skeleton';

export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-bg">
      <div className="w-full max-w-2xl space-y-4 p-6">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-4 w-2/3" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Skeleton className="h-[108px]" />
          <Skeleton className="h-[108px]" />
          <Skeleton className="h-[108px]" />
          <Skeleton className="h-[108px]" />
        </div>
      </div>
    </div>
  );
}
