/**
 * Shared API types
 */

export interface PaginatedResponse<T> {
  total: number;
  items: T[];
  skip?: number;
  limit?: number;
}

export interface ApiError extends Error {
  status: number;
  detail?: string;
}
