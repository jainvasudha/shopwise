import axios from "axios";
import type { SearchResponse } from "./types";

// Detect if running on Daytona (check for Daytona environment variables or hostname)
// Daytona forwards ports, so we need to use the forwarded URL
const getApiBaseUrl = (): string => {
  // Check if we're in a Daytona environment
  // Daytona typically sets DAYTONA_WS_ID or similar env vars
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    // If hostname contains "daytona", use the same protocol/host but port 8000
    if (hostname.includes("daytona") || hostname.includes("app.daytona.io")) {
      // Extract workspace ID from hostname (format: <workspace-id>-<port>.app.daytona.io)
      // For API, we need port 8000, so construct: https://<workspace-id>-8000.app.daytona.io
      const parts = hostname.split(".");
      if (parts.length > 0) {
        const firstPart = parts[0]; // e.g., "workspace-id-3000"
        const baseId = firstPart.split("-").slice(0, -1).join("-"); // Remove port part
        const protocol = window.location.protocol;
        return `${protocol}//${baseId}-8000.app.daytona.io`;
      }
    }
  }
  // Default to localhost for local development
  return import.meta.env.VITE_API_URL || "http://localhost:8000";
};

const API_BASE_URL = getApiBaseUrl();

export async function searchProducts(query: string, limit: number): Promise<SearchResponse> {
  const response = await axios.post<SearchResponse>(`${API_BASE_URL}/api/search`, {
    query,
    limit,
  });
  return response.data;
}


