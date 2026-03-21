import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";

import { getDishes, getWeeklyMenu } from "./api/client";
import { CatalogPage } from "./pages/CatalogPage";
import { VotingPage } from "./pages/VotingPage";
import { WeeklyMenuPage } from "./pages/WeeklyMenuPage";
import type { Dish, WeeklyMenuResponse } from "./types/domain";

export default function App() {
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [menu, setMenu] = useState<WeeklyMenuResponse | null>(null);
  const [error, setError] = useState("");

  async function loadDishes() {
    try {
      setDishes(await getDishes());
    } catch {
      setError("Could not load dishes. Is backend running on :8000?");
    }
  }

  async function loadMenu() {
    try {
      setMenu(await getWeeklyMenu());
    } catch {
      setError("Could not load weekly menu.");
    }
  }

  useEffect(() => {
    void loadDishes();
    void loadMenu();
  }, []);

  return (
    <main className="container">
      <h1>Family Meal Planner - MVP</h1>
      <nav className="nav">
        <Link to="/">Catalog</Link>
        <Link to="/vote">Vote</Link>
        <Link to="/menu">Weekly Menu</Link>
      </nav>
      {error && <p className="error">{error}</p>}
      <Routes>
        <Route path="/" element={<CatalogPage dishes={dishes} />} />
        <Route path="/vote" element={<VotingPage dishes={dishes} />} />
        <Route path="/menu" element={<WeeklyMenuPage menu={menu} onRefresh={loadMenu} />} />
      </Routes>
    </main>
  );
}
