import { cn } from "@/lib/utils";

export function Logo({ className, collapsed = false }: { className?: string; collapsed?: boolean }) {
  if (collapsed) {
    return (
      <div className={cn("flex items-center", className)}>
        <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-gradient shadow-glow">
          {/* petal-N brand mark: cream outer petals, pink diagonal */}
          <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none">
            <path d="M7.5 5.5C9.5 8 9.5 16 7.5 18.5 5.5 16 5.5 8 7.5 5.5Z" fill="#FEFBDA" />
            <path d="M16.5 5.5C18.5 8 18.5 16 16.5 18.5 14.5 16 14.5 8 16.5 5.5Z" fill="#FEFBDA" />
            <path d="M9 6C13.5 8.5 15 13.5 15.5 18 11 15.5 9.5 10.5 9 6Z" fill="#FABBCB" />
          </svg>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex items-center", className)}>
      {/* brighten the crimson wordmark in dark mode so it reads on the dark bg */}
      <img
        src="/logo/logo.png"
        alt="NUMÉ Beauty"
        className="h-9 w-auto dark:brightness-[1.75] dark:saturate-[1.15]"
      />
    </div>
  );
}
