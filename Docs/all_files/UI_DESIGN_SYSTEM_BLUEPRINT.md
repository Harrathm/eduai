# UI DESIGN SYSTEM BLUEPRINT — EDUAI Learning

**Date :** 05/08/2026
**Objectif :** Créer `src/components/ui/` avec des composants réutilisables, typés et accessibles
**Audit findings :** 80+ boutons inline, 35 fichiers avec spinners, 24 empty states, 18 modals inline, 13+ badges inline

---

## 1. STRUCTURE CIBLE

```
src/components/ui/
├── index.ts           ← Barrel export
├── Button.tsx         ← 5 variants, 3 sizes, loading, icons
├── Card.tsx           ← CardHeader, CardTitle, CardContent, CardFooter
├── Input.tsx          ← Label, error, icon, required
├── Textarea.tsx       ← Même API que Input
├── Spinner.tsx        ← 3 sizes, color
├── Modal.tsx          ← Accessible, backdrop, footer
├── Badge.tsx          ← Générique, couleurs custom
├── StatusBadge.tsx    ← success/warning/error/info pré-défini
└── EmptyState.tsx     ← Icon, title, description, action
```

---

## 2. COMPOSANTS

### `src/components/ui/Button.tsx`

```tsx
import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import { Loader2 } from "lucide-react";

// ─── Types ─────────────────────────────────────────────────────────────────

type ButtonVariant = "primary" | "secondary" | "accent" | "danger" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
}

// ─── Styles ────────────────────────────────────────────────────────────────

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-navy text-white hover:bg-navy-m active:bg-navy-s shadow-sm disabled:bg-navy-50",
  secondary:
    "bg-cream-m text-navy hover:bg-cream border border-black/5 disabled:bg-cream-m/50",
  accent:
    "bg-orange text-white hover:bg-orange-w active:bg-orange shadow-or disabled:bg-orange/50",
  danger:
    "bg-red-500 text-white hover:bg-red-600 active:bg-red-700 disabled:bg-red-300",
  ghost:
    "bg-transparent text-navy hover:bg-cream-m active:bg-cream disabled:text-gray",
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "px-4 py-2 text-xs gap-1.5 rounded-lg",
  md: "px-5 py-2.5 text-sm gap-2 rounded-xl",
  lg: "px-7 py-3.5 text-base gap-2.5 rounded-xl",
};

// ─── Component ─────────────────────────────────────────────────────────────

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      isLoading = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      disabled,
      className = "",
      children,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={`
          inline-flex items-center justify-center font-medium
          transition-all duration-150 ease-in-out
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange/50
          disabled:cursor-not-allowed disabled:opacity-60
          ${variantStyles[variant]}
          ${sizeStyles[size]}
          ${fullWidth ? "w-full" : ""}
          ${className}
        `.trim()}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="animate-spin" style={{ width: size === "sm" ? 14 : size === "lg" ? 20 : 16 }} />
        ) : leftIcon ? (
          <span className="shrink-0">{leftIcon}</span>
        ) : null}

        {children && <span>{children}</span>}

        {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = "Button";

export { Button, type ButtonProps, type ButtonVariant, type ButtonSize };
```

---

### `src/components/ui/Card.tsx`

