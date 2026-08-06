import { ReactNode } from "react";

interface PageWrapperProps {
  children: ReactNode;
  title?: ReactNode;
  subtitle?: string;
  icon?: ReactNode;
  /** Header gradient: 'orange' (default) or 'navy' */
  headerVariant?: "orange" | "navy";
  /** Optional right-side actions in header */
  actions?: ReactNode;
  /** No header at all */
  noHeader?: boolean;
  /** Max width container */
  maxWidth?: string;
}

const headerGradients = {
  orange: "bg-gradient-to-br from-orange to-orange-l",
  navy: "bg-navy",
};

export function PageWrapper({
  children,
  title,
  subtitle,
  icon,
  headerVariant = "orange",
  actions,
  noHeader = false,
  maxWidth,
}: PageWrapperProps) {
  return (
    <div className="page-slide-in space-y-6">
      {!noHeader && title && (
        <div
          className={`${headerGradients[headerVariant]} rounded-3xl p-8 ${
            headerVariant === "navy" ? "" : "shadow-sm"
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {icon && <div className="text-white/80">{icon}</div>}
              <div>
                <h1 className="text-3xl font-[300] text-white">{title}</h1>
                {subtitle && (
                  <p className="text-white/60 mt-1">{subtitle}</p>
                )}
              </div>
            </div>
            {actions && <div>{actions}</div>}
          </div>
        </div>
      )}
      <div className={maxWidth ? `max-w-${maxWidth} mx-auto` : ""}>
        {children}
      </div>
    </div>
  );
}
