import type { Dish } from "../types/domain";

interface CatalogPageProps {
  dishes: Dish[];
}

export function CatalogPage({ dishes }: CatalogPageProps) {
  return (
    <section>
      <h2>Dish Catalog</h2>
      <ul>
        {dishes.map((dish) => (
          <li key={dish.id}>
            <strong>{dish.name}</strong>
            {dish.tags.length > 0 ? ` (${dish.tags.join(", ")})` : ""}
          </li>
        ))}
      </ul>
    </section>
  );
}
