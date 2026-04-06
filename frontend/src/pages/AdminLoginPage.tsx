import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { loginAdmin } from "../api/client";

interface AdminLoginPageProps {
  onLoginSuccess: () => void;
}

export function AdminLoginPage({ onLoginSuccess }: AdminLoginPageProps) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    try {
      await loginAdmin({ username, password });
      onLoginSuccess();
      navigate("/admin");
    } catch {
      setError("Nom d'utilisateur ou mot de passe invalide.");
    }
  }

  return (
    <section className="card">
      <div className="section-head">
        <h2>Connexion administrateur</h2>
        <p>Veuillez vous connecter pour accéder aux fonctions d'administration.</p>
      </div>
      <form className="stack" onSubmit={handleSubmit}>
        <label>
          Nom d'utilisateur
          <input
            name="username"
            type="text"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoComplete="username"
          />
        </label>
        <label>
          Mot de passe
          <input
            name="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit">Se connecter</button>
      </form>
    </section>
  );
}
