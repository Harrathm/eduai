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
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="px-3 py-1.5 text-sm rounded-lg hover:bg-cream disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Prec.
        </button>
        {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
          const p = i + 1;
          return (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              className={`w-8 h-8 text-sm rounded-lg ${p === page ? "bg-orange text-white" : "hover:bg-cream"}`}
            >
              {p}
            </button>
          );
        })}
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="px-3 py-1.5 text-sm rounded-lg hover:bg-cream disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Suiv.
        </button>
      </div>
    </div>
  );
}