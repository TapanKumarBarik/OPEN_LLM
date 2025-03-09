from .azure_llm import AzureOpenAILLM
from .phi_llm import PhiLLM
import os

def get_llm_instance():
    llm_type = os.getenv("LLM_TYPE", "phi")
    
    if llm_type == "azure":
        return AzureOpenAILLM()
    else:
        return PhiLLM()