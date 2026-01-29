import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pybiocfilecache import BiocFileCache

from ._ahub import AHUB_METADATA_URL
from .ensdb import EnsDb
from .record import EnsDbRecord

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


class EnsDbRegistry:
    """Registry for EnsDb resources."""

    def __init__(
        self,
        cache_dir: Optional[Union[str, Path]] = None,
        force: bool = False,
    ) -> None:
        """Initialize the EnsDb registry.

        Args:
            cache_dir: Path to cache directory.
            force: Force re-download of metadata.
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "ensembldb_bfc"

        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._bfc = BiocFileCache(self._cache_dir)

        self._registry_map: Dict[str, EnsDbRecord] = {}
        self._initialize_registry(force=force)

    def _initialize_registry(self, force: bool = False):
        """Populate registry from AnnotationHub metadata."""
        rname = "annotationhub_metadata"

        existing = None
        try:
            existing = self._bfc.get(rname)
        except Exception:
            pass

        if force and existing:
            try:
                self._bfc.remove(rname)
            except Exception:
                pass
            existing = None

        if existing:
            md_resource = existing
        else:
            md_resource = self._bfc.add(rname, AHUB_METADATA_URL, rtype="web")

        md_path = self._get_filepath(md_resource)

        if not md_path or not os.path.exists(md_path):
            if existing and not force:
                return self._initialize_registry(force=True)
            raise RuntimeError("Failed to retrieve AnnotationHub metadata.")

        conn = sqlite3.connect(md_path)
        try:
            # Filter for EnsDb sqlite files
            # Updated query: Checks rdataclass AND rdatapath extension
            query = """
            SELECT
                r.id,
                r.title,
                r.species,
                r.taxonomyid,
                r.genome,
                r.description,
                lp.location_prefix || rp.rdatapath AS full_url,
                r.rdatadateadded
            FROM resources r
            LEFT JOIN location_prefixes lp
                ON r.location_prefix_id = lp.id
            LEFT JOIN rdatapaths rp
                ON rp.resource_id = r.id
            WHERE (rp.rdataclass = 'EnsDb' OR r.title LIKE 'Ensembl % EnsDb%')
              AND rp.rdatapath LIKE '%.sqlite'
            ORDER BY r.rdatadateadded DESC;
            """
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
        finally:
            conn.close()

        for row in rows:
            record = EnsDbRecord.from_db_row(row)
            self._registry_map[record.ensdb_id] = record

    def list_ensdbs(self) -> List[str]:
        """List available EnsDb IDs."""
        return sorted(list(self._registry_map.keys()))

    def get_record(self, ensdb_id: str) -> EnsDbRecord:
        if ensdb_id not in self._registry_map:
            raise KeyError(f"ID '{ensdb_id}' not found.")
        return self._registry_map[ensdb_id]

    def download(self, ensdb_id: str, force: bool = False) -> str:
        record = self.get_record(ensdb_id)
        url = record.url
        key = ensdb_id

        if force:
            try:
                self._bfc.remove(key)
            except Exception:
                pass

        if not force:
            try:
                existing = self._bfc.get(key)
                if existing:
                    path = self._get_filepath(existing)
                    if path and os.path.exists(path) and os.path.getsize(path) > 0:
                        return path
            except Exception:
                pass

        resource = self._bfc.add(
            key,
            url,
            rtype="web",
            download=True,
        )

        path = self._get_filepath(resource)
        if not path or not os.path.exists(path) or os.path.getsize(path) == 0:
            try:
                self._bfc.remove(key)
            except Exception:
                pass
            raise RuntimeError(f"Download failed for {ensdb_id}.")

        return path

    def load_db(self, ensdb_id: str, force: bool = False) -> EnsDb:
        path = self.download(ensdb_id, force=force)
        return EnsDb(path)

    def _get_filepath(self, resource: Any) -> Optional[str]:
        if hasattr(resource, "rpath"):
            rel_path = str(resource.rpath)
        elif hasattr(resource, "get"):
            rel_path = str(resource.get("rpath"))
        else:
            return None
        return str(self._cache_dir / rel_path)
