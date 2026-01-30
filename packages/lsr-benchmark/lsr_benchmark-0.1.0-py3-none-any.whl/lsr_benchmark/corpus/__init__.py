from tqdm import tqdm
import ir_datasets
from .corpus_subsampling import create_subsample
from .segmentation import segmented_document
import gzip
import json


def load_docs(ir_datasets_id, subsample):
    ret = {}
    docs_store = ir_datasets.load(ir_datasets_id).docs_store()

    skipped = 0
    for doc in tqdm(subsample):
        try:
            ret[doc] = docs_store.get(doc).default_text()[:2000000]
        except Exception:
            skipped += 1
    print(f"Skipped {skipped} docs")
    return ret

def incorporate_fields(docs, ir_datasets_id, fields):
    if fields is None or len(fields) == 0:
        return

    ret = {}
    docs_store = ir_datasets.load(ir_datasets_id).docs_store()

    skipped = 0
    for doc_id in tqdm(docs.keys(), "add fields"):
        try:
            doc = docs_store.get(doc_id)
            ret[doc_id] = {k: getattr(doc, k) for k in fields}
        except Exception:
            skipped += 1
    for doc_id in docs.keys():
        for f in fields:
            docs[doc_id][f] = ret.get(doc_id, {}).get(f)


def irds_id_from_config(config):
    if "ir-datasets-id" not in config:
        from lsr_benchmark.chatnoir import register_subsample_from_chatnoir
        ir_datasets_id = "chatnoir/" + config["chatnoir-index"]
        register_subsample_from_chatnoir(config["chatnoir-index"], config["qrels"], config["topics"], ir_datasets_id)
        return ir_datasets_id

    ir_datasets_id = config["ir-datasets-id"]
    if ir_datasets_id.startswith("clueweb"):
        from ir_datasets_subsample import register_subsamples
        register_subsamples()
        ir_datasets_id = "corpus-subsamples/" + ir_datasets_id
    return ir_datasets_id

def materialize_raw_corpus(directory, subsample, config):
    ir_datasets_id = irds_id_from_config(config)
    docs = load_docs(ir_datasets_id, subsample)
    with gzip.open(directory / "corpus.jsonl.gz", 'wt') as f:
        for doc in docs.values():
            f.write(json.dumps(doc) + '\n')

def materialize_corpus(directory, config):
    ir_datasets_id = irds_id_from_config(config)
    if (directory/"corpus.jsonl.gz").is_file():
        return

    subsample = create_subsample(config["runs"], ir_datasets_id, config["subsample_depth"], directory)
    docs = load_docs(ir_datasets_id, subsample)
    docs = segmented_document(docs, config.get("passage_size", 200))
    incorporate_fields(docs, ir_datasets_id, config.get("include-fields"))
    with gzip.open(directory/"corpus.jsonl.gz", 'wt') as f:
        for doc in docs.values():
            f.write(json.dumps(doc) + '\n')

def materialize_queries(directory, config):
    from tira.ir_datasets_loader import IrDatasetsLoader
    
    irds_loader = IrDatasetsLoader()
    ir_datasets_id = irds_id_from_config(config)
    output_jsonl = directory / "queries.jsonl"
    output_xml = directory / "queries.xml"

    allowed_queries = set()
    for i in ir_datasets.load(ir_datasets_id).qrels_iter():
        allowed_queries.add(i.query_id)

    if not output_jsonl.exists():
        dataset = ir_datasets.load(ir_datasets_id)
        queries_mapped_jsonl = [irds_loader.map_query_as_jsonl(query, True) for query in dataset.queries_iter() if query.query_id in allowed_queries]
        with open(output_jsonl, 'w') as f:
            for query_json in queries_mapped_jsonl:
                f.write(query_json + '\n')

    if not output_xml.exists():
        dataset = ir_datasets.load(ir_datasets_id)
        queries_mapped_xml = [irds_loader.map_query_as_xml(query, True) for query in dataset.queries_iter() if query.query_id in allowed_queries]
        with open(output_xml, 'w') as f:
            for query_xml in queries_mapped_xml:
                f.write(str(query_xml) + '\n')

def materialize_qrels(output_qrels, config):
    ir_datasets_id = irds_id_from_config(config)

    if output_qrels.exists():
        return

    dataset = ir_datasets.load(ir_datasets_id)

    with open(output_qrels, 'w') as f:
        for qrel in dataset.qrels_iter():
            f.write(f"{qrel.query_id} 0 {qrel.doc_id} {qrel.relevance}\n")