```tsx
import { forwardRef, type HTMLAttributes, type ReactNode } from "react";

// ─── Types ─────────────────────────────────────────────────────────────────

type CardPadding = "none" | "sm" | "md" | "lg";
type CardShadow = "none" | "sm" | "md" | "lg";
type CardRounded = "none" | "sm" | "md" | "lg" | "xl" | "2xl" | "3xl";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padding?: CardPadding;
  shadow?: CardShadow;
  rounded?: CardRounded;
  hover?: boolean;
}

interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  action?: ReactNode;
}

interface CardTitleProps extends HTMLAttributes<HTMLHeadingElement> {
  as?: "h1" | "h2" | "h3" | "h4";
}

// ─── Styles ────────────────────────────────────────────────────────────────

const paddingStyles: Record<CardPadding, string> = {
  none: "",
  sm: "p-4",
  md: "p-6",
  lg: "p-8",
};

const shadowStyles: Record<CardShadow, string> = {
  none: "",
  sm: "shadow-sm",
  md: "shadow-md",
  lg: "shadow-lg",
};

const roundedStyles: Record<CardRounded, string> = {
  none: "",
  sm: "rounded-lg",
  md: "rounded-xl",
  lg: "rounded-2xl",
  xl: "rounded-3xl",
  "2xl": "rounded-3xl",
  "3xl": "rounded-3xl",
};

// ─── Card ──────────────────────────────────────────────────────────────────

const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      padding = "md",
      shadow = "sm",
      rounded = "xl",
      hover = false,
      className = "",
      children,
      ...props
    },
    ref
  ) => (
    <div
      ref={ref}
      className={`
        bg-white border border-black/5
        ${paddingStyles[padding]}
        ${shadowStyles[shadow]}
        ${roundedStyles[rounded]}
        ${hover ? "hover:shadow-md transition-shadow" : ""}
        ${className}
      `.trim()}
      {...props}
    >
      {children}
    </div>
  )
);

Card.displayName = "Card";

// ─── CardHeader ────────────────────────────────────────────────────────────

const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ action, className = "", children, ...props }, ref) => (
    <div
      ref={ref}
      className={`flex items-center justify-between pb-4 border-b border-black/5 ${className}`.trim()}
      {...props}
    >
      <div>{children}</div>
      {action && <div>{action}</div>}
    </div>
  )
);

CardHeader.displayName = "CardHeader";

// ─── CardTitle ─────────────────────────────────────────────────────────────

const CardTitle = forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ as: Tag = "h3", className = "", children, ...props }, ref) => (
    <Tag
      ref={ref}
      className={`font-semibold text-navy ${className}`.trim()}
      {...props}
    >
      {children}
    </Tag>
  )
);

CardTitle.displayName = "CardTitle";

// ─── CardContent ───────────────────────────────────────────────────────────

const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className = "", children, ...props }, ref) => (
    <div ref={ref} className={`pt-4 ${className}`.trim()} {...props}>
      {children}
    </div>
  )
);

CardContent.displayName = "CardContent";

// ─── CardFooter ────────────────────────────────────────────────────────────

const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className = "", children, ...props }, ref) => (
    <div
      ref={ref}
      className={`flex items-center gap-3 pt-4 border-t border-black/5 ${className}`.trim()}
      {...props}
    >
      {children}
    </div>
  )
);

CardFooter.displayName = "CardFooter";

export {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
  type CardProps,
  type CardHeaderProps,
  type CardTitleProps,
  type CardPadding,
  type CardShadow,
  type CardRounded,
};
```

---

### `src/components/ui/Input.tsx`

```tsx
import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";

// ─── Types ─────────────────────────────────────────────────────────────────

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  required?: boolean;
}

// ─── Component ─────────────────────────────────────────────────────────────

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      hint,
      leftIcon,
      rightIcon,
      required,
      className = "",
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);
    const hasError = !!error;

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-navy mb-1.5"
          >
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}

        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray pointer-events-none">
              {leftIcon}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            aria-invalid={hasError}
            aria-describedby={hasError ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
            className={`
              w-full rounded-xl border bg-white px-4 py-2.5 text-sm text-navy
              placeholder:text-gray/60
              transition-colors duration-150
              focus:outline-none focus:ring-2 focus:ring-orange/30 focus:border-orange
              disabled:cursor-not-allowed disabled:bg-cream-m/50 disabled:text-gray
              ${leftIcon ? "pl-10" : ""}
              ${rightIcon ? "pr-10" : ""}
              ${hasError
                ? "border-red-400 focus:ring-red-300 focus:border-red-500"
                : "border-black/10 hover:border-black/20"
              }
              ${className}
            `.trim()}
            {...props}
          />

          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray">
              {rightIcon}
            </div>
          )}
        </div>

        {hasError && (
          <p id={`${inputId}-error`} className="mt-1.5 text-xs text-red-500" role="alert">
            {error}
          </p>
        )}

        {!hasError && hint && (
          <p id={`${inputId}-hint`} className="mt-1.5 text-xs text-gray">
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input, type InputProps };
```

