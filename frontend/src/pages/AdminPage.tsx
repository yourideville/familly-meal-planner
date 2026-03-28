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
      setMessage("Override de plat enregistré.");
    } catch {
      setMessage("Impossible d'enregistrer l'override.");
    }
  }

  return (
    <section className="card">
      <div className="section-head">
        <h2>Administration</h2>
        <p>Gestion des membres, disponibilité, catalogue et menu.</p>
      </div>
      <div className="stack">
        <form onSubmit={onAddMember} className="inline-form">
          <label>
            Nouveau membre
            <input value={newMemberName} onChange={(event) => setNewMemberName(event.target.value)} />
          </label>
          <button type="submit">Ajouter membre</button>
        </form>

        <div>
          <h3>Membres</h3>
          <ul className="member-list">
            {members.map((member) => (
              <li key={member} className="member-item">
                <span>{member}</span>
                <input
                  value={memberEdits[member] ?? member}
                  onChange={(event) => setMemberEdits((prev) => ({ ...prev, [member]: event.target.value }))}
                />
                <button onClick={() => void onUpdateMember(member)} type="button">
                  Renommer
                </button>
                <button onClick={() => void onDeleteMember(member)} type="button">
                  Supprimer
                </button>
              </li>
            ))}
          </ul>
        </div>

        <form onSubmit={onAddDish} className="inline-form">
          <label>
            Nom du plat
            <input value={newDishName} onChange={(event) => setNewDishName(event.target.value)} />
          </label>
          <label>
            Tags (virgule séparés)
            <input value={newDishTags} onChange={(event) => setNewDishTags(event.target.value)} />
          </label>
          <label>
            Catégorie
            <select value={newDishCategory} onChange={(event) => setNewDishCategory(event.target.value as DishCategory)}>
              <option value="lunch">Déjeuner</option>
              <option value="dinner">Dîner</option>
              <option value="weekends_lunch">Weekend déjeuner</option>
              <option value="saturday_dinner">Samedi dîner</option>
            </select>
          </label>
          <button type="submit">Ajouter plat</button>
        </form>

        <div>
          <h3>Catalogue</h3>
          {dishes.length === 0 ? (
            <p>Aucun plat</p>
          ) : (
            <ul className="dish-list">
              {dishes.map((dish) => (
                <li key={dish.id}>
                  <strong>{dish.name}</strong> ({categoryLabel(dish.category)}) {dish.tags.join(", ")}
                  <button onClick={() => void onDeleteDish(dish.id)} type="button">
                    supprimer
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h3>Disponibilité des votes</h3>
          <table className="availability-table">
            <thead>
              <tr>
                <th>Jour</th>
                {MEALS.map((meal) => (
                  <th key={meal}>{MEAL_LABELS_FR[meal]}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {WEEK_DAYS.map((day) => (
                <tr key={day}>
                  <td>{WEEK_DAY_LABELS_FR[day]}</td>
                  {MEALS.map((meal) => (
                    <td key={meal}>
                      <button onClick={() => void onToggleAvailability(day, meal)} type="button">
                        {availability[day][meal] ? "Ouvert" : "Fermé"}
                      </button>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div>
          <h3>Shortlist par créneau</h3>
          <label>
            Jour
            <select value={selectedDay} onChange={(event) => setSelectedDay(event.target.value as Weekday)}>
              {WEEK_DAYS.map((day) => (
                <option key={day} value={day}>
                  {WEEK_DAY_LABELS_FR[day]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Repas
            <select value={selectedMeal} onChange={(event) => setSelectedMeal(event.target.value as Meal)}>
              {MEALS.map((meal) => (
                <option key={meal} value={meal}>
                  {MEAL_LABELS_FR[meal]}
                </option>
              ))}
            </select>
          </label>
          <div className="shortlist-grid">
            {dishes.map((dish) => (
              <label key={dish.id}>
                <input
                  type="checkbox"
                  checked={selectedShortlist.includes(dish.id)}
                  onChange={(event) => {
                    if (event.target.checked) {
                      setSelectedShortlist((prev) => [...prev, dish.id]);
                    } else {
                      setSelectedShortlist((prev) => prev.filter((id) => id !== dish.id));
                    }
                  }}
                />
                {dish.name}
              </label>
            ))}
          </div>
          <button onClick={onSetShortlist} type="button">
            Enregistrer shortlist
          </button>
          <p>
            Shortlist actuelle pour {WEEK_DAY_LABELS_FR[selectedDay]} {MEAL_LABELS_FR[selectedMeal]} : {shortlist
              .map((id) => dishes.find((dish) => dish.id === id)?.name)
              .filter(Boolean)
              .join(", ") || "(vide)"}
          </p>
        </div>

        <div>
          <h3>Override manuel par créneau</h3>
          <label>
            Jour
            <select value={selectedDay} onChange={(event) => setSelectedDay(event.target.value as Weekday)}>
              {WEEK_DAYS.map((day) => (
                <option key={day} value={day}>
                  {WEEK_DAY_LABELS_FR[day]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Repas
            <select value={selectedMeal} onChange={(event) => setSelectedMeal(event.target.value as Meal)}>
              {MEALS.map((meal) => (
                <option key={meal} value={meal}>
                  {MEAL_LABELS_FR[meal]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Plat manuel
            <select value={selectedManualDish} onChange={(event) => setSelectedManualDish(event.target.value)}>
              <option value="">Utiliser les votes</option>
              {dishes.map((dish) => (
                <option key={dish.id} value={dish.id}>{dish.name}</option>
              ))}
            </select>
          </label>
          <button onClick={onSetManualMenu} type="button">
            Enregistrer override
          </button>
        </div>

        <div>
          <h3>Validation finale</h3>
          <button onClick={onValidateMenu} type="button" disabled={menu?.finalized}>
            Valider menu hebdomadaire
          </button>
          <button onClick={onUnvalidateMenu} type="button" disabled={!menu?.finalized}>
            Dévalider menu hebdomadaire
          </button>
          <p>État finalisé : {menu?.finalized ? "oui" : "non"}</p>
        </div>

        {message && <p className="info">{message}</p>}
      </div>
    </section>
  );
}
