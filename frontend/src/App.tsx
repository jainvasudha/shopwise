import { useState } from "react";
import { searchProducts } from "./api";
import type { ProductResult, SearchResponse } from "./types";
import { ProductCard } from "./components/ProductCard";
import { Summary } from "./components/Summary";

type SortMode = "price" | "carbon";

export default function App() {
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<SearchResponse | null>(null);
  const [sortMode, setSortMode] = useState<SortMode>("price");

  const handleSearch = async (event?: React.FormEvent) => {
    event?.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      setError("Please enter a product name before searching.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const result = await searchProducts(trimmed, limit);
      setData(result);
    } catch (err) {
      console.error(err);
      setError("Something went wrong while contacting the ShopWise API.");
    } finally {
      setLoading(false);
    }
  };

  const sortedResults: ProductResult[] =
    (data?.results ?? []).slice().sort((a, b) => {
      if (sortMode === "carbon") {
        if (a.carbon.kg_co2e === b.carbon.kg_co2e) {
          return a.price - b.price;
        }
        return a.carbon.kg_co2e - b.carbon.kg_co2e;
      }
      if (a.price === b.price) {
        return a.carbon.kg_co2e - b.carbon.kg_co2e;
      }
      return a.price - b.price;
    });

  return (
    <>
      {/* Navigation Bar */}
      <nav className="navbar">
        <div className="navbar-container">
          <a href="/" className="navbar-logo">
            <div className="logo-icon">S</div>
            ShopWise
          </a>
          <div className="navbar-center">
            <ul className="navbar-menu">
              <li><a href="#features">Features</a></li>
              <li><a href="#how-it-works">How It Works</a></li>
              <li><a href="#about">About</a></li>
              <li><a href="#contact">Contact</a></li>
            </ul>
          </div>
          <div className="navbar-actions">
            <button className="button secondary">Log In</button>
            <button className="button accent">Sign Up</button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1>Student-Friendly Sustainable Shopping</h1>
          <p>
            Compare student-budget-friendly options across major retailers and balance affordability with carbon impact.
          </p>

          {/* Search Bar */}
          <div className="search-container">
            <label className="search-label">What are you shopping for?</label>
            <form onSubmit={handleSearch}>
              <div className="search-bar">
                <div className="search-input-wrapper">
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g. wireless headphones, eco backpack, graphing calculator"
                  />
                </div>
                <div className="select-wrapper">
                  <select
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                  >
                    <option value={1}>1 per store</option>
                    <option value={2}>2 per store</option>
                    <option value={3}>3 per store</option>
                    <option value={4}>4 per store</option>
                    <option value={5}>5 per store</option>
                  </select>
                </div>
                <button type="submit" className="button primary" disabled={loading}>
                  {loading ? "Searching..." : "Search"}
                </button>
              </div>
            </form>

            {error && <div className="alert alert-warning">{error}</div>}
          </div>
        </div>
      </section>

      {/* Main Content */}
      <main className="page">
        {data && data.results.length > 0 && (
          <>
            <section className="controls">
              <span>Sort results by:</span>
              <div className="segmented">
                <button
                  type="button"
                  className={sortMode === "price" ? "active" : ""}
                  onClick={() => setSortMode("price")}
                >
                  Lowest Price
                </button>
                <button
                  type="button"
                  className={sortMode === "carbon" ? "active" : ""}
                  onClick={() => setSortMode("carbon")}
                >
                  Lowest Carbon Footprint
                </button>
              </div>
            </section>

            <section className="results">
              <h2>Top Student-Friendly Picks</h2>
              {sortedResults.map((product) => (
                <ProductCard key={`${product.store}-${product.link}`} product={product} />
              ))}
            </section>

            <Summary summary={data.summary} />
          </>
        )}

        {!data && (
          <section className="empty-state">
            <p>Search for something like "wireless headphones" to get started.</p>
          </section>
        )}
      </main>
    </>
  );
}
