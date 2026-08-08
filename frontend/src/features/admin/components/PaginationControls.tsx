import { Button } from "@/components/ui";

interface PaginationControlsProps {
  page: number;
  limit: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function PaginationControls({ page, limit, total, onPageChange }: PaginationControlsProps) {
  const totalPages = Math.ceil(total / limit);
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between px-6 py-4 border-t border-black/5">
      <p className="text-sm text-gray">
        {((page - 1) * limit) + 1}-{Math.min(page * limit, total)} sur {total}
      </p>
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
        >
          Prec.
        </Button>
        {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
          const p = i + 1;
          return (
            <Button variant="ghost" size="sm"
              key={p}
              onClick={() => onPageChange(p)}
            >
              {p}
            </Button>
          );
        })}
        <Button variant="ghost" size="sm"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
        >
          Suiv.
        </Button>
      </div>
    </div>
  );
}