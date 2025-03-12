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
        
        

    def _build_prompt(self, query: str, context: list) -> str:
        # Create a combined context string from all chunks
        context_str = "\n\n".join(context)
            
        # Build a detailed prompt with instructions
        prompt = f"""Use the following pieces of content to answer the question below. 
        Content:
        {context_str}
        
        Question: {query}
        
        Answer:"""
            
        return prompt        

    def generate_response(self, query, context):
        prompt = self._build_prompt(query, context)
        response = self.client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_MODEL"),
            messages=[{"role": "user", "content": prompt}]
        )
        return {
            "answer": response.choices[0].message.content
        }

    def get_model_name(self):
        return "azure-openai"