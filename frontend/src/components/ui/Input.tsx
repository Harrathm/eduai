import { forwardRef, type InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = "", ...props }, ref) => (
    <div>
      {label && <label className="block text-sm font-medium text-gray mb-2">{label}</label>}
      <input
        ref={ref}
        className={`w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5 ${error ? "border-red-400" : ""} ${className}`}
        {...props}
      />
      {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
    </div>
  )
);
Input.displayName = "Input";