---

### `src/components/ui/Textarea.tsx`

```tsx
import { forwardRef, type TextareaHTMLAttributes, type ReactNode } from "react";

// ─── Types ─────────────────────────────────────────────────────────────────

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
  required?: boolean;
}

// ─── Component ─────────────────────────────────────────────────────────────

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, hint, required, className = "", id, ...props }, ref) => {
    const textareaId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);
    const hasError = !!error;

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={textareaId}
            className="block text-sm font-medium text-navy mb-1.5"
          >
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}

        <textarea
          ref={ref}
          id={textareaId}
          aria-invalid={hasError}
          aria-describedby={hasError ? `${textareaId}-error` : hint ? `${textareaId}-hint` : undefined}
          className={`
            w-full rounded-xl border bg-white px-4 py-2.5 text-sm text-navy
            placeholder:text-gray/60 min-h-[80px] resize-y
            transition-colors duration-150
            focus:outline-none focus:ring-2 focus:ring-orange/30 focus:border-orange
            disabled:cursor-not-allowed disabled:bg-cream-m/50 disabled:text-gray
            ${hasError
              ? "border-red-400 focus:ring-red-300 focus:border-red-500"
              : "border-black/10 hover:border-black/20"
            }
            ${className}
          `.trim()}
          {...props}
        />

        {hasError && (
          <p id={`${textareaId}-error`} className="mt-1.5 text-xs text-red-500" role="alert">
            {error}
          </p>
        )}

        {!hasError && hint && (
          <p id={`${textareaId}-hint`} className="mt-1.5 text-xs text-gray">
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = "Textarea";

export { Textarea, type TextareaProps };
```

---

### `src/components/ui/Spinner.tsx`

```tsx
import { type HTMLAttributes } from "react";

// ─── Types ─────────────────────────────────────────────────────────────────

type SpinnerSize = "xs" | "sm" | "md" | "lg";
type SpinnerColor = "navy" | "orange" | "white" | "gray";

interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
  size?: SpinnerSize;
  color?: SpinnerColor;
  label?: string;
}

// ─── Styles ────────────────────────────────────────────────────────────────

const sizeStyles: Record<SpinnerSize, string> = {
  xs: "w-3 h-3 border",
  sm: "w-4 h-4 border-[1.5px]",
  md: "w-6 h-6 border-2",
  lg: "w-10 h-10 border-[3px]",
};

const colorStyles: Record<SpinnerColor, string> = {
  navy: "border-navy/20 border-t-navy",
  orange: "border-orange/20 border-t-orange",
  white: "border-white/30 border-t-white",
  gray: "border-gray/20 border-t-gray",
};

// ─── Component ─────────────────────────────────────────────────────────────

function Spinner({
  size = "md",
  color = "orange",
  label = "Chargement...",
  className = "",
  ...props
}: SpinnerProps) {
  return (
    <div
      role="status"
      aria-label={label}
      className={`
        inline-block rounded-full animate-spin
        ${sizeStyles[size]}
        ${colorStyles[color]}
        ${className}
      `.trim()}
      {...props}
    >
      <span className="sr-only">{label}</span>
    </div>
  );
}

// ─── Full-page loader ──────────────────────────────────────────────────────

function PageSpinner({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center justify-center py-12 ${className}`.trim()}>
      <div className="text-center">
        <Spinner size="lg" />
        <p className="text-sm text-gray mt-3">Chargement...</p>
      </div>
    </div>
  );
}

// ─── Button spinner (inline) ───────────────────────────────────────────────

function ButtonSpinner({ size = "sm" }: { size?: SpinnerSize }) {
  return <Spinner size={size} color="white" label="" />;
}

