import type { ReactNode } from "react";

interface AdminSectionProps {
  title: string;
  description: string;
  children: ReactNode;
}

export function AdminSection({ title, description, children }: AdminSectionProps) {
  return (
    <section className="admin-section">
      <div className="section-head-row">
        <div>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
      </div>
      {children}
    </section>
  );
}
