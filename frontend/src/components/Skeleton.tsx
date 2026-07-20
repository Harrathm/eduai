import { Component, CSSProperties, ReactNode } from "react";

interface SkeletonProps {
  /** Element to display after loading */
  children?: ReactNode;
  /** Whether content is loading */
  isLoading?: boolean;
  /** Custom loading placeholder */
  loadingPlaceholder?: ReactNode;
  /** Animation speed in ms (default: 800) */
  animationSpeed?: number;
  /** Base color for skeleton (default: #e2e8f0) */
  baseColor?: string;
  /** Highlight color for skeleton (default: #f1f5f9) */
  highlightColor?: string;
}

export function Skeleton({
  children,
  isLoading = true,
  loadingPlaceholder,
  animationSpeed = 800,
  baseColor = "#e2e8f0",
  highlightColor = "#f1f5f9",
}: SkeletonProps) {
  const shimmerAnimation: CSSProperties = {
    background: `linear-gradient(90deg, ${baseColor} 0%, ${highlightColor} 50%, ${baseColor} 100%)`,
    backgroundSize: "200% 100%",
    animation: `shimmer ${animationSpeed}ms ease-in-out infinite`,
  };

  if (!isLoading) {
    return <>{children}</>;
  }

  if (loadingPlaceholder) {
    return <>{loadingPlaceholder}</>;
  }

  return (
    <>
      <style>
        {`
          @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
          }
        `}
      </style>
      {/* Default loading placeholders */}
      <div className="animate-pulse space-y-4">
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        <div className="h-4 bg-gray-200 rounded w-5/6"></div>
      </div>
    </>
  );
}

// Pre-built skeleton components
export function CardSkeleton() {
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border">
      <div className="animate-pulse space-y-3">
        <div className="h-32 bg-gray-200 rounded-lg"></div>
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        <div className="h-3 bg-gray-200 rounded w-1/2"></div>
      </div>
    </div>
  );
}

export function ListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 animate-pulse">
          <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="animate-pulse space-y-2">
      {/* Header */}
      <div className="flex gap-4">
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="h-4 bg-gray-300 rounded flex-1"></div>
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4">
          {Array.from({ length: cols }).map((_, j) => (
            <div key={j} className="h-4 bg-gray-200 rounded flex-1"></div>
          ))}
        </div>
      ))}
    </div>
  );
}

export function FormSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-10 bg-gray-200 rounded"></div>
      <div className="h-10 bg-gray-200 rounded"></div>
      <div className="h-10 bg-gray-200 rounded w-1/3"></div>
      <div className="h-32 bg-gray-200 rounded"></div>
    </div>
  );
}

// Loading button component
export function LoadingButton({
  children,
  isLoading,
  loadingText,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { isLoading?: boolean; loadingText?: string }) {
  return (
    <button {...props} disabled={isLoading || props.disabled}>
      {isLoading ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          {loadingText || "Loading..."}
        </span>
      ) : children}
    </button>
  );
}