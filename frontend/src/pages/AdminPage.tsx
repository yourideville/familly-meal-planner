import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  createDish,
  createMember,
  deleteDish,
  deleteMember,
  getMembers,
  getVoteAvailability,
  getVotes,
  setMenuItem,
  setShortlist,
  setVoteAvailability,
  unvalidateWeeklyMenu,
  validateWeeklyMenu,
  updateMember,
} from "../api/client";
import { AdminMembersSection } from "../components/admin/AdminMembersSection";
import { AdminCatalogSection } from "../components/admin/AdminCatalogSection";
import { AdminVotesSection } from "../components/admin/AdminVotesSection";
import { AdminMenuSection } from "../components/admin/AdminMenuSection";
import { AdminSectionNav } from "../components/admin/AdminSectionNav";
import { WEEK_DAY_LABELS_FR, WEEK_DAYS } from "../constants/weekdays";
import { MEAL_LABELS_FR, MEALS } from "../constants/meals";
import type {
  Dish,
  DishCategory,
  Meal,
  Vote,
  VoteSlot,
  WeeklyMenuResponse,
  Weekday,
} from "../types/domain";

interface AdminPageProps {
  dishes: Dish[];
  refreshDishes: () => Promise<void>;
  refreshMenu: () => Promise<void>;
  menu: WeeklyMenuResponse | null;
}

type AvailabilityMap = Record<Weekday, Record<Meal, boolean>>;
type AdminTab = "members" | "catalog" | "votes" | "menu";

const initialAvailability: AvailabilityMap = {
  monday: { lunch: true, dinner: true },
  tuesday: { lunch: true, dinner: true },
  wednesday: { lunch: true, dinner: true },
  thursday: { lunch: true, dinner: true },
  friday: { lunch: true, dinner: true },
  saturday: { lunch: true, dinner: true },
  sunday: { lunch: true, dinner: true },
};

const categoryLabel = (category: DishCategory) => {
  switch (category) {
    case "lunch":
      return "Déjeuner";
    case "dinner":
      return "Dîner";
    case "weekends_lunch":
      return "Weekend déjeuner";
    case "saturday_dinner":
      return "Samedi dîner";
    default:
      return category;
  }
};

const sectionLabels: Record<AdminTab, string> = {
  members: "Membres",
  catalog: "Catalogue",
  votes: "Votes",
  menu: "Menu",
};

