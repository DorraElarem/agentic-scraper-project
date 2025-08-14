import logging
from langchain_community.llms import Ollama

# Activez les logs pour debug
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ollama():
    try:
        logger.info("Création du client Ollama...")
        llm = Ollama(
            model="llama2",
            base_url="http://localhost:11434",
            timeout=30  # 30 secondes max
        )
        
        logger.info("Envoi de la requête...")
        response = llm.invoke("Explique le scraping web en une phrase")
        
        print("\nRéponse reçue:")
        print(response)
        
    except Exception as e:
        logger.error(f"Échec : {str(e)}")
        if "timeout" in str(e).lower():
            print("\n⇒ Conseil : Essayez avec un prompt plus court ou augmentez timeout=60")

if __name__ == "__main__":
    test_ollama()