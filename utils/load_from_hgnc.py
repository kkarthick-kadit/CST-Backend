import json
import http.client
import html
import urllib.parse


def fetch_hgnc_info(query):
    conn = http.client.HTTPSConnection("genenames.org")
    encoded_query = urllib.parse.quote(query)
    url = f"/cgi-bin/search/search?query={encoded_query}&rows=20&start=0"
    conn.request("GET", url)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data)

def extract_hgnc_entries(query):
    data = fetch_hgnc_info(query)
    documents = data.get("documents", [])
    formatted_entries = []

    for doc in documents:
        # Filter only Page type == 'Gene'
        display_fields = doc.get("display", [])
        page_type = next((d.get("value") for d in display_fields if d.get("label") == "Page type"), None)
        if page_type != "Gene":
            continue

        matches = next((d.get("value") for d in display_fields if d.get("label") == "Matches"), {})
        
        # Collect all names: gene_name + all 'Matches' values
        all_names = []

        # Gene name
        gene_name = doc.get("gene_name", "")
        if gene_name:
            all_names.append(gene_name)

        # Previous gene names and symbols
        for key in ["Previous gene name", "Previous gene symbol"]:
            values = matches.get(key, [])
            all_names.extend([html.unescape(v).replace("<b>", "").replace("</b>", "") for v in values])

        # Also include "Gene name" from matches if not already in list
        for v in matches.get("Gene name", []):
            clean_v = html.unescape(v).replace("<b>", "").replace("</b>", "")
            if clean_v not in all_names:
                all_names.append(clean_v)

        # Create semicolon-separated text
        text = "; ".join(all_names)

        # Get HGNC ID
        hgnc_id = next((d.get("value") for d in display_fields if d.get("label") == "HGNC ID"), "")
        hgnc_id = hgnc_id.replace("HGNC:", "")

        # Gene Symbol
        gene_symbol = doc.get("gene_symbol", "")

        formatted_entries.append({
            "text": text,
            "metadata": {
                "CST_ID": "",
                "Reference #": f"https://www.uniprot.org/uniprotkb?query=%28xref%3Ahgnc-{hgnc_id}%29",
                "Organism": "",
                "Gene Symbols": gene_symbol,
                "HGNC_ID": hgnc_id,
                "Source": "HGNC"
            }
        })

    return formatted_entries


if __name__ =="__main__":
    # Run with a gene symbol query
    structured_entries = extract_hgnc_entries("anf")

    # Print result
    print(json.dumps(structured_entries, indent=4))
