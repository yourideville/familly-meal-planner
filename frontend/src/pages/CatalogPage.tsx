import { useMemo, useState } from "react";
import type { Dish, DishCategory } from "../types/domain";
import { CATEGORY_LABELS_FR } from "../constants/categories";

interface CatalogPageProps {
  dishes: Dish[];
}

export function CatalogPage({ dishes }: CatalogPageProps) {
  const [categoryFilter, setCategoryFilter] = useState<DishCategory | "all">("all");

  const filteredDishes = useMemo(
    () => {
      const filtered = categoryFilter === "all" ? dishes : dishes.filter((dish) => dish.category === categoryFilter);
      return [...filtered].sort((a, b) => a.name.localeCompare(b.name));
    },
    [categoryFilter, dishes],
  );

  return (
    <section className="card">
      <div className="section-head">
        <h2>Catalogue des plats</h2>
        <p>{filteredDishes.length} plats disponibles</p>
      </div>
      <div className="filters">
        <button type="button" onClick={() => setCategoryFilter("all")} className={categoryFilter === "all" ? "active" : ""}>
          Tous
        </button>
        {Object.entries(CATEGORY_LABELS_FR).map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setCategoryFilter(key as DishCategory)}
            className={categoryFilter === key ? "active" : ""}
          >
            {label}
          </button>
        ))}
      </div>
      {filteredDishes.length === 0 ? (
        <p className="empty">Aucun plat disponible pour le moment.</p>
      ) : (
        <ul className="dish-list">
          {filteredDishes.map((dish) => (
            <li key={dish.id} className="dish-item">
              <div>
                <strong>{dish.name}</strong>
                <span className="category-label">{CATEGORY_LABELS_FR[dish.category]}</span>
              </div>
              {dish.tags.length > 0 && (
                <div className="tags">
                  {dish.tags.map((tag) => (
                    <span key={`${dish.id}-${tag}`} className="tag">
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
