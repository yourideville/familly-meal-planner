import type { ButtonHTMLAttributes } from "react";

interface AdminButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  danger?: boolean;
}

export function AdminButton({ children, className = "", danger, ...rest }: AdminButtonProps) {
  return (
    <button
      className={`admin-button ${danger ? "danger" : ""} ${className}`.trim()}
      {...rest}
    >
      {children}
    </button>
  );
}
