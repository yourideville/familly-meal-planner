import { FormEvent, useMemo, useState } from "react";

import { createVote } from "../api/client";
import { WEEK_DAYS, WEEK_DAY_LABELS_FR } from "../constants/weekdays";
import type { Dish, WeeklyMenuResponse, Weekday } from "../types/domain";

interface VotingPageProps {
  dishes: Dish[];
  menu: WeeklyMenuResponse | null;
}

export function VotingPage({ dishes, menu }: VotingPageProps) {
  const [userName, setUserName] = useState("Alex");
  const [dishId, setDishId] = useState("");
  const [day, setDay] = useState<Weekday>("monday");
  const [message, setMessage] = useState("");

  const availableDishes = useMemo(() => {
    const shortlist = menu?.shortlists?.[day] ?? [];
    if (shortlist.length > 0) {
      return dishes.filter(dish => shortlist.includes(dish.id));
    }
    return dishes;
  }, [dishes, menu, day]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!dishId) {
      setMessage("Veuillez sélectionner un plat.");
      return;
    }

    try {
      await createVote({ user_name: userName, dish_id: dishId, day });
      setMessage("Vote enregistré.");
    } catch {
      setMessage("Impossible d'envoyer le vote.");
    }
  }

  return (
    <section className="card">
      <div className="section-head">
        <h2>Vote</h2>
        <p>Exprimez votre préférence du jour.</p>
      </div>
      <form onSubmit={onSubmit} className="stack">
        <label>
          Votre nom
          <input value={userName} onChange={(event) => setUserName(event.target.value)} />
        </label>
        <label>
          Jour
          <select value={day} onChange={(event) => setDay(event.target.value as Weekday)}>
            {WEEK_DAYS.map((item) => (
              <option key={item} value={item}>
                {WEEK_DAY_LABELS_FR[item]}
              </option>
            ))}
          </select>
        </label>
        <label>
          Plat
          <select value={dishId} onChange={(event) => setDishId(event.target.value)}>
            <option value="">Sélectionnez un plat</option>
            {availableDishes.map((dish) => (
              <option key={dish.id} value={dish.id}>
                {dish.name}
              </option>
            ))}
          </select>
        </label>
        <button type="submit">Envoyer le vote</button>
      </form>
      {message && <p className="info">{message}</p>}
    </section>
  );
}
