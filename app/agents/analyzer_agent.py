from typing import Dict, Any
from dataclasses import dataclass
import logging
from datetime import datetime
from app.config.llm_config import LLMConfig
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import json

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Résultat d'une analyse"""
    analysis_id: str
    data_source: str
    analysis_type: str
    insights: Dict[str, Any]
    confidence_score: float
    timestamp: str
    processing_time: float

class AnalyzerAgent:
    """Agent spécialisé dans l'analyse de données"""
    
    def __init__(self, agent_id: str = "analyzer_001"):
        self.agent_id = agent_id
        self.llm_config = LLMConfig()
        self.analysis_history = []
        
    def analyze_scraped_data(self, data: Dict[str, Any]) -> AnalysisResult:
        """Analyser les données scrapées"""
        start_time = datetime.now()
        analysis_id = f"analysis_{int(start_time.timestamp())}"
        
        try:
            analysis_type = data.get("analysis_type", "general")
            content = data.get("result", "") or data.get("content", "")
            
            if analysis_type == "economic":
                insights = self._analyze_economic_data(content)
            elif analysis_type == "company":
                insights = self._analyze_company_data(content)
            elif analysis_type == "news":
                insights = self._analyze_news_data(content)
            else:
                insights = self._analyze_general_data(content)
            
            confidence_score = self._calculate_confidence_score(insights)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = AnalysisResult(
                analysis_id=analysis_id,
                data_source=data.get("query", "unknown"),
                analysis_type=analysis_type,
                insights=insights,
                confidence_score=confidence_score,
                timestamp=datetime.now().isoformat(),
                processing_time=processing_time
            )
            
            self.analysis_history.append(result)
            return result
            
        except Exception as e:
            logger.error(f"Erreur analyse {self.agent_id}: {e}", exc_info=True)
            processing_time = (datetime.now() - start_time).total_seconds()
            return AnalysisResult(
                analysis_id=analysis_id,
                data_source=data.get("query", "unknown"),
                analysis_type=data.get("analysis_type", "general"),
                insights={"error": str(e)},
                confidence_score=0.0,
                timestamp=datetime.now().isoformat(),
                processing_time=processing_time
            )
    
    def _analyze_economic_data(self, content: str) -> Dict[str, Any]:
        llm = self.llm_config.get_analyzer_llm()
        prompt = PromptTemplate(
            input_variables=["content"],
            template="""
            [INST] Analyse les données économiques tunisiennes suivantes :
            {content}

            Structure la réponse en JSON avec :
            - indicateurs_cles (liste)
            - tendances_marquantes (texte)
            - analyse_region (texte)
            - risques (liste)
            - score_urgence (1-5) [/INST]
            """
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        result = chain.run(content=content)
        return self._parse_llm_response(result)
    
    def _analyze_company_data(self, content: str) -> Dict[str, Any]:
        llm = self.llm_config.get_default_llm()
        prompt = PromptTemplate(
            input_variables=["content"],
            template="""
            Analyse les informations d'entreprise suivantes:

            {content}

            Retourne une analyse JSON avec:
            - company_profile: Profil de l'entreprise
            - sector_analysis: Analyse du secteur
            - competitive_position: Position concurrentielle
            - growth_potential: Potentiel de croissance
            - contact_info: Informations de contact si disponibles

            Réponse (JSON uniquement):
            """
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        result = chain.run(content=content)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw_analysis": result}
    
    def _analyze_news_data(self, content: str) -> Dict[str, Any]:
        llm = self.llm_config.get_default_llm()
        prompt = PromptTemplate(
            input_variables=["content"],
            template="""
            Analyse les actualités suivantes:

            {content}

            Retourne une analyse JSON avec:
            - key_events: Événements clés
            - impact_assessment: Évaluation de l'impact
            - stakeholders: Parties prenantes affectées
            - timeline: Chronologie si applicable
            - sentiment: Analyse de sentiment

            Réponse (JSON uniquement):
            """
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        result = chain.run(content=content)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw_analysis": result}
    
    def _analyze_general_data(self, content: str) -> Dict[str, Any]:
        return {
            "content_length": len(content),
            "word_count": len(content.split()),
            "summary": (content[:200] + "...") if len(content) > 200 else content
        }
    
    def _calculate_confidence_score(self, insights: Dict[str, Any]) -> float:
        if "error" in insights:
            return 0.0
        
        factors = []
        content_str = str(insights).lower()

        if len(insights) > 2:
            factors.append(0.3)
        if any(char.isdigit() for char in content_str):
            factors.append(0.2)
        if len(content_str) > 500:
            factors.append(0.2)
        important_keywords = ['analyse', 'données', 'résultat', 'conclusion', 'tendance']
        if any(keyword in content_str for keyword in important_keywords):
            factors.append(0.3)
        
        return min(sum(factors), 1.0)
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse la réponse LLM, tenter un JSON, sinon brut"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning(f"Réponse LLM non JSON parsable: {response[:200]}...")
            return {"raw_response": response}
