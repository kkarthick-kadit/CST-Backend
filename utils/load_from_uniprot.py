import json
import http.client
import urllib.parse


def from_uniprot(query):
    conn = http.client.HTTPSConnection("rest.uniprot.org")
    encoded_query = urllib.parse.quote(f"({query}) AND (reviewed:true)")
    # url = f"/uniprotkb/search?fields=accession%2Corganism_name%2Cprotein_name%2Cgene_names%2Creviewed%2Ckeyword%2Cprotein_existence%2Clength&query={encoded_query}&format=json&size=100"
    url = f"/uniprotkb/search?fields=comment_count,feature_count,length,structure_3d,annotation_score,protein_existence,lit_pubmed_id,accession,organism_name,protein_name,gene_names,reviewed,keyword,id&query=%28{encoded_query}%29&size=100&format=json"
    conn.request("GET", url)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data)

def extract_entry_info_from_uniprot(query):
    entries = from_uniprot(query)
    results = entries.get("results", [])
    formatted_entries = []

    for entry in results:
        alt_names = []

        # Recommended full name
        rec_name = entry.get("proteinDescription", {}).get("recommendedName", {})
        rec_full = rec_name.get("fullName", {}).get("value")
        if rec_full:
            alt_names.append(rec_full)

        # Recommended short names
        rec_short = rec_name.get("shortNames", [])
        alt_names.extend([s.get("value") for s in rec_short if s.get("value")])

        # Alternative names (full + short)
        alt_full = entry.get("proteinDescription", {}).get("alternativeNames", [])
        for alt in alt_full:
            full_name = alt.get("fullName", {}).get("value")
            if full_name:
                alt_names.insert(0, full_name)  # Put alt full name at the beginning
            short_names = alt.get("shortNames", [])
            alt_names.extend([s.get("value") for s in short_names if s.get("value")])

        # Create semicolon-separated text
        text = "; ".join(alt_names)

        # Metadata fields
        primary_accession = entry.get("primaryAccession", "")
        organism = entry.get("organism", {})
        organism_full = f'{organism.get("scientificName", "")} ({organism.get("commonName", "")})'
        gene_info = entry.get("genes", [{}])[0]
        gene_symbol = gene_info.get("geneName", {}).get("value", "")

        try:
            hgnc_id = gene_info.get("geneName", {}).get("evidences", "").strip().split(":")[1]
        except Exception :
            hgnc_id = ""

        formatted_entries.append({
            "text": text,
            "metadata": {
                "CST_ID": "",
                "Reference #": primary_accession,
                "Organism": organism_full,
                "Gene Symbols": gene_symbol,
                "HGNC_ID": "",
                "Source": "Uniprot"
            }
        })
    return formatted_entries


if __name__ == "__main__":
    import asyncio
    # Call the function with your query
    structured_entries = extract_entry_info_from_uniprot("akt1")
    # structured_entries = asyncio.run(extract_entry_info_from_uniprot("akt1"))

    # Print the result
    # print(json.dumps(structured_entries, indent=4))
