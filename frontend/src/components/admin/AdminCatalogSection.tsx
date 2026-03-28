import type { FormEvent } from "react";
import { AdminButton } from "./AdminButton";
import { AdminSection } from "./AdminSection";
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

const categoryLabel = (category: DishCategory) => {
  switch (category) {
    case "lunch":
      return "Déjeuner";
    case "dinner":
      return "Dîner";
    case "weekends_lunch":
      return "Weekend déjeuner";
    case "saturday_dinner":
      return "Samedi dîner";
    default:
      return category;
  }
};

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

        {dishes.length === 0 ? (
          <p>Aucun plat disponible.</p>
        ) : (
          <ul className="dish-list">
            {dishes.map((dish) => (
              <li key={dish.id} className="dish-item">
                <div>
                  <strong>{dish.name}</strong>
                  <span className="category-label">{categoryLabel(dish.category)}</span>
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
