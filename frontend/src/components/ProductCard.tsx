import type { ProductResult } from "../types";

interface Props {
  product: ProductResult;
}

export function ProductCard({ product }: Props) {
  const badgeColor =
    product.carbon.label === "Low impact"
      ? "badge-low"
      : product.carbon.label === "Moderate impact"
        ? "badge-medium"
        : "badge-high";

  return (
    <div className="card">
      <div className="card-main">
        <div>
          <h3>{product.name}</h3>
          <p className="muted">Store: {product.store}</p>
          <p className="price">${product.price.toFixed(2)}</p>
          <span className={`badge ${badgeColor}`}>
            {product.carbon.label} (~{product.carbon.kg_co2e} kg CO₂e)
          </span>
        </div>
        <div>
          <a className="button primary" href={product.link} target="_blank" rel="noreferrer">
            Buy Now
          </a>
        </div>
      </div>
    </div>
  );
}



