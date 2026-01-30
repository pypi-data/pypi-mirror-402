#!/usr/bin/env python3
import click
from tira.rest_api_client import Client
import pandas as pd
from lsr_benchmark.datasets import lsr_overview, TIRA_DATASET_ID_TO_IR_DATASET_ID, EMBEDDING_MODEL_TO_PRETTY_NAME, EMBEDDING_MODEL_TO_HF_NAME, EMBEDDING_MODEL_TO_ENGINE, EMBEDDING_ENGINE_LINKS


def upload_aggregated_results(aggregated_results):
    tira = Client()
    tira.modify_task("lsr-benchmark", {"aggregated_results": aggregated_results})


DATASET_TO_AGGREGATION = {
    "CW09": ["trec-18-web-20251008-test",  "trec-19-web-20251008-test", "trec-20-web-20251008-test", "trec-21-web-20251008-test"],
    "CW12": ["trec-28-misinfo-20251008_1-test", "trec-23-web-20251008-test", "trec-22-web-20251008-test"],
    "R04": ["trec-robust-2004-fold-1-20250927-test", "trec-robust-2004-fold-5-20250926-test", "trec-robust-2004-fold-2-20250926-test", "trec-robust-2004-fold-3-20250926-test", "trec-robust-2004-fold-4-20250926-test"],
    "RAG": ["trec-33-rag-20250926_1-training"],
    "DL": ["trec-29-deep-learning-passages-20250926-training", "trec-28-deep-learning-passages-20250926-training"],
    "Avg.": [
        "trec-28-misinfo-20251008_1-test", "trec-21-web-20251008-test",
        "trec-robust-2004-fold-5-20250926-test", "trec-20-web-20251008-test",
        "trec-23-web-20251008-test", "trec-22-web-20251008-test",
        "trec-33-rag-20250926_1-training", "trec-robust-2004-fold-2-20250926-test",
        "trec-19-web-20251008-test", "trec-29-deep-learning-passages-20250926-training",
        "trec-18-web-20251008-test", "trec-robust-2004-fold-3-20250926-test",
        "trec-28-deep-learning-passages-20250926-training", "trec-robust-2004-fold-1-20250927-test",
        "trec-robust-2004-fold-4-20250926-test"
    ]
}

def ndcg(df, group):
    df = df.copy()
    df = df[df["tira-dataset-id"].isin(set(DATASET_TO_AGGREGATION[group]))]
    if len(df) != len(set(DATASET_TO_AGGREGATION[group])):
        raise ValueError(f"Expected results for all datasets in group {group}.")
    return int(df["nDCG@10"].mean()*1000)/1000

