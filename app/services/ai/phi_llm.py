from .base_llm import BaseLLM
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class PhiLLM(BaseLLM):
    def __init__(self):
        self.model = AutoModelForCausalLM.from_pretrained(
            "microsoft/Phi-3.5-mini-instruct",
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True 
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            "microsoft/Phi-3.5-mini-instruct",
            trust_remote_code=True 
        )

    def generate_response(self, query, context, citations=None):
        prompt = self._build_prompt(query, context)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(**inputs, max_length=512)
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return {
            "answer": response,
            "citations": citations
        }

    def get_model_name(self):
        return "phi-3.5"