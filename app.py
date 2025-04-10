from utils.load_embedddings import load_data, create_mongo_indexes
from Apis.mongo_connection import search_cst, is_uniprot_id
from Apis.embeddings import embeddings
from utils.tools import process_results, fetch_hgnc_id
from utils.load_from_hgnc import extract_hgnc_entries
from utils.load_from_uniprot import extract_entry_info_from_uniprot

from fastapi import FastAPI, Request
import uvicorn
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from Apis.llm import query_classifier
import time

import concurrent.futures

from services.autosuggestion import suggester

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)

#Load Embediing data
# load_data()

#templates
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def run_retriever(query,k):
    retriever = search_cst(embeddings)
    results = retriever.similarity_search_with_score(
        query, k=k
    )
    print(results[0][0].page_content)
    results = [{"text": i[0].page_content,"metadata":i[0].metadata["metadata"], "score": i[1]} for i in results if i[1]>0.5]
    results = process_results(results)


    return {"results": results}

@app.get("/search",response_class=JSONResponse)
async def cst_search(query: str, k: int = 10,from_another_source :bool = False):
    print(from_another_source,query,k)
    is_ref = is_uniprot_id(query)

    if is_ref:
        Genes = [fetch_hgnc_id(i.get("metadata", {}).get("Gene Symbols", "")) for i in is_ref]

        for gene in Genes:
            for i in is_ref: i.get("metadata", {})["HGNC_ID"] = gene

        return {"results":is_ref}
    start = time.time()

    # if from_another_source == False:
    #     query_classifier_result, retriever_results = await asyncio.gather(
    #         # asyncio.to_thread(query_classifier, query),
    #         query_classifier(query),
    #         run_retriever(query, k)
    #     )
    # else:
    #     query_classifier_result, retriever_results,hgnc_entries,uniprot_entries = await asyncio.gather(
    #         # asyncio.to_thread(query_classifier, query),
    #         query_classifier(query),
    #         run_retriever(query, k),
    #         extract_hgnc_entries(query),
    #         extract_entry_info_from_uniprot(query)

    #     )

    if from_another_source:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(query_classifier, query),
                executor.submit(run_retriever, query, k),
                executor.submit(extract_hgnc_entries, query),
                executor.submit(extract_entry_info_from_uniprot, query)
            ]
            results = [f.result() for f in futures]
            query_classifier_result, retriever_results,hgnc_entries,uniprot_entries = results
            retriever_results["results"] =  retriever_results["results"] + hgnc_entries + uniprot_entries

    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(query_classifier, query),
                executor.submit(run_retriever, query, k),
            ]
            results = [f.result() for f in futures]
            query_classifier_result, retriever_results = results

    end = time.time()
    print("Time taken to search:", end - start)

    if query_classifier_result:
        return retriever_results
    else:
        return {
            "results": [
                {
                    "text": "No results found.",
                    "metadata": {
                        "CST_ID": "",
                        "Reference #": "",
                        "Organism": "",
                        "Gene Symbols": "",
                        "HGNC_ID": ""
                    },
                }
            ]
        }
    


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


app.include_router(suggester)
    
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)