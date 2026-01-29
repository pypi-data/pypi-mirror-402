import pytest
from genomicranges import GenomicRanges

from ensembldb import EnsDb, EnsDbRegistry

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


@pytest.fixture(scope="module")
def ensdb_resource():
    registry = EnsDbRegistry()

    all_ids = registry.list_ensdbs()

    if not all_ids:
        pytest.fail("Registry found no EnsDb files. Check query logic.")

    target_id = "AH100751"  # Saccharomyces cerevisiae
    return registry.load_db(target_id)


def test_connection_and_metadata(ensdb_resource):
    assert isinstance(ensdb_resource, EnsDb)

    meta = ensdb_resource.metadata

    assert "name" in meta.column_names
    assert "value" in meta.column_names

    names = meta.get_column("name")
    values = meta.get_column("value")
    meta_dict = dict(zip(names, values))

    assert "DBSCHEMAVERSION" in meta_dict or "schema_version" in meta_dict


def test_genes_fetch(ensdb_resource):
    gr = ensdb_resource.genes()

    assert isinstance(gr, GenomicRanges)
    assert len(gr) > 0

    mcols = gr.mcols
    assert "gene_id" in mcols.column_names
    assert len(gr.seqnames) == len(gr)
    assert len(gr.ranges) == len(gr)


def test_genes_filter(ensdb_resource):
    all_genes = ensdb_resource.genes()
    if len(all_genes) == 0:
        pytest.skip("No genes found in DB to filter.")

    target_id = all_genes.mcols.get_column("gene_id")[0]
    gr_filtered = ensdb_resource.genes(filter={"gene_id": target_id})
    assert len(gr_filtered) == 1
    assert gr_filtered.mcols.get_column("gene_id")[0] == target_id


def test_transcripts_fetch(ensdb_resource):
    gr = ensdb_resource.transcripts()

    assert isinstance(gr, GenomicRanges)
    if len(gr) == 0:
        print("Warning: No transcripts found.")
        return

    mcols = gr.mcols
    assert "tx_id" in mcols.column_names
    assert "gene_id" in mcols.column_names


def test_exons_fetch(ensdb_resource):
    gr = ensdb_resource.exons()

    assert isinstance(gr, GenomicRanges)
    if len(gr) == 0:
        print("Warning: No exons found.")
        return

    mcols = gr.mcols
    assert "exon_id" in mcols.column_names


def test_combined_filter(ensdb_resource):
    txs = ensdb_resource.transcripts()
    if len(txs) == 0:
        pytest.skip("No transcripts to filter.")

    target_gene = txs.mcols.get_column("gene_id")[0]
    gr = ensdb_resource.transcripts(filter={"gene_id": target_gene})

    assert len(gr) > 0
    for gid in gr.mcols.get_column("gene_id"):
        assert gid == target_gene


def test_seqinfo_population(ensdb_resource):
    gr = ensdb_resource.genes()
    if len(gr) == 0:
        pytest.skip("No genes.")

    assert all(start > 0 for start in gr.ranges.start)
