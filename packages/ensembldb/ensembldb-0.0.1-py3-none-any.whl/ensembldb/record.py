from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


@dataclass(frozen=True)
class EnsDbRecord:
    """Container for a single EnsDb entry."""

    ensdb_id: str  # e.g., "AH12345"
    title: str
    species: Optional[str]
    taxonomy_id: Optional[str]
    genome: Optional[str]
    description: Optional[str]
    url: str
    release_date: Optional[date]
    ensembl_version: Optional[str] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> "EnsDbRecord":
        """Build a record from a database query row."""
        rid, title, species, tax_id, genome, desc, url, date_str = row

        ah_id = f"AH{rid}"

        rel_date: Optional[date] = None
        if date_str:
            try:
                rel_date = datetime.strptime(str(date_str).split(" ")[0], "%Y-%m-%d").date()
            except ValueError:
                pass

        ens_ver = None
        if title and "Ensembl" in title:
            parts = title.split(" ")
            for i, p in enumerate(parts):
                if p == "Ensembl" and i + 1 < len(parts):
                    candidate = parts[i + 1]
                    if candidate.isdigit():
                        ens_ver = candidate
                        break

        return cls(
            ensdb_id=ah_id,
            title=title or "",
            species=species,
            taxonomy_id=str(tax_id) if tax_id else None,
            genome=genome,
            description=desc,
            url=url,
            release_date=rel_date,
            ensembl_version=ens_ver,
        )
