from pathlib import Path
from ir_datasets.formats import BaseDocs
from ir_datasets.indices.base import Docstore
from ir_datasets import Dataset
from ir_datasets.formats import TrecQrels, TrecXmlQueries
from ir_datasets.util import StringFile
from ir_datasets import registry
import json
import gzip

def cached_chatnoir_docs_store(chatnoir_index: str, cache_file: Path):
    from chatnoir_api.irds import ChatNoirDocsStore, ChatNoirOwiDoc
    docs_store = ChatNoirDocsStore(chatnoir_index)
    doc_id_to_doc = {}

    with gzip.open(cache_file, "rt") as f:
        for line in f:
            try:
                doc = json.loads(line)
            except Exception:
                print(f"Warning: Could not parse line in cache file: {line}")
                continue
            doc_id_to_doc[doc["doc_id"]] = ChatNoirOwiDoc(doc["doc_id"], doc["text"], doc["url"], doc["main_content"], doc["title"], doc["description"])
            

    class CachedChatNoirDocsStore(Docstore):
        def get_many_iter(self, doc_ids):
            for doc in doc_ids:
                if doc in doc_id_to_doc:
                    yield doc_id_to_doc[doc]
                else:            
                    with gzip.open(cache_file, "at") as f:
                        ret = docs_store.get(doc)
                        f.write(json.dumps(ret._asdict()) + "\n")
                        f.flush()
                        yield ret

    return CachedChatNoirDocsStore(ChatNoirOwiDoc)

def register_subsample_from_chatnoir(chatnoir_index: str, qrels_file: Path, topics_file: Path, ir_datasets_id: str):
    if ir_datasets_id in registry:
        return

    class ChatNoirDocs(BaseDocs):
        def docs_store(self):
            return cached_chatnoir_docs_store(chatnoir_index, Path(qrels_file).parent.parent / "chatnoir-docs.jsonl.gzip")

    topics = TrecXmlQueries(StringFile(open(topics_file, "r").read()))
    docs = ChatNoirDocs()
    qrels = TrecQrels(StringFile(open(qrels_file, "r").read()), {})

    dataset = Dataset(docs, qrels, topics)
    registry.register(ir_datasets_id, dataset)
    

