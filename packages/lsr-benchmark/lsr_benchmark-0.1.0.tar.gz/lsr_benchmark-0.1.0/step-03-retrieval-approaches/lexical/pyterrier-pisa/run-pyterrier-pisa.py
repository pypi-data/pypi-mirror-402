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
from pyterrier_pisa import PisaIndex
from tempfile import TemporaryDirectory


@click.command()
@option_lsr_dataset()
@option_retrieval_depth()
@click.option("--precompute-impact", type=bool, is_flag=True, default=False, required=False, help="Pre-compute impact scores. This speeds up retrieval..")
def main(dataset, output, k, precompute_impact):
    output.mkdir(parents=True, exist_ok=True)
    lsr_benchmark.register_to_ir_datasets(dataset)
    ir_dataset = ir_datasets.load(f"lsr-benchmark/{dataset}")
    ensure_pyterrier_is_loaded(boot_packages=())
    tag = f"pyterrier-splade-top-{k}"
    register_metadata({"actor": {"team": "reneuir-baselines"}, "tag": tag})

    documents = [{"docno": i.doc_id, "text": i.default_text()} for i in ir_dataset.docs_iter()]

    with TemporaryDirectory() as tmpdir:
        with tracking(export_file_path=output / "index-metadata.yml", export_format=ExportFormat.IR_METADATA):
            index = PisaIndex(tmpdir.name)
            index.index(tqdm(documents, "Index docs"))
            pipeline = index.bm25(precompute_impact=precompute_impact)

    rmtree(output / ".tirex-tracker")

    queries = []
    for i in ir_dataset.queries_iter():
        queries.extend([{"qid": i.query_id, "query": i.default_text()}])

    with tracking(export_file_path=output / "retrieval-metadata.yml", export_format=ExportFormat.IR_METADATA):
        run = pipeline(pd.DataFrame(queries))

    pt.io.write_results(normalize_run(run, tag, k), f'{output}/run.txt')

if __name__ == "__main__":
    main()
