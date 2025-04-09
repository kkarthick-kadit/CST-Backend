from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders import DataFrameLoader
import time
from Apis.embeddings import get_embeddings
import pandas as pd
from Apis.mongo_connection import collection, create_mongo_indexes

df = pd.read_csv("data/protein_data.csv")

# df[["Alt. Names","Gene Symbols"]].to_csv("data/synames.csv", index=False)
# loader = DataFrameLoader(df["Alt. Names"])
# print(loader.load())

def load_data():
    if collection.count_documents({}) == 0:
        json_list = df[["Alt. Names", "Gene Symbols","CST_ID","Reference #", "Organism"]].to_dict(orient="records")

        print("Embeddings Started")
        start = time.time()

        documents_to_be_pushed = [{"embedding": get_embeddings(i["Alt. Names"]),"text": i["Alt. Names"],
            "metadata": { 
            "CST_ID": i["CST_ID"], 
            "Reference #": i["Reference #"], 
            "Organism": i["Organism"], 
            "Gene Symbols": i["Gene Symbols"]
        }} for i in json_list]

        end = time.time()
        print("Embeddings Finished in", end - start)

        collection.insert_many(documents_to_be_pushed)
        create_mongo_indexes(len(get_embeddings("check")))