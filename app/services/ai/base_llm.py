from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class BaseLLM(ABC):
    @abstractmethod
    def generate_response(self, 
                         query: str, 
                         context: List[str],
                         citations: List[Dict] = None) -> Dict:
        """Generate response with citations"""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return model name"""
        pass