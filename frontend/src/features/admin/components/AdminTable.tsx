import { ReactNode, useState } from "react";
import { Loader2, ChevronUp, ChevronDown } from "lucide-react";
import { PaginationControls } from "./PaginationControls";

export interface Column<T> {
  key: string;
  header: string | ReactNode;
  render?: (row: T) => ReactNode;
  width?: string;
  sortable?: boolean;
}

export interface AdminTableProps<T> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  emptyMessage?: string;
  rowKey?: keyof T;
  onRowClick?: (row: T) => void;
  pagination?: { page: number; per_page: number; total: number; onPageChange: (page: number) => void };
  onSort?: (key: string, order: "asc" | "desc") => void;
  sortKey?: string;
  sortOrder?: "asc" | "desc";
}

export function AdminTable<T extends { id: number | string }>({
  columns,
  data,
  loading,
  emptyMessage = "Aucune donnee",
  rowKey = "id" as keyof T,
  onRowClick,
  pagination,
}: AdminTableProps<T>) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-cream-m">
            <tr>
              {columns.map((col) => (
                <th key={col.key} className="text-start px-5 py-4 text-xs font-semibold text-gray uppercase tracking-wider whitespace-nowrap"
                  style={{ width: col.width }}>
                  {typeof col.header === "string" ? col.header : col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-black/5">
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i}>
                  {columns.map((col) => (
                    <td key={col.key} className="px-5 py-5">
                      <div className="h-5 bg-gray-100 rounded animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="text-center py-20">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-cream-m flex items-center justify-center">
                      <svg className="w-6 h-6 text-gray" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                      </svg>
                    </div>
                    <p className="text-gray text-sm font-medium">{emptyMessage}</p>
                  </div>
                </td>
              </tr>
            ) : (
              data.map((row) => (
                <tr key={String(row[rowKey])}
                  className={`hover:bg-cream/40 transition-colors ${onRowClick ? "cursor-pointer" : ""}`}
                  onClick={() => onRowClick?.(row)}>
                  {columns.map((col) => (
                    <td key={col.key} className="px-5 py-4 text-sm">
                      {col.render ? col.render(row) : String((row as Record<string, unknown>)[col.key] ?? "")}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {pagination && (
        <PaginationControls
          page={pagination.page}
          limit={pagination.per_page}
          total={pagination.total}
          onPageChange={pagination.onPageChange}
        />
      )}
    </div>
  );
}