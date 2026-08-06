import { tokenStorage } from "./tokenStorage";
import { triggerUpsell } from "../components/UpsellModal";

const API_URL = import.meta.env.VITE_API_URL || "";

interface RequestInterceptor {
  onFulfilled: (config: RequestInit) => RequestInit | Promise<RequestInit>;
}

interface ResponseInterceptor {
  onFulfilled: (response: Response) => Response | Promise<Response>;
  onRejected: (error: Error) => Error | Promise<Error>;
}

class ApiClient {
  private baseURL: string;
  private interceptors = {
    request: new Map<number, RequestInterceptor>(),
    response: new Map<number, ResponseInterceptor>(),
  };
  private requestId = 0;
  private responseId = 0;

  constructor(baseURL: string = API_URL) {
    this.baseURL = baseURL;
  }

  private getToken(): string | null {
    return tokenStorage.getToken();
  }

  addRequestInterceptor(fn: (config: RequestInit) => RequestInit | Promise<RequestInit>): number {
    const id = ++this.requestId;
    this.interceptors.request.set(id, { onFulfilled: fn });
    return id;
  }

  addResponseInterceptor(
    onFulfilled: (response: Response) => Response | Promise<Response>,
    onRejected?: (error: Error) => Error | Promise<Error>
  ): number {
    const id = ++this.responseId;
    this.interceptors.response.set(id, {
      onFulfilled,
      onRejected: onRejected || ((e) => Promise.reject(e)),
    });
    return id;
  }

  removeRequestInterceptor(id: number): void {
    this.interceptors.request.delete(id);
  }

  removeResponseInterceptor(id: number): void {
    this.interceptors.response.delete(id);
  }

  private async runRequestInterceptors(config: RequestInit): Promise<RequestInit> {
    let result = config;
    for (const interceptor of this.interceptors.request.values()) {
      result = await interceptor.onFulfilled(result);
    }
    return result;
  }

  private async runResponseInterceptors(response: Response): Promise<Response> {
    let result = response;
    for (const interceptor of this.interceptors.response.values()) {
      result = await interceptor.onFulfilled(result);
    }
    return result;
  }

  private async runErrorInterceptors(error: Error): Promise<Error> {
    let result = error;
    for (const interceptor of this.interceptors.response.values()) {
      try {
        result = await interceptor.onRejected(result);
      } catch {
        // Keep original error
      }
    }
    return result;
  }

  async fetch<T = unknown>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = endpoint.startsWith("http") ? endpoint : `${this.baseURL}${endpoint}`;
    const token = this.getToken();

    // Build request config
    let config: RequestInit = {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    };

    // Run request interceptors
    config = await this.runRequestInterceptors(config);

    try {
      const response = await fetch(url, config);
      
      // Handle 401 - Unauthorized (try refresh token first)
      if (response.status === 401) {
        const refreshToken = tokenStorage.getRefreshToken();
        if (refreshToken && !url.includes("/auth/refresh-token")) {
          try {
            const refreshRes = await fetch(`${this.baseURL}/auth/refresh-token`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ refresh_token: refreshToken }),
            });
            if (refreshRes.ok) {
              const data = await refreshRes.json();
              tokenStorage.setToken(data.access_token);
              if (data.refresh_token) tokenStorage.setRefreshToken(data.refresh_token);
              // Retry original request with new token
              const retryConfig = {
                ...config,
                headers: {
                  ...config.headers,
                  Authorization: `Bearer ${data.access_token}`,
                },
              };
              const retryResponse = await fetch(url, retryConfig);
              if (!retryResponse.ok) {
                const errorData = await retryResponse.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${retryResponse.status}`);
              }
              const retryText = await retryResponse.text();
              return retryText ? (JSON.parse(retryText) as T) : (null as T);
            }
          } catch {
            // Refresh failed — fall through to logout
          }
        }
        tokenStorage.clearAll();
        window.location.href = "/login";
        throw new Error("Session expired. Please login again.");
      }

      // Run response interceptors
      const processedResponse = await this.runResponseInterceptors(response);

      if (!processedResponse.ok) {
        const errorData = await processedResponse.json().catch(() => ({}));
        
        // Handle 402 Payment Required — ABAC upsell
        if (processedResponse.status === 402) {
          const detail = errorData.detail || "Contenu premium requis";
          // Extract pack name from message if present
          const packMatch = detail.match(/Pack\s+(\w+)/i);
          const requiredPack = packMatch ? packMatch[1] : "Silver";
          triggerUpsell(detail, requiredPack);
          throw new Error(detail);
        }
        
        if (processedResponse.status === 429) {
          throw new Error("Trop de requêtes. Veuillez patienter avant de réessayer.");
        }
        if (processedResponse.status === 404) {
          throw new Error("Ressource introuvable.");
        }
        if (processedResponse.status >= 500) {
          throw new Error("Erreur serveur. Veuillez réessayer plus tard.");
        }
        throw new Error(errorData.detail || `HTTP ${processedResponse.status}`);
      }

      // Handle empty responses
      const text = await processedResponse.text();
      return text ? (JSON.parse(text) as T) : (null as T);
    } catch (error) {
      throw await this.runErrorInterceptors(error as Error);
    }
  }

  // Convenience methods
  get<T = unknown>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.fetch<T>(endpoint, { ...options, method: "GET" });
  }

  post<T = unknown>(endpoint: string, data?: unknown, options?: RequestInit): Promise<T> {
    return this.fetch<T>(endpoint, {
      ...options,
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  put<T = unknown>(endpoint: string, data?: unknown, options?: RequestInit): Promise<T> {
    return this.fetch<T>(endpoint, {
      ...options,
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  patch<T = unknown>(endpoint: string, data?: unknown, options?: RequestInit): Promise<T> {
    return this.fetch<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  delete<T = unknown>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.fetch<T>(endpoint, { ...options, method: "DELETE" });
  }
}

// Export singleton instance
export const api = new ApiClient();

// Add global response interceptor for logging
api.addResponseInterceptor(async (response) => {
  return response;
});

// Add error handling interceptor
api.addResponseInterceptor(
  (response) => response,
  async (error) => {
    console.error("API Error:", error.message);
    return Promise.reject(error);
  }
);

export default api;