export { Spinner, PageSpinner, ButtonSpinner, type SpinnerProps, type SpinnerSize, type SpinnerColor };
```

---

### `src/components/ui/Modal.tsx`

```tsx
import { useEffect, useRef, type ReactNode } from "react";
import { X } from "lucide-react";
import { createPortal } from "react-dom";

// ─── Types ─────────────────────────────────────────────────────────────────

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  footer?: ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
  closeOnBackdrop?: boolean;
  closeOnEscape?: boolean;
}

// ─── Styles ────────────────────────────────────────────────────────────────

const sizeStyles = {
  sm: "max-w-md",
  md: "max-w-lg",
  lg: "max-w-2xl",
  xl: "max-w-4xl",
};

// ─── Component ─────────────────────────────────────────────────────────────

function Modal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = "md",
  closeOnBackdrop = true,
  closeOnEscape = true,
}: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  // Escape key
  useEffect(() => {
    if (!isOpen || !closeOnEscape) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isOpen, closeOnEscape, onClose]);

  // Lock body scroll
  useEffect(() => {
    if (!isOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = prev; };
  }, [isOpen]);

  // Focus trap
  useEffect(() => {
    if (isOpen && panelRef.current) {
      panelRef.current.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (closeOnBackdrop && e.target === overlayRef.current) {
      onClose();
    }
  };

  return createPortal(
    <div
      ref={overlayRef}
      onClick={handleBackdropClick}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-[fadeUp_0.2s_ease]"
      role="dialog"
      aria-modal="true"
      aria-label={title || "Dialogue"}
    >
      <div
        ref={panelRef}
        tabIndex={-1}
        className={`
          bg-white rounded-3xl shadow-dp w-full ${sizeStyles[size]}
          max-h-[90vh] flex flex-col
          outline-none
        `.trim()}
      >
        {/* Header */}
        {(title || onClose) && (
          <div className="flex items-center justify-between px-8 py-6 border-b border-black/5">
            {title && (
              <h2 className="text-xl font-semibold text-navy">{title}</h2>
            )}
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-gray hover:text-navy hover:bg-cream-m transition-colors"
              aria-label="Fermer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* Body */}
        <div className="px-8 py-6 overflow-y-auto flex-1">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="flex items-center justify-end gap-3 px-8 py-5 border-t border-black/5">
            {footer}
          </div>
        )}
      </div>
    </div>,
    document.body
  );
}

// ─── ConfirmModal ──────────────────────────────────────────────────────────

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "warning" | "info";
  isLoading?: boolean;
}

function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = "Confirmer",
  cancelLabel = "Annuler",
  variant = "danger",
  isLoading = false,
}: ConfirmModalProps) {
  const variantBtn = {
    danger: "danger" as const,
    warning: "accent" as const,
    info: "primary" as const,
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="sm"
      footer={
        <>
          <button
            onClick={onClose}
            className="px-5 py-2.5 text-sm font-medium rounded-xl bg-cream-m text-navy hover:bg-cream"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={`
              px-5 py-2.5 text-sm font-medium rounded-xl text-white
              disabled:opacity-50 disabled:cursor-not-allowed
              ${variant === "danger" ? "bg-red-500 hover:bg-red-600" :
                variant === "warning" ? "bg-orange hover:bg-orange-w" :
                "bg-navy hover:bg-navy-m"}
            `}
          >
            {isLoading ? "En cours..." : confirmLabel}
          </button>
        </>
      }
    >
      <p className="text-gray">{message}</p>
    </Modal>
  );
}

export { Modal, ConfirmModal, type ModalProps, type ConfirmModalProps };
```

---

### `src/components/ui/Badge.tsx`

```tsx
import { type HTMLAttributes, type ReactNode } from "react";

// ─── Types ─────────────────────────────────────────────────────────────────

type BadgeVariant = "default" | "navy" | "orange" | "success" | "warning" | "error" | "info" | "purple";
type BadgeSize = "sm" | "md";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  children: ReactNode;
}

