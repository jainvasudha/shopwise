export interface Carbon {
  kg_co2e: number;
  label: string;
}

export interface ProductResult {
  store: string;
  name: string;
  price: number;
  link: string;
  ethical_score: number;
  carbon: Carbon;
}

export interface SearchResponse {
  query: string;
  results: ProductResult[];
  summary: string;
}



