import os
import asyncio
import httpx
from app.config.settings import settings
from langchain_community.llms import Ollama, HuggingFaceHub
from langchain_core.language_models import BaseLanguageModel
from typing import Optional, Dict, Any
import requests
import logging
import time

# Configuration du logging
logger = logging.getLogger(__name__)

class LLMConfig:
    """Configuration centralisée pour les modèles de langage - VERSION OPTIMISÉE"""
    
    def __init__(self):
        self.hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", settings.OLLAMA_HOST)
        # CORRECTION: Timeout réduit pour éviter les blocages
        self.timeout = min(settings.OLLAMA_TIMEOUT, 60)  # Max 60 secondes
        self.quick_timeout = 30  # Timeout rapide pour les tests
        
        logger.info(f"🔧 LLM Config initialized - Ollama URL: {self.ollama_url}, Timeout: {self.timeout}s")
        
    def _check_service(self, url: str, timeout: int = 5) -> bool:
        """Vérifie la disponibilité d'un service avec timeout court"""
        try:
            response = requests.get(f"{url}/api/tags", timeout=timeout)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Service indisponible {url}: {str(e)}")
            return False
        
    def _get_ollama_models(self) -> list:
        """Récupère la liste des modèles Ollama installés"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                logger.info(f"📋 Found {len(models)} Ollama models")
                return models
            return []
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch Ollama models: {e}")
            return []

    def get_ollama_llm(self, model_name: str = None, **kwargs) -> BaseLanguageModel:
        """
        Retourne un LLM Ollama configuré avec paramètres optimisés
        """
        model_name = model_name or settings.OLLAMA_MODEL
        
        # Paramètres optimisés pour éviter les timeouts
        base_params = {
            "model": model_name,
            "base_url": self.ollama_url,
            "temperature": settings.OLLAMA_TEMPERATURE,
            "num_ctx": min(settings.OLLAMA_NUM_CTX, 3072),  # Contexte réduit
            "keep_alive": settings.OLLAMA_KEEP_ALIVE,
            "timeout": self.timeout,
            "num_predict": min(kwargs.get("num_predict", 1000), 1500),  # Limite les tokens
            "top_k": 40,
            "top_p": 0.9,
            **kwargs
        }
        
        logger.info(f"🤖 Creating Ollama LLM with model: {model_name}")
        
        try:
            return Ollama(**base_params)
        except Exception as e:
            logger.error(f"❌ Failed to create Ollama LLM: {e}")
            raise RuntimeError(f"Could not initialize Ollama LLM: {str(e)}")
    
    def get_quick_llm(self, model_name: str = None) -> BaseLanguageModel:
        """
        LLM optimisé pour réponses rapides (timeout court)
        """
        return self.get_ollama_llm(
            model_name=model_name,
            timeout=self.quick_timeout,
            num_ctx=2048,  # Contexte très réduit
            num_predict=500,  # Réponses courtes
            temperature=0.1  # Plus déterministe
        )
    
    def get_huggingface_llm(self, model_name: str = "google/flan-t5-large") -> BaseLanguageModel:
        """
        Fallback vers les modèles HuggingFace
        """
        if not self.hf_token:
            raise RuntimeError("HuggingFace token not configured - set HUGGINGFACEHUB_API_TOKEN")
        
        try:
            logger.info(f"🤗 Creating HuggingFace LLM with model: {model_name}")
            return HuggingFaceHub(
                repo_id=model_name,
                huggingfacehub_api_token=self.hf_token,
                model_kwargs={
                    "temperature": 0.1,
                    "max_length": min(settings.OLLAMA_MAX_TOKENS, 1000),
                    "top_k": 50,
                    "top_p": 0.95
                }
            )
        except Exception as e:
            logger.error(f"❌ Failed to create HuggingFace LLM: {e}")
            raise RuntimeError(f"Could not initialize HuggingFace LLM: {str(e)}")
    
    def get_default_llm(self) -> BaseLanguageModel:
        """
        LLM principal avec fallback automatique
        """
        if not settings.ENABLE_LLM_ANALYSIS:
            raise RuntimeError("LLM analysis is disabled in settings")
        
        # Tentative 1: Ollama avec le modèle par défaut
        if self._check_service(self.ollama_url):
            installed_models = self._get_ollama_models()
            
            # Chercher le modèle configuré
            model_names_to_try = [
                settings.OLLAMA_MODEL,
                "mistral:7b-instruct-v0.2-q4_0",
                "mistral:latest",
                "mistral",
                "llama2:latest",
                "llama2"
            ]
            
            for model_name in model_names_to_try:
                # Vérifier si le modèle est installé
                if any(model["name"].startswith(model_name.split(":")[0]) for model in installed_models):
                    try:
                        logger.info(f"✅ Using Ollama model: {model_name}")
                        return self.get_ollama_llm(model_name)
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to load Ollama model {model_name}: {e}")
                        continue
            
            logger.warning("⚠️ No compatible Ollama models found")
        else:
            logger.warning("⚠️ Ollama service not available")
        
        # Tentative 2: HuggingFace fallback
        if self.hf_token:
            try:
                logger.info("🤗 Falling back to HuggingFace")
                return self.get_huggingface_llm()
            except Exception as e:
                logger.error(f"❌ HuggingFace fallback failed: {e}")
        else:
            logger.warning("⚠️ HuggingFace token not configured")
        
        # Aucun LLM disponible
        raise RuntimeError(
            "Aucun LLM configuré et disponible. "
            "Veuillez installer Ollama avec au moins un modèle, "
            "ou configurer HuggingFace avec HUGGINGFACEHUB_API_TOKEN"
        )

    def get_analyzer_llm(self) -> BaseLanguageModel:
        """
        LLM pour analyses avancées avec timeout management
        """
        if not settings.ENABLE_LLM_ANALYSIS:
            raise RuntimeError("LLM analysis is disabled in settings")
            
        if self._check_service(self.ollama_url):
            installed_models = self._get_ollama_models()
            
            # Modèles préférés pour l'analyse (du plus au moins préféré)
            preferred_models = [
                "mistral:7b-instruct-v0.2-q4_0",
                "mistral:7b-instruct",
                "mistral:latest",
                "mistral",
                settings.OLLAMA_MODEL
            ]
            
            for model_name in preferred_models:
                model_base = model_name.split(":")[0]
                if any(model["name"].startswith(model_base) for model in installed_models):
                    try:
                        logger.info(f"🧠 Using analyzer model: {model_name}")
                        return self.get_ollama_llm(
                            model_name,
                            temperature=0.3,
                            num_ctx=min(settings.OLLAMA_NUM_CTX, 3072),
                            num_predict=min(1200, settings.OLLAMA_MAX_TOKENS),
                            top_k=50,
                            top_p=0.95
                        )
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to load analyzer model {model_name}: {e}")
                        continue
            
            logger.warning("⚠️ No Mistral models found, using default LLM")
    
        # Fallback vers le LLM par défaut
        return self.get_default_llm()

    async def analyze_with_timeout(self, content: str, category: str = "economic") -> Dict[str, Any]:
        """
        Analyse avec gestion de timeout et fallback
        """
        start_time = time.time()
        
        try:
            # Tentative d'analyse complète avec timeout
            llm = self.get_analyzer_llm()
            
            # Réduire le contenu si trop long
            max_content_length = 3000
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
                logger.info(f"📝 Content truncated to {max_content_length} chars")
            
            prompt = f"""
