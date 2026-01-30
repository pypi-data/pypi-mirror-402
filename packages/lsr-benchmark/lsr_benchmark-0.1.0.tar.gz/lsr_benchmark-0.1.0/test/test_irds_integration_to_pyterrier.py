import unittest
from pathlib import Path
from lsr_benchmark import register_to_ir_datasets


def load_dataset_with_pyterrier(irds_id):
        import pyterrier as pt
        return pt.get_dataset(f"irds:{irds_id}")


class TestIrdsIntegrationToPyTerrier(unittest.TestCase):
    def test_that_original_dataset_can_be_loaded(self):
        dataset = load_dataset_with_pyterrier("clueweb09/en/trec-web-2009")
        self.assertIsNotNone(dataset)


    def test_from_local_directory(self):
        resource_dir = str(Path(__file__).parent / "resources" / "example-dataset")
        register_to_ir_datasets(resource_dir)
        ds = load_dataset_with_pyterrier("lsr-benchmark/" + resource_dir)

        self.assertEqual(3, len(ds.get_topics()))
        self.assertEqual(4, len(list(ds.get_corpus_iter())))

    def test_ms_marco_dataset(self):
        register_to_ir_datasets("msmarco-passage/trec-dl-2019/judged")
        ds = load_dataset_with_pyterrier("lsr-benchmark/msmarco-passage/trec-dl-2019/judged")

        self.assertEqual(43, len(ds.get_topics()))
        self.assertEqual(32123, len(list(ds.get_corpus_iter())))
        self.assertEqual(9260, len(ds.get_qrels()))