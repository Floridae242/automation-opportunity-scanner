import type { ButtonHTMLAttributes } from "react";

export function Button({
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      data-slot="button"
      className={`button button-secondary ${className}`}
      {...props}
    />
  );
}
