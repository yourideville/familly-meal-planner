import { FormEvent, useState } from "react";

import { createVote } from "../api/client";
import type { Dish, Weekday } from "../types/domain";

const weekDays: Weekday[] = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
];

const weekDayLabels: Record<Weekday, string> = {
  monday: "Lundi",
  tuesday: "Mardi",
  wednesday: "Mercredi",
  thursday: "Jeudi",
  friday: "Vendredi",
  saturday: "Samedi",
  sunday: "Dimanche",
};

interface VotingPageProps {
  dishes: Dish[];
}

export function VotingPage({ dishes }: VotingPageProps) {
  const [userName, setUserName] = useState("Alex");
  const [dishId, setDishId] = useState("");
  const [day, setDay] = useState<Weekday>("monday");
  const [message, setMessage] = useState("");

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
            {weekDays.map((item) => (
              <option key={item} value={item}>
                {weekDayLabels[item]}
              </option>
            ))}
          </select>
        </label>
        <label>
          Plat
          <select value={dishId} onChange={(event) => setDishId(event.target.value)}>
            <option value="">Sélectionnez un plat</option>
            {dishes.map((dish) => (
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