export function AdminPage({ dishes, refreshDishes, refreshMenu, menu }: AdminPageProps) {
  const [newDishName, setNewDishName] = useState("");
  const [newDishTags, setNewDishTags] = useState("");
  const [newDishCategory, setNewDishCategory] = useState<DishCategory>("lunch");
  const [members, setMembers] = useState<string[]>([]);
  const [memberEdits, setMemberEdits] = useState<Record<string, string>>({});
  const [newMemberName, setNewMemberName] = useState("");
  const [availability, setAvailability] = useState<AvailabilityMap>(initialAvailability);
  const [selectedDay, setSelectedDay] = useState<Weekday>("monday");
  const [selectedMeal, setSelectedMeal] = useState<Meal>("lunch");
  const [selectedShortlist, setSelectedShortlist] = useState<string[]>([]);
  const [selectedManualDish, setSelectedManualDish] = useState("");
  const [message, setMessage] = useState("");
  const [selectedSection, setSelectedSection] = useState<AdminTab>("members");
  const [votes, setVotes] = useState<Vote[]>([]);

  useEffect(() => {
    void loadMembers();
    void loadAvailability();
  }, []);

  useEffect(() => {
    setSelectedShortlist(menu?.shortlists?.[selectedDay]?.[selectedMeal] ?? []);
    const slot = menu?.items.find((item) => item.day === selectedDay && item.meal === selectedMeal);
    setSelectedManualDish(slot?.dish?.id ?? "");
  }, [menu, selectedDay, selectedMeal]);

  useEffect(() => {
    async function loadVotes() {
      try {
        setVotes(await getVotes());
      } catch {
        // Ignore errors for now.
      }
    }

    void loadVotes();
  }, []);

  const shortlist = useMemo(
    () => menu?.shortlists?.[selectedDay]?.[selectedMeal] ?? [],
    [menu, selectedDay, selectedMeal],
  );

  const votesBySlot = useMemo(() => {
    const result: Record<Weekday, Record<Meal, Vote[]>> = {
      monday: { lunch: [], dinner: [] },
      tuesday: { lunch: [], dinner: [] },
      wednesday: { lunch: [], dinner: [] },
      thursday: { lunch: [], dinner: [] },
      friday: { lunch: [], dinner: [] },
      saturday: { lunch: [], dinner: [] },
      sunday: { lunch: [], dinner: [] },
    };

    votes.forEach((vote) => {
      result[vote.day][vote.meal].push(vote);
    });

    return result;
  }, [votes]);

  async function loadMembers() {
    try {
      setMembers(await getMembers());
    } catch {
      setMessage("Impossible de charger les membres.");
    }
  }

  async function loadAvailability() {
    try {
      const slots: VoteSlot[] = await getVoteAvailability();
      const updatedAvailability: AvailabilityMap = {
        monday: { lunch: true, dinner: true },
        tuesday: { lunch: true, dinner: true },
        wednesday: { lunch: true, dinner: true },
        thursday: { lunch: true, dinner: true },
        friday: { lunch: true, dinner: true },
        saturday: { lunch: true, dinner: true },
        sunday: { lunch: true, dinner: true },
      };
      slots.forEach((slot) => {
        updatedAvailability[slot.day][slot.meal] = slot.available;
      });
      setAvailability(updatedAvailability);
    } catch {
      setMessage("Impossible de charger la disponibilité des votes.");
    }
  }

  async function onAddMember(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!newMemberName.trim()) {
      setMessage("Nom du membre requis");
      return;
    }

    try {
      await createMember({ name: newMemberName.trim() });
      setNewMemberName("");
      await loadMembers();
      setMessage("Membre ajouté.");
    } catch {
      setMessage("Impossible d'ajouter le membre.");
    }
  }

  async function onUpdateMember(oldName: string) {
    const newName = memberEdits[oldName]?.trim();
    if (!newName) {
      setMessage("Nouveau nom requis");
      return;
    }

    try {
      await updateMember(oldName, { name: newName });
      await loadMembers();
      setMessage("Membre modifié.");
    } catch {
      setMessage("Impossible de modifier le membre.");
    }
  }

  async function onDeleteMember(name: string) {
    try {
      await deleteMember(name);
      await loadMembers();
      setMessage("Membre supprimé.");
    } catch {
      setMessage("Impossible de supprimer le membre.");
    }
  }

  async function onAddDish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!newDishName.trim()) {
      setMessage("Nom du plat requis");
      return;
    }

    try {
      await createDish({
        name: newDishName.trim(),
        tags: newDishTags.split(",").map((tag) => tag.trim()).filter(Boolean),
        category: newDishCategory,
      });
      await refreshDishes();
      setNewDishName("");
      setNewDishTags("");
      setNewDishCategory("lunch");
      setMessage("Plat ajouté");
    } catch {
      setMessage("Impossible d'ajouter le plat.");
    }
  }

  async function onDeleteDish(id: string) {
    try {
      await deleteDish(id);
      await refreshDishes();
      setMessage("Plat supprimé");
    } catch {
      setMessage("Impossible de supprimer le plat.");
    }
  }

  async function onValidateMenu() {
    try {
      await validateWeeklyMenu();
      await refreshMenu();
      setMessage("Menu final validé.");
    } catch {
      setMessage("Impossible de valider le menu.");
    }
  }

  async function onUnvalidateMenu() {
    try {
      await unvalidateWeeklyMenu();
      await refreshMenu();
      setMessage("Menu dévalidé.");
    } catch {
      setMessage("Impossible de dévalider le menu.");
    }
  }

  async function onSetShortlist() {
    try {
      await setShortlist(selectedDay, selectedMeal, selectedShortlist);
      await refreshMenu();
      setMessage("Shortlist mise à jour.");
    } catch {
      setMessage("Impossible de définir la shortlist.");
    }
  }

  async function onToggleAvailability(day: Weekday, meal: Meal) {
    const updatedAvailability: AvailabilityMap = {
      ...availability,
      [day]: { ...availability[day], [meal]: !availability[day][meal] },
    };
    try {
      await setVoteAvailability(
        WEEK_DAYS.flatMap((slotDay) =>
          MEALS.map((slotMeal) => ({
            day: slotDay,
            meal: slotMeal,
            available: updatedAvailability[slotDay][slotMeal],
          })),
        ),
      );
      setAvailability(updatedAvailability);
      setMessage("Disponibilité mise à jour.");
    } catch {
      setMessage("Impossible de mettre à jour la disponibilité.");
    }
  }

  async function onSetManualMenu() {
    try {
      await setMenuItem(selectedDay, selectedMeal, selectedManualDish || null);
      await refreshMenu();
      setMessage("Remplacement manuel enregistré.");
    } catch {
      setMessage("Impossible d'enregistrer le remplacement manuel.");
    }
  }

  return (
    <section className="card">
      <div className="section-head">
        <h2>Administration</h2>
        <p>Navigation par section pour une gestion plus simple du foyer.</p>
      </div>

      <AdminSectionNav
        sections={(Object.keys(sectionLabels) as AdminTab[]).map((section) => ({
          id: section,
          label: sectionLabels[section],
        }))}
        selectedSection={selectedSection}
        onSelect={setSelectedSection}
      />

      {message && <p className="info">{message}</p>}

      {selectedSection === "members" && (
        <AdminMembersSection
          members={members}
          memberEdits={memberEdits}
          newMemberName={newMemberName}
          onNewMemberNameChange={setNewMemberName}
          onAddMember={onAddMember}
          onUpdateMember={onUpdateMember}
          onDeleteMember={onDeleteMember}
          onMemberEditChange={(name, value) => setMemberEdits((prev) => ({ ...prev, [name]: value }))}
        />
      )}

      {selectedSection === "catalog" && (
        <AdminCatalogSection
          dishes={dishes}
          newDishName={newDishName}
          newDishTags={newDishTags}
          newDishCategory={newDishCategory}
          onNewDishNameChange={setNewDishName}
          onNewDishTagsChange={setNewDishTags}
          onNewDishCategoryChange={setNewDishCategory}
          onAddDish={onAddDish}
          onDeleteDish={onDeleteDish}
        />
      )}

      {selectedSection === "votes" && (
        <AdminVotesSection
          dishes={dishes}
          availability={availability}
          selectedDay={selectedDay}
          selectedMeal={selectedMeal}
          selectedShortlist={selectedShortlist}
          onSelectDay={setSelectedDay}
          onSelectMeal={setSelectedMeal}
          onToggleAvailability={onToggleAvailability}
          onToggleShortlist={(dishId, selected) => {
            setSelectedShortlist((prev) =>
              selected ? [...prev, dishId] : prev.filter((id) => id !== dishId),
            );
          }}
          onSetShortlist={onSetShortlist}
          shortlist={shortlist}
        />
      )}

      {selectedSection === "menu" && (
        <AdminMenuSection
          dishes={dishes}
          selectedDay={selectedDay}
          selectedMeal={selectedMeal}
          selectedManualDish={selectedManualDish}
          onSelectDay={setSelectedDay}
          onSelectMeal={setSelectedMeal}
          onSelectManualDish={setSelectedManualDish}
          onSetManualMenu={onSetManualMenu}
          onValidateMenu={onValidateMenu}
          onUnvalidateMenu={onUnvalidateMenu}
          menu={menu}
        />
      )}
    </section>
  );
}
