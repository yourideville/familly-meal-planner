import type { FormEvent } from "react";
import { AdminButton } from "./AdminButton";
import { AdminSection } from "./AdminSection";

interface AdminMembersSectionProps {
  members: string[];
  memberEdits: Record<string, string>;
  newMemberName: string;
  onNewMemberNameChange: (value: string) => void;
  onAddMember: (event: FormEvent<HTMLFormElement>) => void;
  onUpdateMember: (oldName: string) => void;
  onDeleteMember: (name: string) => void;
  onMemberEditChange: (oldName: string, value: string) => void;
}

export function AdminMembersSection({
  members,
  memberEdits,
  newMemberName,
  onNewMemberNameChange,
  onAddMember,
  onUpdateMember,
  onDeleteMember,
  onMemberEditChange,
}: AdminMembersSectionProps) {
  return (
    <div className="admin-body">
      <AdminSection title="Membres" description="Ajouter, renommer ou supprimer un membre du foyer.">
        <form onSubmit={onAddMember} className="form-grid">
          <label>
            Nouveau membre
            <input value={newMemberName} onChange={(event) => onNewMemberNameChange(event.target.value)} />
          </label>
          <AdminButton type="submit">Ajouter membre</AdminButton>
        </form>

        <ul className="member-list">
          {members.map((member) => (
            <li key={member} className="member-item">
              <span>{member}</span>
              <input
                value={memberEdits[member] ?? member}
                onChange={(event) => onMemberEditChange(member, event.target.value)}
              />
              <div className="button-pair">
                <AdminButton onClick={() => onUpdateMember(member)} type="button">
                  Renommer
                </AdminButton>
                <AdminButton onClick={() => onDeleteMember(member)} type="button" danger>
                  Supprimer
                </AdminButton>
              </div>
            </li>
          ))}
        </ul>
      </AdminSection>
    </div>
  );
}
