from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from time import time



from pydantic import BaseModel, Field

llm = ChatGroq(model = "llama-3.3-70b-versatile", temperature = 0.0,model_kwargs=dict(response_format = {"type": "json_object"}))

class QueryClassifier(BaseModel):
    is_related_to_protein_and_gene_name: bool = Field(
        ..., description="Indicates whether the query is related to a protein or gene name. if the query is related to a protein or gene name or symbol, the value is True. Otherwise, the value is False."
    )


from langchain_core.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnableLambda
import json

# Define the prompt
prompt = PromptTemplate(
    input_variables=["query"],
    template="""
    You are a classifier that determines whether a given query is related to a protein or gene name.
    
    Query: {query}
    
    Respond in JSON format following this schema:
    {{
        "is_related_to_protein_and_gene_name": <true or false>
    }}
    """
)

# Define JSON parser
def parse_response(response: str):
    try:
        return QueryClassifier.model_validate_json(response)
    except json.JSONDecodeError:
        return {"is_related_to_protein_and_gene_name": False}  # Default to False if parsing fails

json_parser = RunnableLambda(parse_response)

# Create the chain
query_classifier_chain = prompt | llm | StrOutputParser() | json_parser

def query_classifier(query):
    start = time()
    response = query_classifier_chain.invoke({"query": query})
    end = time()
    print("Time taken to classify:", end - start)
    return response.is_related_to_protein_and_gene_name

if "__main__" == __name__:
    # Example usage
    query = "GM"
    response = query_classifier_chain.invoke({"query": query})
    print(response.is_related_to_protein_and_gene_name)