def embedding_model_results():
    lines = []

    overview_per_dataset = lsr_overview()
    embedding_to_size = {}

    df = pd.read_json("../step-04-evaluation/results-in-progress.jsonl.gz", lines=True)
    df["index.runtime_wallclock"] = df["index.runtime_wallclock"].apply(lambda i: int(i.split()[0]))
    df["retrieval.runtime_wallclock"] = df["retrieval.runtime_wallclock"].apply(lambda i: int(i.split()[0]))

    # filter to engines that did run on bm25 to ensure that we compare the same things in the averages
    retrieval_engines = set(df[df["embedding/model"] == "bm25"]["Retrieval"].unique())

    df = df[df["Retrieval"].isin(retrieval_engines)]

    embedding_model_to_retrieval_time = {}
    
    for n, i in df[['embedding/model', "retrieval_per_query.runtime_wallclock"]].groupby("embedding/model").describe(percentiles=[0.5, .9, .99]).iterrows():
        embedding_model_to_retrieval_time[n] = int(i[("retrieval_per_query.runtime_wallclock", "50%")]*100)/100

    for dataset_id in TIRA_DATASET_ID_TO_IR_DATASET_ID:
        for k,v in overview_per_dataset[dataset_id]["embedding-sizes"].items():
            if k not in embedding_to_size:
                embedding_to_size[k] = []
            embedding_to_size[k] += [v]

    # for the efficiency stuff, we only take the exact search
    df = df[df["Retrieval"].isin(set(["naive-search"]))]

    for e, s in embedding_to_size.items():
        e_display = e.replace("naver-", "naver/").replace("webis-", "webis/").replace("castorini-", "castorini/").replace("opensearch-project-", "opensearch-project/")
        df_eval = df.copy()
        df_eval = df_eval[df_eval["embedding/model"] == e_display]
        
        lines += [{
            "embedding_model": EMBEDDING_MODEL_TO_PRETTY_NAME[e],
            "embedding_model_link": EMBEDDING_MODEL_TO_HF_NAME[e],
            "embedding_size": int((sum([int(i) for i in s])/len(s))/1024),
            "engine": EMBEDDING_MODEL_TO_ENGINE[e],
            "engine_link": EMBEDDING_ENGINE_LINKS[EMBEDDING_MODEL_TO_ENGINE[e]],
            "latency": embedding_model_to_retrieval_time[e_display],
            "CW09": ndcg(df_eval, "CW09"),
            "CW12": ndcg(df_eval, "CW12"),
            "DL": ndcg(df_eval, "DL"),
            "R04": ndcg(df_eval, "R04"),
            "RAG": ndcg(df_eval, "RAG"),
            "Avg.": ndcg(df_eval, "Avg.")
        }]
    
    return {
        "title": "Overview of Embedding Models",
        "description": "We compare embedding models for learned sparse retrieval for efficiency and effectiveness accross eleven TREC shared tasks and eight retrieval engines. The table shows the average size of the embeddings and the median latency in milliseconds accross the eight retrieval engines (as efficiency aspects) together with the nDCG@10 (as effectiveness aspect).",
        "ev_keys": ["CW09", "CW12", "DL", "R04", "RAG", "Avg."],
        "lines": lines,
        "table_headers": [
            {"title": "Embedding", "key": "embedding_model"},
            {"title": "Engine", "key": "engine", "align": "center"},
            {"title": "Efficiency",
             "align": "center",
             "children": [
                {"title": "Avg. Size (MB)", "key": "embedding_size", "align": "center"},
                {"title": "Latency per Query (ms)", "key": "latency", "align": "center"},
             ]
            },
            {"title": "  ", "key": "does not exist"},
            {"title": "Effectiveness (nDCG@10)",
             "align": "center",
             "children": [
               {"title": "CW09", "key": "CW09"},
               {"title": "CW12", "key": "CW12"},
               {"title": "DL", "key": "DL"},
               {"title": "R04", "key": "R04"},
               {"title": "RAG", "key": "RAG"},
               {"title": "Avg.", "key": "Avg."}
             ]
            }
        ],
        "table_headers_small_layout": [
            {"title": "Embedding", "key": "embedding_model"},
            {"title": "Avg. nDCG@10", "key": "Avg."},
        ],
        "table_sort_by": [{"key": "Avg.", "order": "desc"}],
    }


