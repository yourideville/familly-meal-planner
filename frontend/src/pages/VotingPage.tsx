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
      setMessage("Please select a dish.");
      return;
    }

    try {
      await createVote({ user_name: userName, dish_id: dishId, day });
      setMessage("Vote submitted.");
    } catch {
      setMessage("Could not submit vote.");
    }
  }

  return (
    <section>
      <h2>Voting</h2>
      <form onSubmit={onSubmit} className="stack">
        <label>
          Your name
          <input value={userName} onChange={(event) => setUserName(event.target.value)} />
        </label>
        <label>
          Day
          <select value={day} onChange={(event) => setDay(event.target.value as Weekday)}>
            {weekDays.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label>
          Dish
          <select value={dishId} onChange={(event) => setDishId(event.target.value)}>
            <option value="">Select one</option>
            {dishes.map((dish) => (
              <option key={dish.id} value={dish.id}>
                {dish.name}
              </option>
            ))}
          </select>
        </label>
        <button type="submit">Submit vote</button>
      </form>
      {message && <p>{message}</p>}
    </section>
  );
}