// ─── Styles ────────────────────────────────────────────────────────────────

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-cream-m text-gray",
  navy: "bg-navy-50 text-navy",
  orange: "bg-orange-p text-orange",
  success: "bg-green-50 text-green-700",
  warning: "bg-amber-50 text-amber-700",
  error: "bg-red-50 text-red-600",
  info: "bg-blue-50 text-blue-600",
  purple: "bg-purple-50 text-purple-600",
};

const dotColors: Record<BadgeVariant, string> = {
  default: "bg-gray",
  navy: "bg-navy",
  orange: "bg-orange",
  success: "bg-green-500",
  warning: "bg-amber-500",
  error: "bg-red-500",
  info: "bg-blue-500",
  purple: "bg-purple-500",
};

const sizeStyles: Record<BadgeSize, string> = {
  sm: "px-2 py-0.5 text-[10px]",
  md: "px-2.5 py-1 text-xs",
};

// ─── Component ─────────────────────────────────────────────────────────────

function Badge({
  variant = "default",
  size = "md",
  dot = false,
  className = "",
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center gap-1.5 font-medium rounded-full
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `.trim()}
      {...props}
    >
      {dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]}`}
          aria-hidden="true"
        />
      )}
      {children}
    </span>
  );
}

Badge.displayName = "Badge";

export { Badge, type BadgeProps, type BadgeVariant, type BadgeSize };
```

---

### `src/components/ui/StatusBadge.tsx`

```tsx
import { type ReactNode } from "react";
import { Badge, type BadgeSize } from "./Badge";

// ─── Types ─────────────────────────────────────────────────────────────────

type StatusVariant = "success" | "warning" | "error" | "info" | "neutral";

interface StatusBadgeProps {
  status: StatusVariant;
  label: string;
  size?: BadgeSize;
  dot?: boolean;
  icon?: ReactNode;
}

// ─── Mapping statut → badge variant ────────────────────────────────────────

const statusToVariant: Record<StatusVariant, "success" | "warning" | "error" | "info" | "default"> = {
  success: "success",
  warning: "warning",
  error: "error",
  info: "info",
  neutral: "default",
};

// ─── Preset status badges ──────────────────────────────────────────────────

const presets = {
  active: { status: "success" as const, label: "Actif" },
  inactive: { status: "error" as const, label: "Inactif" },
  pending: { status: "warning" as const, label: "En attente" },
  published: { status: "success" as const, label: "Publié" },
  draft: { status: "neutral" as const, label: "Brouillon" },
  rejected: { status: "error" as const, label: "Rejeté" },
  approved: { status: "success" as const, label: "Approuvé" },
  trial: { status: "info" as const, label: "Essai" },
  premium: { status: "warning" as const, label: "Premium" },
} as const;

// ─── Component ─────────────────────────────────────────────────────────────

function StatusBadge({
  status,
  label,
  size = "md",
  dot = true,
  icon,
}: StatusBadgeProps) {
  return (
    <Badge variant={statusToVariant[status]} size={size} dot={dot}>
      {icon && <span className="shrink-0">{icon}</span>}
      {label}
    </Badge>
  );
}

StatusBadge.displayName = "StatusBadge";

// ─── RoleBadge ─────────────────────────────────────────────────────────────

const roleColors: Record<string, "navy" | "orange" | "purple" | "info" | "success" | "default"> = {
  super_admin: "navy",
  admin_school: "purple",
  pedagogical_admin: "info",
  pedagogical_lead: "info",
  teacher: "success",
  student: "default",
  parent: "orange",
};

const roleLabels: Record<string, string> = {
  super_admin: "Super Admin",
  admin_school: "Admin École",
  pedagogical_admin: "Admin Pédago",
  pedagogical_lead: "Réf. Pédago",
  teacher: "Enseignant",
  student: "Étudiant",
  parent: "Parent",
};

function RoleBadge({ role, size = "md" }: { role: string; size?: BadgeSize }) {
  const variant = roleColors[role] || "default";
  const label = roleLabels[role] || role;
  return <Badge variant={variant} size={size}>{label}</Badge>;
}

RoleBadge.displayName = "RoleBadge";