Analysez ce contenu économique tunisien en 3 phrases maximum :

{content}

Répondez en JSON simple :
{{
    "indicateurs": ["indicateur1", "indicateur2"],
    "sujet_principal": "description courte",
    "confiance": 0.8
}}
"""
            
            # Utiliser asyncio pour le timeout
            result = await asyncio.wait_for(
                self._async_llm_call(llm, prompt),
                timeout=self.timeout
            )
            
            execution_time = time.time() - start_time
            logger.info(f"✅ LLM analysis completed in {execution_time:.2f}s")
            
            return {
                "analysis": result,
                "execution_time": execution_time,
                "status": "success",
                "method": "full_analysis"
            }
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.warning(f"⏰ LLM analysis timed out after {execution_time:.2f}s")
            
            return {
                "analysis": {
                    "indicateurs": [],
                    "sujet_principal": "Analyse non complétée (timeout)",
                    "confiance": 0.0
                },
                "execution_time": execution_time,
                "status": "timeout",
                "method": "fallback",
                "error": f"Analysis timed out after {self.timeout}s"
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ LLM analysis failed: {e}")
            
            return {
                "analysis": {
                    "indicateurs": [],
                    "sujet_principal": "Erreur d'analyse",
                    "confiance": 0.0
                },
                "execution_time": execution_time,
                "status": "error",
                "method": "fallback",
                "error": str(e)
            }
    
    async def _async_llm_call(self, llm: BaseLanguageModel, prompt: str) -> str:
        """Appel LLM asynchrone"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, llm.invoke, prompt)

    def test_llm_connection(self, model_type: str = "default") -> Dict[str, Any]:
        """
        Teste la connexion LLM avec timeout court
        """
        result = {
            "timestamp": time.time(),
            "model_type": model_type,
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Test avec timeout court
            if model_type == "analyzer":
                llm = self.get_analyzer_llm()
            elif model_type == "quick":
                llm = self.get_quick_llm()
            else:
                llm = self.get_default_llm()
            
            # Test simple avec une question courte
            test_prompt = "Capitale Tunisie?"
            
            start_time = time.time()
            
            # Test avec timeout de 15 secondes max
            try:
                response = asyncio.run(
                    asyncio.wait_for(
                        self._async_llm_call(llm, test_prompt),
                        timeout=15
                    )
                )
                execution_time = time.time() - start_time
                
                result.update({
                    "status": "success",
                    "response": response[:100] + "..." if len(response) > 100 else response,
                    "response_time": f"{execution_time:.2f}s",
                    "model_info": {
                        "type": type(llm).__name__,
                        "model": getattr(llm, 'model', 'unknown')
                    }
                })
                
                logger.info(f"✅ LLM test successful for {model_type}")
                
            except asyncio.TimeoutError:
                result.update({
                    "status": "timeout",
                    "error": "Test timed out after 15s",
                    "response_time": "15.0s+"
                })
                logger.warning(f"⏰ LLM test timed out for {model_type}")
                
        except Exception as e:
            result.update({
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__
            })
            logger.error(f"❌ LLM test failed for {model_type}: {e}")
        
        return result

    def get_available_models(self) -> Dict[str, Any]:
        """
        Retourne la liste des modèles disponibles
        """
        available = {
            "ollama": {
                "service_available": self._check_service(self.ollama_url),
                "models": []
            },
            "huggingface": {
                "token_configured": bool(self.hf_token),
                "models": ["google/flan-t5-large", "google/flan-t5-xl"] if self.hf_token else []
            }
        }
        
        if available["ollama"]["service_available"]:
            available["ollama"]["models"] = [
                model["name"] for model in self._get_ollama_models()
            ]
        
        return available

# Instance globale pour tests
def get_llm_config() -> LLMConfig:
    """Factory function pour obtenir une instance LLMConfig"""
    return LLMConfig()

# Instructions d'installation mises à jour
OLLAMA_SETUP_INSTRUCTIONS = """
=== Configuration Ollama Optimisée pour Agentic Scraper ===

1. Installation de base (requise):
   ollama pull mistral:7b-instruct-v0.2-q4_0    # Modèle principal optimisé (4.1GB)

2. Alternative plus légère:
   ollama pull llama2:7b-chat-q4_0              # Modèle plus rapide (3.8GB)

3. Vérification:
   ollama list                  # Liste des modèles installés
   ollama serve                 # Démarrer le service

4. Test de performance:
   curl -X POST http://localhost:11434/api/generate \\
     -H "Content-Type: application/json" \\
     -d '{"model": "mistral:7b-instruct-v0.2-q4_0", "prompt": "Test", "stream": false}'

Configuration dans .env optimisée:
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=mistral:7b-instruct-v0.2-q4_0
OLLAMA_TIMEOUT=60
OLLAMA_NUM_CTX=3072
OLLAMA_MAX_TOKENS=1500
ENABLE_LLM_ANALYSIS=true
"""