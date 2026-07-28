import { cn } from "@/lib/utils";

/**
 * Kbd — keyboard shortcut chip.
 * Matches the glass language used across the shell.
 */
export function Kbd({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <kbd
      className={cn(
        "inline-flex h-5 min-w-[20px] items-center justify-center rounded-[5px]",
        "border border-foreground/[0.09] bg-foreground/[0.05] px-1.5",
        "font-sans text-[10px] font-medium leading-none text-foreground/50",
        className
      )}
    >
      {children}
    </kbd>
  );
}
