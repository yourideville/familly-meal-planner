type AdminSectionNavItem<SectionId extends string> = {
  id: SectionId;
  label: string;
};

interface AdminSectionNavProps<SectionId extends string> {
  sections: AdminSectionNavItem<SectionId>[];
  selectedSection: SectionId;
  onSelect: (sectionId: SectionId) => void;
}

export function AdminSectionNav<SectionId extends string>({ sections, selectedSection, onSelect }: AdminSectionNavProps<SectionId>) {
  return (
    <div className="admin-section-nav" role="tablist">
      {sections.map((section) => (
        <button
          key={section.id}
          type="button"
          role="tab"
          className={selectedSection === section.id ? "active" : ""}
          aria-selected={selectedSection === section.id}
          onClick={() => onSelect(section.id)}
        >
          {section.label}
        </button>
      ))}
    </div>
  );
}
