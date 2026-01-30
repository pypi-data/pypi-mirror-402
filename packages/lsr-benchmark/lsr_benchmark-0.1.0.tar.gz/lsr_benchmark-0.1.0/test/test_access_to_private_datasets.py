import unittest


def load_ds(ds_id):
    from lsr_benchmark import register_to_ir_datasets
    import ir_datasets

    register_to_ir_datasets(ds_id)
    return ir_datasets.load(f"lsr-benchmark/{ds_id}")

class TestAccessToPrivateDatasets(unittest.TestCase):
    def test_private_dataset_can_be_loaded(self):
        ds = load_ds("clueweb09/en/trec-web-2009")
        self.assertIsNotNone(ds)

    def test_private_dataset_fails_to_access_documents(self):
        ds = load_ds("clueweb09/en/trec-web-2009")
        with self.assertRaises(ValueError, msg='The dataset trec-18-web-20251008-test is private, you can not access the raw data.'):
            list(ds.docs_iter())

    def test_public_dataset_can_access_documents(self):
        ds = load_ds("msmarco-passage/trec-dl-2019/judged")
        self.assertEqual(32123, len(list(ds.docs_iter())))
    
    def test_public_dataset_can_access_qrels(self):
        ds = load_ds("msmarco-passage/trec-dl-2019/judged")
        self.assertEqual(9260, len(list(ds.qrels_iter())))

    def test_qrels_can_be_accessed_on_private_dataset(self):
        ds = load_ds("clueweb09/en/trec-web-2009")
        self.assertEqual(23601, len(list(ds.qrels_iter())))