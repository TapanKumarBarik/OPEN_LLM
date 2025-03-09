from .base_llm import BaseLLM
from openai import AzureOpenAI
import os

class AzureOpenAILLM(BaseLLM):
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
    def generate_response(self, query, context, citations=None):
        prompt = self._build_prompt(query, context)
        response = self.client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_MODEL"),
            messages=[{"role": "user", "content": prompt}]
        )
        return {
            "answer": response.choices[0].message.content,
            "citations": citations
        }

    def get_model_name(self):
        return "azure-openai"