from langchain_huggingface import HuggingFaceEmbeddings

embedding_model_name = 'sentence-transformers/all-MiniLM-L12-v2'
# embedding_model_name ="microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext"
# embedding_model_name = "Rostlab/prot_bert"
embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name, model_kwargs={'device': 'cpu'})

def get_embeddings(text):
    return embeddings.embed_query(text)
len(get_embeddings("hi"))