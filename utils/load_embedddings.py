from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders import DataFrameLoader
import time
from pymongo.errors import BulkWriteError
from Apis.embeddings import get_embeddings
import pandas as pd
from Apis.mongo_connection import collection, create_mongo_indexes

df = pd.read_csv("data/protein_data.csv")

df = pd.read_csv("data/Proteins_processed.csv")

# df[["Alt. Names","Gene Symbols"]].to_csv("data/synames.csv", index=False)
# loader = DataFrameLoader(df["Alt. Names"])
# print(loader.load())

# def load_data():
#     if collection.count_documents({}) == 0:
#         json_list = df[["Alt. Names", "Gene Symbols","CST_ID","Reference #", "Organism"]].to_dict(orient="records")

#         print("Embeddings Started")
#         start = time.time()

#         documents_to_be_pushed = [{"embedding": get_embeddings(i["Alt. Names"]),"text": i["Alt. Names"],
#             "metadata": { 
#             "CST_ID": i["CST_ID"], 
#             "Reference #": i["Reference #"], 
#             "Organism": i["Organism"], 
#             "Gene Symbols": i["Gene Symbols"]
#         }} for i in json_list]

#         end = time.time()
#         print("Embeddings Finished in", end - start)

#         collection.insert_many(documents_to_be_pushed)
#         create_mongo_indexes(len(get_embeddings("check")))

def load_data():
    if collection.count_documents({}) == 0:
        json_list = df[["Alt. Names", "Gene Symbols", "CST_ID", "Reference #", "Organism"]].to_dict(orient="records")

        print("Embeddings Started")
        start = time.time()
        success_count = 0

        documents_to_be_pushed = []

        for idx, record in enumerate(json_list, 1):
            alt_names = record.get("Alt. Names", "")
            if not alt_names:
                continue  # skip empty Alt. Names

            for name in alt_names.split(";"):
                name = name.strip()
                if not name:
                    continue

                try:
                    embedding = get_embeddings(name)
                    documents_to_be_pushed.append({
                        "embedding": embedding,
                        "text": alt_names,
                        "metadata": {
                            "CST_ID": record["CST_ID"],
                            "Reference #": record["Reference #"],
                            "Organism": record["Organism"],
                            "Gene Symbols": record["Gene Symbols"]
                        }
                    })
                    success_count += 1
                except Exception as e:
                    print(f"Failed to embed '{name}': {e}")

            if idx % 100 == 0:
                print(f"{idx} records processed...")

        end = time.time()
        print("Embeddings Finished in", end - start)

        # Insert in batches of 1000
        batch_size = 1000
        for i in range(0, len(documents_to_be_pushed), batch_size):
            batch = documents_to_be_pushed[i:i+batch_size]
            try:
                result = collection.insert_many(batch)
                print(f"Inserted {len(result.inserted_ids)} documents (Batch {i//batch_size + 1})")
            except BulkWriteError as bwe:
                print(f"Bulk write error in batch {i//batch_size + 1}: {bwe.details}")
            except Exception as e:
                print(f"Error inserting batch {i//batch_size + 1}: {e}")
            time.sleep(10)

        # Create indexes
        try:
            create_mongo_indexes(len(get_embeddings("check")))
        except Exception as e:
            print("Error while creating indexes:", e)