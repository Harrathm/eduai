import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {icon && <div className="text-gray/40 mb-4">{icon}</div>}
      <h3 className="text-lg font-medium text-navy mb-1">{title}</h3>
      {description && <p className="text-sm text-gray mb-4">{description}</p>}
      {action}
    </div>
  );
}