def retrieval_engines_results():
    lines = []
    engine_to_name = {
        "duckdb": "DuckDB",
        "kannolo": "kANNolo",
        "naive-search": "Naive",
        "pyserini-lsr": "Pyserini",
        "pyterrier-splade": "PyTerrier",
        "pyterrier-splade-pisa": "Pisa",
        "seismic": "Seismic",
    }
    engine_to_link = {
        "duckdb": "https://github.com/reneuir/lsr-benchmark/tree/main/step-03-retrieval-approaches/duckdb",
        "kannolo": "https://github.com/reneuir/lsr-benchmark/tree/main/step-03-retrieval-approaches/kannolo",
        "naive-search": "https://github.com/reneuir/lsr-benchmark/tree/main/step-03-retrieval-approaches/naive-search",
        "pyserini-lsr": "https://github.com/reneuir/lsr-benchmark/tree/main/step-03-retrieval-approaches/pyserini-lsr",
        "pyterrier-splade": "https://github.com/reneuir/lsr-benchmark/tree/main/step-03-retrieval-approaches/pyterrier-splade",
        "pyterrier-splade-pisa": "https://github.com/reneuir/lsr-benchmark/tree/main/step-03-retrieval-approaches/pyterrier-splade-pisa",
        "seismic": "https://github.com/reneuir/lsr-benchmark/tree/main/step-03-retrieval-approaches/seismic",
    }

    df = pd.read_json("../step-04-evaluation/results-in-progress.jsonl.gz", lines=True)
    df = df[df["embedding/model"].isin(set(['castorini/unicoil-noexp-msmarco-passage', 'naver/splade-v3-distilbert', 'opensearch-project/opensearch-neural-sparse-encoding-v2-distill', 'naver/splade-v3', 'opensearch-project/opensearch-neural-sparse-encoding-doc-v2-distill',  'opensearch-project/opensearch-neural-sparse-encoding-doc-v2-mini', 'webis/splade', 'naver/splade_v2_distil', 'bge-m3', 'opensearch-project/opensearch-neural-sparse-encoding-doc-v3-distill', 'naver/splade-v3-doc', 'naver/splade-v3-lexical']))]

    df = df[['Retrieval', "index_1000.runtime_wallclock", "retrieval_per_query.runtime_wallclock"]].groupby("Retrieval").describe(percentiles=[0.5, .9, .99])

    for _, i in df.iterrows():
        if i.name == "pytorch-naive":
            #OOM on some datasets? TODO: investigate
            continue
        lines += [{
            "embedding_model": engine_to_name[i.name],
            "embedding_model_link": engine_to_link[i.name],
            "index_50": int(100*i[("index_1000.runtime_wallclock", "50%")])/100,
            "index_90": int(100*i[("index_1000.runtime_wallclock", "90%")])/100,
            "index_99": int(100*i[("index_1000.runtime_wallclock", "99%")])/100,
            "retrieval_50": int(100*i[("retrieval_per_query.runtime_wallclock", "50%")])/100,
            "retrieval_90": int(100*i[("retrieval_per_query.runtime_wallclock", "90%")])/100,
            "retrieval_99": int(100*i[("retrieval_per_query.runtime_wallclock", "99%")])/100,
        }]

    return {
        "title": "Overview of Retrieval Engines",
        "description": "We compare different retrieval engines for learned sparse retrieval for their efficiency accross eleven TREC shared tasks and the embedding models above. The table shows the measured as wallclock runtime in milliseconds at 50%, 90%, and 99% percentiles for indexing (runtime per 1000 documents) and retrieval (runtime per query) accross all embeddings and collections.",
        "ev_keys": ["CW09", "CW12", "DL", "R04", "RAG", "Avg."],
        "lines": lines,
        "table_headers": [
            {"title": "Retrieval Engine", "key": "embedding_model"},
            {"title": "Indexing (ms)",
             "align": "center",
             "children": [
                {"title": "50%", "key": "index_50"},
                {"title": "90%", "key": "index_90"},
                {"title": "99%", "key": "index_99"},
             ]
            },
            {"title": "  ", "key": "does not exist"},
            {"title": "Retrieval (ms)",
             "align": "center",
             "children": [
                {"title": "50%", "key": "retrieval_50"},
                {"title": "90%", "key": "retrieval_90"},
                {"title": "99%", "key": "retrieval_99"},
             ]
            },
        ],
        "table_headers_small_layout": [
            {"title": "Retrieval Engine", "key": "embedding_model"},
            {"title": "50% Retrieval (ms)", "key": "retrieval_50"},
        ],
        "table_sort_by": [{"key": "retrieval_50", "order": "asc"}],
    }

@click.command()
def main():
    aggregated_results = [
        embedding_model_results(),
        retrieval_engines_results(),
    ]
    upload_aggregated_results(aggregated_results)


if __name__ == "__main__":
    main()
