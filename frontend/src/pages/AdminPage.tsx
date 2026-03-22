import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  createDish,
  deleteDish,
  getDishes,
  getVotes,
  setMenuItem,
  setShortlist,
  unvalidateWeeklyMenu,
  updateDish,
  validateWeeklyMenu,
} from "../api/client";
import { WEEK_DAY_LABELS_FR, WEEK_DAYS } from "../constants/weekdays";
import type { Dish, Vote, WeeklyMenuResponse, Weekday } from "../types/domain";

interface AdminPageProps {
  dishes: Dish[];
  refreshDishes: () => Promise<void>;
  refreshMenu: () => Promise<void>;
  menu: WeeklyMenuResponse | null;
}

export function AdminPage({ dishes, refreshDishes, refreshMenu, menu }: AdminPageProps) {
  const [newDishName, setNewDishName] = useState("");
  const [newDishTags, setNewDishTags] = useState("");
  const [selectedDay, setSelectedDay] = useState<Weekday>("monday");
  const [selectedShortlist, setSelectedShortlist] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [votes, setVotes] = useState<Vote[]>([]);
  const [manualMenu, setManualMenu] = useState<Record<Weekday, string>>({
    monday: "",
    tuesday: "",
    wednesday: "",
    thursday: "",
    friday: "",
    saturday: "",
    sunday: "",
  });

  useEffect(() => {
    setSelectedShortlist(menu?.shortlists?.[selectedDay] ?? []);
  }, [menu, selectedDay]);

  const shortlist = useMemo(() => menu?.shortlists?.[selectedDay] ?? [], [menu, selectedDay]);

  const votesByDay = useMemo(() => {
    const result: Record<Weekday, Vote[]> = {
      monday: [],
      tuesday: [],
      wednesday: [],
      thursday: [],
      friday: [],
      saturday: [],
      sunday: [],
    };
    votes.forEach((vote) => {
      result[vote.day].push(vote);
    });
    return result;
  }, [votes]);

  useEffect(() => {
    async function loadVotes() {
      try {
        setVotes(await getVotes());
      } catch {
        // Ignore errors for now
      }
    }

    void loadVotes();
  }, []);


  async function onAddDish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!newDishName.trim()) {
      setMessage("Nom du plat requis");
      return;
    }

    try {
      await createDish({ name: newDishName.trim(), tags: newDishTags.split(",").map((tag) => tag.trim()).filter(Boolean) });
      await refreshDishes();
      setNewDishName("");
      setNewDishTags("");
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
      await setShortlist(selectedDay, selectedShortlist);
      await refreshMenu();
      setMessage("Shortlist mise à jour.");
    } catch {
      setMessage("Impossible de définir la shortlist.");
    }
  }

  return (
    <section className="card">
      <div className="section-head">
        <h2>Administration</h2>
        <p>Gestion catalogue, shortlist et validation finale.</p>
      </div>
      <div className="stack">
        <form onSubmit={onAddDish} className="inline-form">
          <label>
            Nom du plat
            <input value={newDishName} onChange={(event) => setNewDishName(event.target.value)} />
          </label>
          <label>
            Tags (virgule séparés)
            <input value={newDishTags} onChange={(event) => setNewDishTags(event.target.value)} />
          </label>
          <button type="submit">Ajouter</button>
        </form>

        <div>
          <h3>Catalogue</h3>
          {dishes.length === 0 ? (
            <p>Aucun plat</p>
          ) : (
            <ul className="dish-list">
              {dishes.map((dish) => (
                <li key={dish.id}>
                  <strong>{dish.name}</strong> {dish.tags.join(", ")}
                  <button onClick={() => void onDeleteDish(dish.id)} type="button">
                    supprimer
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h3>Shortlist par jour</h3>
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
          <p>Shortlist actuelle pour {WEEK_DAY_LABELS_FR[selectedDay]} : {shortlist.join(", ") || "(vide)"}</p>
        </div>

        <div>
          <h3>Vue semaine avec votes</h3>
          <ul className="menu-list">
            {WEEK_DAYS.map(day => {
              const dayVotes = votesByDay[day];
              const menuItem = menu?.items.find(item => item.day === day);
              const shortlist = menu?.shortlists?.[day] ?? [];
              return (
                <li key={day} className="menu-item">
                  <span className="day-pill">{WEEK_DAY_LABELS_FR[day]}</span>
                  <div>
                    <label>
                      Plat manuel:
                      <select
                        value={manualMenu[day]}
                        onChange={async (event) => {
                          const dishId = event.target.value || null;
                          setManualMenu(prev => ({ ...prev, [day]: dishId }));
                          try {
                            await setMenuItem(day, dishId);
                            await refreshMenu();
                          } catch {
                            // Revert on error
                            setManualMenu(prev => ({ ...prev, [day]: prev[day] }));
                          }
                        }}
                      >
                        <option value="">Utiliser les votes</option>
                        {dishes.map(dish => (
                          <option key={dish.id} value={dish.id}>{dish.name}</option>
                        ))}
                      </select>
                    </label>
                    <br />
                    <strong>{menuItem?.dish?.name ?? "Pas de plat"}</strong>
                    <br />
                    <small>Votes: {dayVotes.length > 0 ? dayVotes.map(v => `${v.user_name} (${dishes.find(d => d.id === v.dish_id)?.name})`).join(", ") : "Aucun"}</small>
                    {shortlist.length > 0 && <br />}
                    {shortlist.length > 0 && <small>Shortlist: {shortlist.map(id => dishes.find(d => d.id === id)?.name).join(", ")}</small>}
                  </div>
                </li>
              );
            })}
          </ul>
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
