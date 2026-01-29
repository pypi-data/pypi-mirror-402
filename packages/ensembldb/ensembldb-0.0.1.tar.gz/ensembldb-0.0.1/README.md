[![PyPI-Server](https://img.shields.io/pypi/v/ensembldb.svg)](https://pypi.org/project/ensembldb/)
![Unit tests](https://github.com/BiocPy/ensembldb/actions/workflows/run-tests.yml/badge.svg)

# EnsemblDb

**EnsemblDb** provides a Python interface to **Ensembl Annotation Databases (EnsDb)**. It mirrors the functionality of the Bioconductor `ensembldb` package, allowing users to efficiently query gene, transcript, and exon annotations from SQLite-based annotation files.

This package is part of the **BiocPy** ecosystem and integrates seamlessly with [GenomicRanges](https://github.com/biocpy/genomicranges).

## Install

To get started, install the package from [PyPI](https://pypi.org/project/ensembldb/)

```bash
pip install ensembldb
```

## Usage

### 1. Connecting to an EnsDb

You can manage and download standard Ensembl databases via the registry (backed by AnnotationHub).

```py
from ensembldb import EnsDbRegistry

# Initialize the registry
registry = EnsDbRegistry()

# List available databases
available = registry.list_ensdbs()
print(available[:5])
# ['AH53211', 'AH53212', ...]

# Load a specific database (e.g., Larimichthys crocea)
# This automatically downloads and caches the SQLite file
db = registry.load_db("AH113677")

# View metadata
print(db.metadata)
```

### 2. Retrieving Genomic Features

EnsemblDb allows you to extract features as GenomicRanges objects.

#### Fetch Genes

```py
genes = db.genes()
print(genes)
# GenomicRanges with 23958 ranges and 3 metadata columns
#                    seqnames              ranges          strand              gene_id gene_name   gene_biotype
#                       <str>           <IRanges> <ndarray[int8]>               <list>    <list>         <list>
# ENSLCRG00005000002       MT              1 - 69               + | ENSLCRG00005000002                  Mt_tRNA
# ENSLCRG00005000003       MT           70 - 1016               + | ENSLCRG00005000003                  Mt_rRNA
# ENSLCRG00005000004       MT         1017 - 1087               + | ENSLCRG00005000004                  Mt_tRNA
#                         ...                 ...             ... |                ...       ...            ...
# ENSLCRG00005023957       VI 22289079 - 22304889               - | ENSLCRG00005023957    FILIP1 protein_coding
# ENSLCRG00005023958       VI 22328118 - 22347657               + | ENSLCRG00005023958     SENP6 protein_coding
# ENSLCRG00005023959       VI 22351962 - 22451867               + | ENSLCRG00005023959     myo6a protein_coding
# ------
# seqinfo(496 sequences): I II III ... XXII XXIII XXIV
```

#### Fetch Transcripts and Exons

```py
transcripts = db.transcripts()
print(transcripts)

exons = db.exons()
print(exons)
```

### 3. Filtering

You can filter results using a dictionary passed to the filter argument. Keys should match column names in the database (e.g., gene_id, gene_name, tx_biotype).

#### Filter by Gene Name

```py
# Get coordinates for a specific gene
senp6 = db.genes(filter={"gene_name": "SENP6"})
print(senp6)
```

#### Filter by ID list

```py
# Get transcripts for a list of gene IDs
ids = ["ENSLCRG00005023958", "ENSLCRG00005000003"]
txs = db.transcripts(filter={"gene_id": ids})
print(txs)
```

#### Filter Exons by Transcript ID:

```py
# Get all exons associated with a specific transcript
tx_exons = db.exons(filter={"tx_id": "ENSLCRT00005000003"})
print(tx_exons)
```

### 4. Direct SQL Access

If you need more complex queries not covered by the standard methods, you can execute SQL directly against the underlying database.

```py
# Get a BiocFrame from a raw SQL query
df = db._query_as_biocframe("SELECT * FROM gene LIMIT 5")
print(df)
```

<!-- biocsetup-notes -->

## Note

This project has been set up using [BiocSetup](https://github.com/biocpy/biocsetup)
and [PyScaffold](https://pyscaffold.org/).
