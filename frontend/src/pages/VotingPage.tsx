import { FormEvent, useEffect, useMemo, useState } from "react";

import { createVote, getMembers, getVoteAvailability } from "../api/client";
import { WEEK_DAY_LABELS_FR, WEEK_DAYS } from "../constants/weekdays";
import { MEAL_LABELS_FR, MEALS } from "../constants/meals";
import type { Dish, DishCategory, Meal, VoteSlot, VotePayload, Weekday } from "../types/domain";

interface VotingPageProps {
  dishes: Dish[];
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

const getCategoryForSlot = (day: Weekday, meal: Meal): DishCategory => {
  if (meal === "lunch") {
    return day === "saturday" || day === "sunday" ? "weekends_lunch" : "lunch";
  }
  if (meal === "dinner") {
    return day === "saturday" ? "saturday_dinner" : "dinner";
  }
  return "dinner";
};

export function VotingPage({ dishes }: VotingPageProps) {
  const [dishId, setDishId] = useState("");
  const [day, setDay] = useState<Weekday>("monday");
  const [meal, setMeal] = useState<Meal>("lunch");
  const [members, setMembers] = useState<string[]>([]);
  const [selectedMember, setSelectedMember] = useState("");
  const [availability, setAvailability] = useState<AvailabilityMap>(initialAvailability);
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const memberList = await getMembers();
        setMembers(memberList);
        if (memberList.length > 0) {
          setSelectedMember(memberList[0]);
        }
      } catch {
        setMessage("Impossible de charger les membres.");
      }
    }

    void load();
  }, []);

  useEffect(() => {
    async function loadAvailability() {
      try {
        const slots: VoteSlot[] = await getVoteAvailability();
        const updated: AvailabilityMap = {
          monday: { lunch: true, dinner: true },
          tuesday: { lunch: true, dinner: true },
          wednesday: { lunch: true, dinner: true },
          thursday: { lunch: true, dinner: true },
          friday: { lunch: true, dinner: true },
          saturday: { lunch: true, dinner: true },
          sunday: { lunch: true, dinner: true },
        };
        slots.forEach((slot) => {
          updated[slot.day][slot.meal] = slot.available;
        });
        setAvailability(updated);
      } catch {
        setMessage("Impossible de charger la disponibilité des votes.");
      }
    }

    void loadAvailability();
  }, []);

  const openDays = useMemo(
    () => WEEK_DAYS.filter((item) => availability[item].lunch || availability[item].dinner),
    [availability],
  );

  useEffect(() => {
    if (openDays.length === 0) {
      return;
    }
    if (!openDays.includes(day)) {
      setDay(openDays[0]);
    }
  }, [day, openDays]);

  const openMeals = useMemo(
    () => MEALS.filter((item) => availability[day]?.[item]),
    [availability, day],
  );

  const noOpenSlots = openDays.length === 0;

  useEffect(() => {
    if (openMeals.length === 0) {
      return;
    }
    if (!openMeals.includes(meal)) {
      setMeal(openMeals[0]);
    }
  }, [meal, openMeals]);

  const slotCategory = getCategoryForSlot(day, meal);

  const availableDishes = useMemo(() => {
    const filtered = dishes.filter((dish) => dish.category === slotCategory);
    return filtered.length > 0 ? filtered : dishes;
  }, [dishes, slotCategory]);

  const slotAvailable = availability[day]?.[meal] ?? false;

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!dishId) {
      setMessage("Veuillez sélectionner un plat.");
      return;
    }
    if (!selectedMember) {
      setMessage("Veuillez sélectionner un membre.");
      return;
    }
    if (!slotAvailable) {
      setMessage("Ce créneau n'est pas disponible pour voter.");
      return;
    }

    try {
      await createVote({ user_name: selectedMember, dish_id: dishId, day, meal } as VotePayload);
      setMessage("Vote enregistré.");
    } catch {
      setMessage("Impossible d'envoyer le vote.");
    }
  }

  return (
    <section className="card">
      <div className="section-head">
        <h2>Vote</h2>
        <p>Exprimez votre préférence pour le déjeuner ou le dîner.</p>
      </div>
      <form onSubmit={onSubmit} className="stack">
        <label>
          Membre
          <select value={selectedMember} onChange={(event) => setSelectedMember(event.target.value)}>
            <option value="">Sélectionnez un membre</option>
            {members.map((member) => (
              <option key={member} value={member}>
                {member}
              </option>
            ))}
          </select>
        </label>
        <label>
          Jour
          <select
            value={day}
            onChange={(event) => setDay(event.target.value as Weekday)}
            disabled={noOpenSlots}
          >
            {noOpenSlots ? (
              <option value="">Aucun jour ouvert</option>
            ) : (
              openDays.map((item) => (
                <option key={item} value={item}>
                  {WEEK_DAY_LABELS_FR[item]}
                </option>
              ))
            )}
          </select>
        </label>
        <label>
          Repas
          <select
            value={meal}
            onChange={(event) => setMeal(event.target.value as Meal)}
            disabled={noOpenSlots || openMeals.length === 0}
          >
            {openMeals.length === 0 ? (
              <option value="">Aucun repas ouvert</option>
            ) : (
              openMeals.map((item) => (
                <option key={item} value={item}>
                  {MEAL_LABELS_FR[item]}
                </option>
              ))
            )}
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
        <p>Catégorie du créneau : {slotCategory.split("_").join(" ")}</p>
        <button type="submit" disabled={!slotAvailable || openDays.length === 0 || openMeals.length === 0}>
          Envoyer le vote
        </button>
        {openDays.length === 0 && <p className="error">Aucun créneau de vote ouvert actuellement.</p>}
      </form>
      {!slotAvailable && <p className="error">Ce créneau n'est pas disponible pour voter.</p>}
      {message && <p className="info">{message}</p>}
    </section>
  );
}
