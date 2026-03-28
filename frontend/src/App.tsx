import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes, useNavigate } from "react-router-dom";

import { getDishes, getWeeklyMenu, checkAdminSession, logoutAdmin } from "./api/client";
import { CatalogPage } from "./pages/CatalogPage";
import { VotingPage } from "./pages/VotingPage";
import { WeeklyMenuPage } from "./pages/WeeklyMenuPage";
import { AdminPage } from "./pages/AdminPage";
import { AdminLoginPage } from "./pages/AdminLoginPage";
import type { Dish, WeeklyMenuResponse } from "./types/domain";

export default function App() {
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [menu, setMenu] = useState<WeeklyMenuResponse | null>(null);
  const [error, setError] = useState("");
  const [isAdminAuthenticated, setAdminAuthenticated] = useState(false);
  const navigate = useNavigate();

  async function loadDishes() {
    try {
      setDishes(await getDishes());
    } catch {
      setError("Impossible de charger les plats. Le backend tourne-t-il sur :8000 ?");
    }
  }

  async function loadMenu() {
    try {
      setMenu(await getWeeklyMenu());
    } catch {
      setError("Impossible de charger le menu de la semaine.");
    }
  }

  async function loadSession() {
    try {
      const session = await checkAdminSession();
      setAdminAuthenticated(session.authenticated);
    } catch {
      setAdminAuthenticated(false);
    }
  }

  async function handleLogout() {
    try {
      await logoutAdmin();
      setAdminAuthenticated(false);
      navigate("/");
    } catch {
      setError("Impossible de se déconnecter.");
    }
  }

  useEffect(() => {
    void loadDishes();
    void loadMenu();
    void loadSession();
  }, []);

  return (
    <main className="container">
      <div className="app-shell">
        <header className="page-header">
          <p className="eyebrow">Repas de famille</p>
          <h1>Planificateur de repas</h1>
          <p>Organisez les repas familiaux de la semaine.</p>
        </header>
        <div className="top-actions">
          <nav className="nav">
            <NavLink to="/" className={({ isActive }) => (isActive ? "active" : "")}>
              Catalogue
            </NavLink>
            <NavLink to="/vote" className={({ isActive }) => (isActive ? "active" : "")}>
              Vote
            </NavLink>
            <NavLink to="/menu" className={({ isActive }) => (isActive ? "active" : "")}>
              Menu hebdomadaire{menu?.finalized ? " (validé)" : ""}
            </NavLink>
            <NavLink to="/admin" className={({ isActive }) => (isActive ? "active" : "")}>
              Admin
            </NavLink>
          </nav>
          <div className="auth-actions">
            {isAdminAuthenticated ? (
              <button type="button" onClick={handleLogout}>
                Se déconnecter
              </button>
            ) : (
              <button type="button" onClick={() => navigate("/admin/login")}>
                Se connecter
              </button>
            )}
          </div>
        </div>
        {error && <p className="error">{error}</p>}
        <Routes>
          <Route path="/" element={<CatalogPage dishes={dishes} />} />
          <Route path="/vote" element={<VotingPage dishes={dishes} />} />
          <Route path="/menu" element={<WeeklyMenuPage menu={menu} onRefresh={loadMenu} />} />
          <Route
            path="/admin"
            element={
              isAdminAuthenticated ? (
                <AdminPage dishes={dishes} refreshDishes={loadDishes} refreshMenu={loadMenu} menu={menu} />
              ) : (
                <Navigate to="/admin/login" replace />
              )
            }
          />
          <Route
            path="/admin/login"
            element={<AdminLoginPage onLoginSuccess={() => setAdminAuthenticated(true)} />}
          />
        </Routes>
      </div>
    </main>
  );
}
