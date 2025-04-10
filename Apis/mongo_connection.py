from pymongo import MongoClient
from pymongo.operations import SearchIndexModel
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_core.documents import Document
import time
import re
import os


# Connect to your Atlas cluster
client = MongoClient(os.getenv("MONGODB_URI"))
# client = MongoClient("mongodb://localhost:27017/")
collection = client["DEV"]["PHOSPHOSITE"]


### Create the index
def create_mongo_indexes(dimensions):
# Create your index model, then create the search index
    index_name="vector_index"
    search_index_model = SearchIndexModel(
    definition = {
        "fields": [
        {
            "type": "vector",
            "numDimensions": dimensions,
            "path": "embedding",
            "similarity": "cosine"
        }
        ]
    },
    name = index_name,
    type = "vectorSearch"
    )
    collection.create_search_index(model=search_index_model)

    # Wait for initial sync to complete
    print("Polling to check if the index is ready. This may take up to a minute.")
    predicate=None
    if predicate is None:
        predicate = lambda index: index.get("queryable") is True

    while True:
        indices = list(collection.list_search_indexes(index_name))
        if len(indices) and predicate(indices[0]):
            break
        time.sleep(5)
    print(index_name + " is ready for querying.")


def search_cst(embeddings):
    vector_store = MongoDBAtlasVectorSearch(
        collection=collection,
        embedding=embeddings,
        index_name="vector_index",
        relevance_score_fn="cosine",
    )

    return vector_store


def is_uniprot_id(id):
    uniprot_id = lambda text: re.findall(r"(?i)\b[A-Z]\w{5}\b", text)
    result = uniprot_id(id)
    if result:
        query = {"metadata.Reference #": id}
        return list(collection.find(query,{"embedding": 0, "_id": 0}))
    else:
        return []