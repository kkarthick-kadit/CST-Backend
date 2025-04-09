import requests
from xml.etree import ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import time

def fetch_hgnc_id(gene_symbol: str) -> str:
    """Fetch the HGNC ID for a given gene symbol from the new API endpoint."""
    url = f"https://rest.genenames.org/search/symbol/{gene_symbol}"
    headers = {"Accept": "application/xml"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        root = ET.fromstring(response.text)
        hgnc_id = root.find(".//str[@name='hgnc_id']")
        if hgnc_id is not None:
            
            return hgnc_id.text.split(":")[1]
    return ""


def process_results(results):
    """Fetch HGNC IDs concurrently and update metadata."""
    gene_symbol_to_result = {}  
    start = time.time()

    for result in results:
        doc= result
        metadata = doc.get("metadata", {})  # Use .get() for safer access
        gene_symbols = metadata.get("Gene Symbols", "").split("; ")
        
        if gene_symbols and gene_symbols[0]:  # Ensure we have a valid gene symbol
            gene_symbol_to_result[gene_symbols[0]] = doc 

    # Fetch HGNC IDs in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        hgnc_ids = list(executor.map(fetch_hgnc_id, gene_symbol_to_result.keys()))

    # Update metadata with fetched HGNC IDs
    for (gene_symbol, doc), hgnc_id in zip(gene_symbol_to_result.items(), hgnc_ids):
        doc["metadata"]["HGNC_ID"] = hgnc_id
        doc["metadata"]["Source"] = "CST"
    
    end = time.time()
    print("Time taken to fetch HGNC IDs:", end - start)
    
    return results

if __name__ == "__main__":
    print(fetch_hgnc_id("akt1"))