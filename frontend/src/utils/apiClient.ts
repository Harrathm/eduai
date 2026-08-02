const API_URL = "";

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
    return localStorage.getItem("token");
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
      
      // Handle 401 - Unauthorized
      if (response.status === 401) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        window.location.href = "/login";
        throw new Error("Session expired. Please login again.");
      }

      // Run response interceptors
      const processedResponse = await this.runResponseInterceptors(response);

      if (!processedResponse.ok) {
        const errorData = await processedResponse.json().catch(() => ({}));
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
  const requestId = response.headers.get("X-Request-ID");
  const processTime = response.headers.get("X-Process-Time");
  console.log(`API Response [${response.status}]: ${response.url} (${processTime})`);
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