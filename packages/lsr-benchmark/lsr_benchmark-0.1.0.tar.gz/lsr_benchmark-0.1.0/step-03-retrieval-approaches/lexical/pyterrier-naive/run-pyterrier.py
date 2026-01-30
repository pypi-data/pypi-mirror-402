#!/usr/bin/env python3
import lsr_benchmark
import click
from tirex_tracker import tracking, ExportFormat, register_metadata
from tqdm import tqdm
import pyterrier as pt
from shutil import rmtree
import pandas as pd
from tira.third_party_integrations import ensure_pyterrier_is_loaded,  normalize_run
import ir_datasets
from lsr_benchmark.click import  option_lsr_dataset, option_retrieval_depth

@click.command()
@option_lsr_dataset()
@option_retrieval_depth()
@click.option("--retrieval", type=str, required=False, default="BM25", help="The retrieval model to use.")
def main(dataset, output, retrieval, k):
    output.mkdir(parents=True, exist_ok=True)
    lsr_benchmark.register_to_ir_datasets(dataset)
    ir_dataset = ir_datasets.load(f"lsr-benchmark/{dataset}")
    ensure_pyterrier_is_loaded(boot_packages=())

    register_metadata({"actor": {"team": "reneuir-baselines"}, "tag": f"pyterrier-naive-{retrieval.lower()}-top-{k}"})
    documents = [{"docno": i.doc_id, "text": i.default_text()} for i in ir_dataset.docs_iter()]

    with tracking(export_file_path=output / "index-metadata.yml", export_format=ExportFormat.IR_METADATA):
        index = pt.IterDictIndexer("ignored", meta= {'docno' : 100}, type=pt.IndexingType.MEMORY).index(tqdm(documents, "Index docs"))

    rmtree(output / ".tirex-tracker")
    queries = []
    tokeniser = pt.autoclass("org.terrier.indexing.tokenisation.Tokeniser").getTokeniser()

    def pt_tokenize(text):
        return ' '.join(tokeniser.getTokens(text))

    for i in ir_dataset.queries_iter():
        queries.extend([{"qid": i.query_id, "query": pt_tokenize(i.default_text())}])

    pipeline = pt.terrier.Retriever(index, wmodel=retrieval)
    with tracking(export_file_path=output / "retrieval-metadata.yml", export_format=ExportFormat.IR_METADATA):
        run = pipeline(pd.DataFrame(queries))

    pt.io.write_results(normalize_run(run, retrieval, k), f'{output}/run.txt')

if __name__ == "__main__":
    main()
