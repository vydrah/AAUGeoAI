"""
LLM Client for multiple providers (Ollama, OpenAI, Claude, Gemini)
"""

import requests
import json
from typing import Optional, Dict, Any


class LLMClient:
    """Client for interacting with various LLM providers."""
    
    def __init__(self, provider: str, base_url: str, api_key: str, model: str):
        """
        Initialize LLM client.
        
        :param provider: Provider name (Ollama, OpenRouter, Gemini)
        :type provider: str
        :param base_url: Base URL for API
        :type base_url: str
        :param api_key: API key (optional for Ollama)
        :type api_key: str
        :param model: Model name
        :type model: str
        """
        self.provider = provider.lower()
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model
    
    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Generate a response from the LLM.
        
        :param prompt: Input prompt
        :type prompt: str
        :param kwargs: Additional parameters
        :type kwargs: dict
        
        :returns: Generated response text
        :rtype: str or None
        """
        if self.provider == "ollama":
            return self._generate_ollama(prompt, **kwargs)
        elif self.provider == "openrouter":
            return self._generate_openrouter(prompt, **kwargs)
        elif self.provider == "gemini":
            return self._generate_gemini(prompt, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _generate_ollama(self, prompt: str, **kwargs) -> Optional[str]:
        """Generate response using Ollama."""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def _generate_openrouter(self, prompt: str, **kwargs) -> Optional[str]:
        """Generate response using OpenRouter (OpenAI/Claude compatible)."""
        url = f"{self.base_url}/chat/completions"
        
        # Determine model provider
        if "gpt" in self.model.lower():
            # OpenAI format
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                **kwargs
            }
        elif "claude" in self.model.lower():
            # Anthropic format
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                **kwargs
            }
        else:
            # Default to OpenAI format
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                **kwargs
            }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract response based on format
            if "choices" in result:
                return result["choices"][0]["message"]["content"]
            elif "content" in result:
                return result["content"]
            else:
                return str(result)
        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenRouter API error: {str(e)}")
    
    def _generate_gemini(self, prompt: str, **kwargs) -> Optional[str]:
        """Generate response using Google Gemini."""
        url = f"{self.base_url}/models/{self.model}:generateContent"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            **kwargs
        }
        
        params = {
            "key": self.api_key
        }
        
        try:
            response = requests.post(url, json=payload, params=params, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract response from Gemini format
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        return parts[0]["text"]
            
            return str(result)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        Test connection to the LLM provider.
        
        :returns: True if connection successful
        :rtype: bool
        """
        try:
            response = self.generate("Test connection. Reply with 'OK'.")
            return response is not None and len(response) > 0
        except Exception:
            return False

