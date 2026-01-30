import unittest
from pathlib import Path

from lsr_benchmark import register_to_ir_datasets
from lsr_benchmark.datasets import IR_DATASET_TO_TIRA_DATASET
from tempfile import TemporaryDirectory
import ir_datasets
import os

class TestIrdsIntegration(unittest.TestCase):
    def test_fails_for_non_existing_dataset(self):
        with self.assertRaises(Exception):
            register_to_ir_datasets("this-does-not-exist")

    def test_works_for_none_as_dataset(self):
        register_to_ir_datasets()

    def test_from_local_directory(self):
        resource_dir = str(Path(__file__).parent / "resources" / "example-dataset")
        register_to_ir_datasets(resource_dir)
        ds = ir_datasets.load(resource_dir)

        self.assertEqual(3, len(list(ds.queries_iter())))
        self.assertEqual(4, len(list(ds.docs_iter())))


    def test_from_local_directory_with_prefix(self):
        resource_dir = str(Path(__file__).parent / "resources" / "example-dataset")
        register_to_ir_datasets(resource_dir)
        ds = ir_datasets.load("lsr-benchmark/" + resource_dir)

        self.assertEqual(3, len(list(ds.queries_iter())))
        self.assertEqual(4, len(list(ds.docs_iter())))

    def test_ms_marco_dataset(self):
        register_to_ir_datasets("msmarco-passage/trec-dl-2019/judged")
        ds = ir_datasets.load("lsr-benchmark/msmarco-passage/trec-dl-2019/judged")

        self.assertEqual("lsr-benchmark/msmarco-passage/trec-dl-2019/judged", ds.dataset_id())
        self.assertEqual(43, len(list(ds.queries_iter())))
        self.assertEqual(32123, len(list(ds.docs_iter())))
        self.assertEqual(9260, len(list(ds.qrels_iter())))

    def test_private_dataset_error_message(self):
        with TemporaryDirectory() as tmp_dir:
            os.environ["TIRA_CACHE_DIR"] = str(tmp_dir)
            with self.assertRaises(ValueError) as e:
                register_to_ir_datasets("disks45/nocr/trec-robust-2004/fold3")
                ds = ir_datasets.load("lsr-benchmark/disks45/nocr/trec-robust-2004/fold3")
                list(ds.queries_iter())
            del os.environ["TIRA_CACHE_DIR"]
            self.assertIsNotNone(e)

    def test_all_datasets_can_be_loaded(self):
        for i in range(3):
            for ds in IR_DATASET_TO_TIRA_DATASET.keys():
                register_to_ir_datasets(ds)
                self.assertIsNotNone(ir_datasets.load(f"lsr-benchmark/{ds}"))

            for ds in IR_DATASET_TO_TIRA_DATASET.values():
                register_to_ir_datasets(ds)
                self.assertIsNotNone(ir_datasets.load(ds))
