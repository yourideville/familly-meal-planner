import type { Dish } from "../types/domain";

interface CatalogPageProps {
  dishes: Dish[];
}

export function CatalogPage({ dishes }: CatalogPageProps) {
  return (
    <section className="card">
      <div className="section-head">
        <h2>Catalogue des plats</h2>
        <p>{dishes.length} plats disponibles</p>
      </div>
      {dishes.length === 0 ? (
        <p className="empty">Aucun plat disponible pour le moment.</p>
      ) : (
        <ul className="dish-list">
          {dishes.map((dish) => (
            <li key={dish.id} className="dish-item">
              <div>
                <strong>{dish.name}</strong>
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
