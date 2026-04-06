import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import { AdminButton } from "./AdminButton";
import { AdminSection } from "./AdminSection";
import { CATEGORY_LABELS_FR } from "../../constants/categories";
import type { Dish, DishCategory } from "../../types/domain";

interface AdminCatalogSectionProps {
  dishes: Dish[];
  newDishName: string;
  newDishTags: string;
  newDishCategory: DishCategory;
  onNewDishNameChange: (value: string) => void;
  onNewDishTagsChange: (value: string) => void;
  onNewDishCategoryChange: (value: DishCategory) => void;
  onAddDish: (event: FormEvent<HTMLFormElement>) => void;
  onDeleteDish: (id: string) => void;
}

export function AdminCatalogSection({
  dishes,
  newDishName,
  newDishTags,
  newDishCategory,
  onNewDishNameChange,
  onNewDishTagsChange,
  onNewDishCategoryChange,
  onAddDish,
  onDeleteDish,
}: AdminCatalogSectionProps) {
  const [categoryFilter, setCategoryFilter] = useState<DishCategory | "all">("all");

  const filteredDishes = useMemo(
    () => {
      const filtered = categoryFilter === "all" ? dishes : dishes.filter((dish) => dish.category === categoryFilter);
      return [...filtered].sort((a, b) => a.name.localeCompare(b.name));
    },
    [categoryFilter, dishes],
  );

  return (
    <div className="admin-body">
      <AdminSection title="Catalogue" description="Créer un nouveau plat et gérer le catalogue existant.">
        <form onSubmit={onAddDish} className="form-grid">
          <label>
            Nom du plat
            <input value={newDishName} onChange={(event) => onNewDishNameChange(event.target.value)} />
          </label>
          <label>
            Tags (virgule séparés)
            <input value={newDishTags} onChange={(event) => onNewDishTagsChange(event.target.value)} />
          </label>
          <label>
            Catégorie
            <select value={newDishCategory} onChange={(event) => onNewDishCategoryChange(event.target.value as DishCategory)}>
              <option value="lunch">Déjeuner</option>
              <option value="dinner">Dîner</option>
              <option value="weekends_lunch">Weekend déjeuner</option>
              <option value="saturday_dinner">Samedi dîner</option>
            </select>
          </label>
          <AdminButton type="submit">Ajouter plat</AdminButton>
        </form>

        <div className="filters">
          <label>
            Filtrer par catégorie
            <select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value as DishCategory | "all")}>
              <option value="all">Tous ({dishes.length})</option>
              {Object.entries(CATEGORY_LABELS_FR).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </label>
        </div>

        {filteredDishes.length === 0 ? (
          <p>Aucun plat disponible.</p>
        ) : (
          <ul className="dish-list">
            {filteredDishes.map((dish) => (
              <li key={dish.id} className="dish-item">
                <div>
                  <strong>{dish.name}</strong>
                  <span className="category-label">{CATEGORY_LABELS_FR[dish.category]}</span>
                  {dish.tags.length > 0 && <p className="tag-row">{dish.tags.join(", ")}</p>}
                </div>
                <AdminButton onClick={() => onDeleteDish(dish.id)} type="button" danger>
                  Supprimer
                </AdminButton>
              </li>
            ))}
          </ul>
        )}
      </AdminSection>
    </div>
  );
}
