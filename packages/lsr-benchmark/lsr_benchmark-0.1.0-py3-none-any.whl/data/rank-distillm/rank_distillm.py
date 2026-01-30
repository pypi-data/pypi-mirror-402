#!/usr/bin/env python3
from trectools import TrecRun
import json
from pathlib import Path
from glob import glob
from collections import defaultdict
import ir_datasets

config = json.loads(Path("rank-distillm/config.json").read_text())
runs = []

run_to_queries = {}

for run in glob(config["runs"] + "/*"):
    run_to_queries[run] = list(set(TrecRun(run).run_data["query"].unique()))

query_to_count = defaultdict(lambda: 0)

for run, queries in run_to_queries.items():
    for query in queries:
        query_to_count[query] = query_to_count[query] + 1

queries_to_retain = set([i for i, v in query_to_count.items() if v == len(run_to_queries)])

if not Path("rank-distillm/subsample.json").exists():
    docs = set()
    for run in glob(config["runs"] + "/*"):
        run = TrecRun(run).run_data
        for _, i in run.iterrows():
            if i.query in queries_to_retain:
                docs.add(str(i.docid))

    Path("rank-distillm/subsample.json").write_text(json.dumps(sorted(list(docs))))

def register_dataset():
    from ir_datasets import registry
    if "rank-distillm" not in registry:
        ds = as_dataset()
        registry.register("rank-distillm", ds)

def as_dataset():
    import ir_datasets
    from ir_datasets.datasets.base import Dataset
    ds = ir_datasets.load("msmarco-passage/train/judged")

    queries = []
    for query in ds.queries_iter():
        if query.query_id in queries_to_retain:
            queries.append(query)

    qrels = []
    for qrel in ds.qrels_iter():
        if qrel.query_id in queries_to_retain:
            qrels.append(qrel)

    
    class RankDistillmQueries():
        def queries_iter(self):
            return queries

    class RankDistillmQrels():
        def qrels_iter(self):
            return qrels

    class RankDistillmDocs():
        def docs_store(self):
            return ds.docs_store()
   
    return Dataset(RankDistillmDocs(), RankDistillmQueries(), RankDistillmQrels())

register_dataset()
ds = ir_datasets.load("rank-distillm")

for i in ds.queries_iter():
    print(i)
    break

for i in ds.qrels_iter():
    print(i)
    break


print("qrels", len(list(ds.qrels_iter())))
print("queries", len(list(ds.queries_iter())))
