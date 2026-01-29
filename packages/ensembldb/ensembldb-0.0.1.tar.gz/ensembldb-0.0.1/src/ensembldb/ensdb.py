import sqlite3
from typing import Dict, List, Optional, Union

from biocframe import BiocFrame
from genomicranges import GenomicRanges
from iranges import IRanges

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


class EnsDb:
    """Interface to Ensembl SQLite annotations."""

    def __init__(self, dbpath: str):
        """Initialize the EnsDb object.

        Args:
            dbpath:
                Path to the SQLite database file.
        """
        self.dbpath = dbpath
        self.conn = sqlite3.connect(dbpath)
        self.conn.row_factory = sqlite3.Row
        self._metadata = None

    def _query_as_biocframe(self, query: str, params: tuple = ()) -> BiocFrame:
        """Execute query and return BiocFrame."""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()

        if not results:
            if cursor.description:
                col_names = [desc[0] for desc in cursor.description]
                # Fix: Initialize empty lists for each column to satisfy BiocFrame validation
                empty_data = {col: [] for col in col_names}
                return BiocFrame(empty_data, column_names=col_names)
            return BiocFrame({})

        col_names = [desc[0] for desc in cursor.description]
        columns_data = list(zip(*results))

        data_dict = {}
        for i, name in enumerate(col_names):
            data_dict[name] = list(columns_data[i])

        return BiocFrame(data_dict)

    @property
    def metadata(self) -> BiocFrame:
        """Get database metadata."""
        if self._metadata is None:
            self._metadata = self._query_as_biocframe("SELECT * FROM metadata")
        return self._metadata

    def _check_column_exists(self, table: str, column: str) -> bool:
        """Check if a column exists in a table."""
        try:
            self.conn.execute(f"SELECT {column} FROM {table} LIMIT 1")
            return True
        except sqlite3.OperationalError:
            return False

    def genes(self, filter: Optional[Dict[str, Union[str, List[str]]]] = None) -> GenomicRanges:
        """Retrieve genes as GenomicRanges.

        Args:
            filter:
                A dictionary defining filters to narrow down the result.
                Keys are column names (e.g., "gene_id", "gene_name", "gene_biotype").
                Values can be a single string or a list of strings to match.

                Example:
                    `{'gene_name': 'BRCA1'}`
                    `{'gene_biotype': ['protein_coding', 'lincRNA']}`

        Returns:
            A GenomicRanges object containing gene coordinates and metadata.
        """
        has_entrez = self._check_column_exists("gene", "entrezid")
        entrez_col = ", g.entrezid" if has_entrez else ""

        query = f"""
        SELECT 
            g.gene_id, g.gene_name, g.gene_biotype,
            g.seq_name, g.gene_seq_start, g.gene_seq_end, g.seq_strand{entrez_col},
            c.seq_length
        FROM gene g
        LEFT JOIN chromosome c ON g.seq_name = c.seq_name
        """

        where_clauses = []
        params = []

        if filter:
            for col, val in filter.items():
                if isinstance(val, list):
                    placeholders = ",".join("?" * len(val))
                    where_clauses.append(f"g.{col} IN ({placeholders})")
                    params.extend(val)
                else:
                    where_clauses.append(f"g.{col} = ?")
                    params.append(val)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        bf = self._query_as_biocframe(query, tuple(params))

        if bf.shape[0] == 0:
            return GenomicRanges.empty()

        return self._make_gr(bf, prefix="gene_")

    def transcripts(self, filter: Optional[Dict[str, Union[str, List[str]]]] = None) -> GenomicRanges:
        """Retrieve transcripts as GenomicRanges.

        Args:
            filter:
                A dictionary defining filters to narrow down the result.
                Keys are column names (e.g., "tx_id", "gene_id", "tx_biotype").
                Values can be a single string or a list of strings to match.

                Columns from the gene table (like "gene_name") can also be used as keys
                since the query performs a join.

        Returns:
            A GenomicRanges object containing transcript coordinates and metadata.
        """
        query = """
        SELECT 
            t.tx_id, t.tx_biotype, t.gene_id,
            t.tx_seq_start, t.tx_seq_end,
            g.seq_name, g.seq_strand, g.gene_name,
            c.seq_length
        FROM tx t
        JOIN gene g ON t.gene_id = g.gene_id
        LEFT JOIN chromosome c ON g.seq_name = c.seq_name
        """

        where_clauses = []
        params = []

        if filter:
            for col, val in filter.items():
                prefix = "t." if col.startswith("tx_") else "g."
                if col == "gene_id":
                    prefix = "t."

                if isinstance(val, list):
                    placeholders = ",".join("?" * len(val))
                    where_clauses.append(f"{prefix}{col} IN ({placeholders})")
                    params.extend(val)
                else:
                    where_clauses.append(f"{prefix}{col} = ?")
                    params.append(val)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        bf = self._query_as_biocframe(query, tuple(params))
        if bf.shape[0] == 0:
            return GenomicRanges.empty()

        return self._make_gr(bf, prefix="tx_")

    def exons(self, filter: Optional[Dict[str, Union[str, List[str]]]] = None) -> GenomicRanges:
        """Retrieve exons as GenomicRanges.

        Args:
            filter:
                A dictionary defining filters to narrow down the result.
                Keys are column names (e.g., "exon_id", "gene_id", "tx_id").
                Values can be a single string or a list of strings to match.

                This allows filtering exons by associated gene or transcript IDs
                (e.g., `{'gene_id': 'ENSG00000139618'}`).

        Returns:
            A GenomicRanges object containing exon coordinates and metadata.
        """
        query = """
        SELECT DISTINCT
            e.exon_id, e.exon_seq_start, e.exon_seq_end,
            g.seq_name, g.seq_strand,
            c.seq_length
        FROM exon e
        JOIN tx2exon t2e ON e.exon_id = t2e.exon_id
        JOIN tx t ON t2e.tx_id = t.tx_id
        JOIN gene g ON t.gene_id = g.gene_id
        LEFT JOIN chromosome c ON g.seq_name = c.seq_name
        """

        where_clauses = []
        params = []
        if filter:
            for col, val in filter.items():
                prefix = "g."
                if col.startswith("tx_"):
                    prefix = "t."
                if col.startswith("exon_"):
                    prefix = "e."

                if isinstance(val, list):
                    placeholders = ",".join("?" * len(val))
                    where_clauses.append(f"{prefix}{col} IN ({placeholders})")
                    params.extend(val)
                else:
                    where_clauses.append(f"{prefix}{col} = ?")
                    params.append(val)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        bf = self._query_as_biocframe(query, tuple(params))
        if bf.shape[0] == 0:
            return GenomicRanges.empty()

        return self._make_gr(bf, prefix="exon_")

    def _make_gr(self, bf: BiocFrame, prefix: str = "gene_") -> GenomicRanges:
        """Helper to convert BiocFrame to GenomicRanges."""
        strand_col = bf.get_column("seq_strand")
        strand_map = {1: "+", -1: "-", 0: "*", "1": "+", "-1": "-", "0": "*"}
        strand = [strand_map.get(x, "*") for x in strand_col]

        seqnames = [str(x) for x in bf.get_column("seq_name")]

        starts = bf.get_column(f"{prefix}seq_start")
        ends = bf.get_column(f"{prefix}seq_end")
        widths = [abs(e - s) + 1 for s, e in zip(starts, ends)]
        ranges = IRanges(start=starts, width=widths)

        row_names = None
        id_col = f"{prefix}id"
        if id_col in bf.column_names:
            row_names = [str(x) for x in bf.get_column(id_col)]

        drop_cols = ["seq_name", "seq_strand", f"{prefix}seq_start", f"{prefix}seq_end", "seq_length"]
        mcols_dict = {}
        for c in bf.column_names:
            if c not in drop_cols:
                mcols_dict[c] = bf.get_column(c)

        mcols = BiocFrame(mcols_dict, row_names=row_names)

        return GenomicRanges(seqnames=seqnames, ranges=ranges, strand=strand, names=row_names, mcols=mcols)

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