export {
  StatusBadge,
  RoleBadge,
  presets,
  type StatusBadgeProps,
  type StatusVariant,
};
```

---

### `src/components/ui/EmptyState.tsx`

```tsx
import { type ReactNode } from "react";
import { Inbox } from "lucide-react";
import { Button, type ButtonProps } from "./Button";

// ─── Types ─────────────────────────────────────────────────────────────────

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: ButtonProps["variant"];
  };
  className?: string;
}

// ─── Component ─────────────────────────────────────────────────────────────

function EmptyState({
  icon,
  title,
  description,
  action,
  className = "",
}: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center py-12 text-center ${className}`.trim()}>
      <div className="w-16 h-16 rounded-2xl bg-cream-m flex items-center justify-center mb-4">
        {icon || <Inbox className="w-8 h-8 text-gray/50" />}
      </div>

      <h3 className="text-lg font-medium text-navy">{title}</h3>

      {description && (
        <p className="text-sm text-gray mt-1 max-w-sm">{description}</p>
      )}

      {action && (
        <Button
          variant={action.variant || "accent"}
          size="sm"
          onClick={action.onClick}
          className="mt-4"
        >
          {action.label}
        </Button>
      )}
    </div>
  );
}

EmptyState.displayName = "EmptyState";

export { EmptyState, type EmptyStateProps };
```

---

### `src/components/ui/index.ts`

```tsx
export { Button } from "./Button";
export type { ButtonProps, ButtonVariant, ButtonSize } from "./Button";

export { Card, CardHeader, CardTitle, CardContent, CardFooter } from "./Card";
export type { CardProps, CardHeaderProps, CardTitleProps, CardPadding, CardShadow, CardRounded } from "./Card";

export { Input } from "./Input";
export type { InputProps } from "./Input";

export { Textarea } from "./Textarea";
export type { TextareaProps } from "./Textarea";

export { Spinner, PageSpinner, ButtonSpinner } from "./Spinner";
export type { SpinnerProps, SpinnerSize, SpinnerColor } from "./Spinner";

export { Modal, ConfirmModal } from "./Modal";
export type { ModalProps, ConfirmModalProps } from "./Modal";

export { Badge } from "./Badge";
export type { BadgeProps, BadgeVariant, BadgeSize } from "./Badge";

export { StatusBadge, RoleBadge, presets } from "./StatusBadge";
export type { StatusBadgeProps, StatusVariant } from "./StatusBadge";

export { EmptyState } from "./EmptyState";
export type { EmptyStateProps } from "./EmptyState";
```

---

## 3. STRATÉGIE DE MIGRATION

### 3.1 — Script de détection des patterns inline

**Boutons inline (pattern le plus courant : `bg-orange text-white rounded-xl`) :**

```bash
cd D:\RAG_APP_new\frontend\src
grep -rn "bg-orange text-white rounded-xl\|bg-navy text-white rounded-xl\|bg-red-500 text-white rounded" \
  --include="*.tsx" --exclude-dir=ui --exclude-dir=__tests__ | \
  awk -F: '{print $1 ":" $2}' | sort
```

**Spinners inline (Loader2 + animate-spin) :**

```bash
cd D:\RAG_APP_new\frontend\src
grep -rn "animate-spin" --include="*.tsx" --exclude-dir=ui --exclude-dir=__tests__ | \
  awk -F: '{print $1 ":" $2}' | sort
```

**Modals inline (`fixed inset-0`) :**

```bash
cd D:\RAG_APP_new\frontend\src
grep -rn "fixed inset-0 bg-black" --include="*.tsx" --exclude-dir=ui --exclude-dir=__tests__ | \
  awk -F: '{print $1 ":" $2}' | sort
```

**Empty states (`Aucun` / `Aucune`) :**

```bash
cd D:\RAG_APP_new\frontend\src
grep -rn "Aucun \|Aucune " --include="*.tsx" --exclude-dir=ui --exclude-dir=__tests__ | \
  awk -F: '{print $1 ":" $2}' | sort
```

**Badges inline (`rounded-full bg-green-100 text-green-700`) :**

```bash
cd D:\RAG_APP_new\frontend\src
grep -rn "rounded-full bg-.*-100 text-.*-700\|rounded-full bg-.*-50 text-.*-600" \
  --include="*.tsx" --exclude-dir=ui --exclude-dir=__tests__ | \
  awk -F: '{print $1 ":" $2}' | sort
```

### 3.2 — Priorisation de migration

| Priorité | Composant | Occurrences | Impact |
|----------|-----------|-------------|--------|
| **P0** | `Button` | ~80 boutons inline | Élevé — normalise les CTAs |
| **P0** | `Spinner` | 35 fichiers | Élevé — élimine les loaders incohérents |
| **P1** | `Modal` | 18 modals inline | Élevé — accessibilité + DRY |
| **P1** | `EmptyState` | 24 occurrences | Moyen — standardise les états vides |
| **P1** | `Input` / `Textarea` | 16+ formulaires | Moyen — cohérence des formulaires |
| **P2** | `Badge` / `StatusBadge` | 13+ badges inline | Faible — principalement visuel |
| **P2** | `Card` | Utilisé partout | Faible — déjà partiellement standard |

### 3.3 — Processus de migration par fichier

```
1. Lister les composants UI inline dans le fichier (grep)
2. Ajouter l'import depuis ui/
3. Remplacer le JSX inline par le composant ui/
4. Vérifier les props (variant, size, etc.)
5. Supprimer les imports inutiles (Loader2 si remplacé par Spinner)
6. npx vite build pour vérifier
```

### 3.4 — Règles de migration

| Règle | Description |
|-------|-------------|
| **Un seul endroit pour les styles** | `src/components/ui/` est la source de vérité |
| **Pas de `className` de composition** | Utiliser les props (`variant`, `size`) plutôt que de surcharger les classes |
| **forwardRef partout** | Permettre l'usage avec `ref` (focus management, etc.) |
| **Aria attributes** | `aria-label`, `aria-invalid`, `role="alert"` pour l'accessibilité |
| **Pas de `any`** | Toutes les props sont typées |
| **Barrel export** | Un seul `import { Button, Card } from "../ui"` |

### 3.5 — Checklist de validation par fichier migré

- [ ] Plus de `Loader2` importé directement (utiliser `Spinner`)
- [ ] Plus de `bg-orange text-white rounded-xl` pour les boutons (utiliser `Button`)
- [ ] Plus de `fixed inset-0 bg-black` pour les modals (utiliser `Modal`)
- [ ] Plus de `Aucun` / `Aucune` sans `EmptyState`
- [ ] Plus de `rounded-full bg-green-100 text-green-700` (utiliser `Badge`)
- [ ] `npx vite build` passe sans erreur
- [ ] Composant fonctionne manuellement

---

## 4. AVANT / APRÈS — Exemples de migration

### Avant (AdminDashboard.tsx)

```tsx
<button
  onClick={() => updateCourseStatus(c.id, "published")}
  className="px-5 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl text-sm font-medium hover:opacity-90"
>
  Approuver
</button>
```

### Après

```tsx
<Button variant="accent" size="sm" onClick={() => updateCourseStatus(c.id, "published")}>
  Approuver
</Button>
```

### Avant (ClassroomManager.tsx spinner)

```tsx
<span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
```

### Après

```tsx
<Spinner size="sm" color="white" />
```

### Avant (24 empty states)

```tsx
<div className="text-center py-8 text-gray">
  <p>Aucune classe</p>
  <button onClick={() => setShowNewClass(true)} className="mt-3 text-orange text-sm font-medium">
    + Créer une classe
  </button>
</div>
```

### Après

```tsx
<EmptyState
  title="Aucune classe"
  description="Créez votre première classe pour commencer"
  action={{ label: "Créer une classe", onClick: () => setShowNewClass(true) }}
/>
```

---

**Blueprint généré le 05/08/2026 — Phase 2 Design System EDUAI Learning**
