"""
Gestionnaire de stockage intelligent pour les données de scraping
Version simplifiée avec intelligence automatique et gestion d'erreurs robuste
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from app.models.database import ScrapingTask, get_db

logger = logging.getLogger(__name__)

class SmartStorageManager:
    """Gestionnaire de stockage intelligent avec fallbacks automatiques"""
    
    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Configuration intelligente
        self.auto_config = {
            'enable_disk_backup': True,
            'enable_compression': False,
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'retention_days': 30,
            'fallback_enabled': True
        }
        
        logger.info(f"SmartStorageManager initialized: {self.storage_dir}")
    
    def save_scraping_result(self, data: Dict[str, Any], task_id: Optional[str] = None) -> Dict[str, Any]:
        """Sauvegarde intelligente des résultats de scraping"""
        try:
            result = {
                'task_id': task_id,
                'success': False,
                'storage_methods': [],
                'errors': [],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Enrichissement automatique des données
            enriched_data = self._enrich_data(data, task_id)
            
            # Sauvegarde en base de données (prioritaire)
            db_result = self._save_to_database(enriched_data, task_id)
            if db_result['success']:
                result['storage_methods'].append('database')
                result['database_id'] = db_result.get('id')
            else:
                result['errors'].append(f"Database: {db_result['error']}")
            
            # Sauvegarde sur disque (backup)
            if self.auto_config['enable_disk_backup']:
                disk_result = self._save_to_disk(enriched_data, task_id)
                if disk_result['success']:
                    result['storage_methods'].append('disk')
                    result['disk_file'] = disk_result.get('filename')
                else:
                    result['errors'].append(f"Disk: {disk_result['error']}")
            
            # Évaluation du succès global
            result['success'] = len(result['storage_methods']) > 0
            
            if result['success']:
                logger.info(f"Data saved successfully: {result['storage_methods']}")
            else:
                logger.error(f"All storage methods failed: {result['errors']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Storage operation failed: {e}")
            return {
                'success': False,
                'errors': [f"Critical error: {str(e)}"],
                'storage_methods': [],
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _enrich_data(self, data: Dict[str, Any], task_id: Optional[str] = None) -> Dict[str, Any]:
        """Enrichissement automatique des données"""
        try:
            enriched = data.copy()
            
            # Métadonnées de stockage
            enriched.update({
                'storage_metadata': {
                    'task_id': task_id,
                    'storage_timestamp': datetime.utcnow().isoformat(),
                    'storage_version': '2.0_smart',
                    'data_size': len(json.dumps(data, default=str)),
                    'intelligence_features': True
                }
            })
            
            # Normalisation des URLs
            if 'url' in data:
                enriched['normalized_url'] = self._normalize_url(data['url'])
            if 'urls' in data:
                enriched['normalized_urls'] = [self._normalize_url(url) for url in data['urls']]
            
            # Classification automatique du contenu
            if 'content' in data or 'structured_data' in data:
                enriched['content_classification'] = self._classify_content(data)
            
            return enriched
            
        except Exception as e:
            logger.warning(f"Data enrichment failed: {e}")
            return data
    
    def _save_to_database(self, data: Dict[str, Any], task_id: Optional[str] = None) -> Dict[str, Any]:
        """Sauvegarde en base de données avec gestion intelligente"""
        try:
            # Si task_id fourni, mettre à jour la tâche existante
            if task_id:
                return self._update_existing_task(data, task_id)
            else:
                return self._create_new_record(data)
                
        except Exception as e:
            logger.error(f"Database save failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _update_existing_task(self, data: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """Met à jour une tâche existante"""
        try:
            with next(get_db()) as db:
                task = db.query(ScrapingTask).filter(ScrapingTask.task_id == task_id).first()
                
                if task:
                    # Mise à jour intelligente
                    if 'results' in data:
                        task.results = data['results']
                    if 'status' in data:
                        task.status = data['status']
                    if 'metadata' in data:
                        current_metadata = task.metadata_info or {}
                        current_metadata.update(data['metadata'])
                        task.metadata_info = current_metadata
                    
                    task.updated_at = datetime.utcnow()
                    db.commit()
                    
                    return {'success': True, 'id': task.id, 'operation': 'update'}
                else:
                    logger.warning(f"Task {task_id} not found, creating new record")
                    return self._create_new_record(data)
                    
        except Exception as e:
            logger.error(f"Task update failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_new_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouvel enregistrement"""
        try:
            with next(get_db()) as db:
                # Extraction des données principales
                urls = data.get('urls', [data.get('url')] if data.get('url') else [])
                
                new_task = ScrapingTask(
                    urls=urls,
                    results=data.get('results', []),
                    status=data.get('status', 'completed'),
                    metadata_info=data.get('storage_metadata', {}),
                    analysis_type='smart_automatic'
                )
                
                db.add(new_task)
                db.commit()
                db.refresh(new_task)
                
                return {'success': True, 'id': new_task.id, 'operation': 'create'}
                
        except Exception as e:
            logger.error(f"Record creation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save_to_disk(self, data: Dict[str, Any], task_id: Optional[str] = None) -> Dict[str, Any]:
        """Sauvegarde sur disque avec gestion intelligente"""
        try:
            # Génération du nom de fichier intelligent
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            prefix = f"task_{task_id}_" if task_id else "scrape_"
            filename = f"{prefix}{timestamp}.json"
            
            filepath = self.storage_dir / filename
            
            # Vérification de la taille
            data_str = json.dumps(data, default=str, ensure_ascii=False, indent=2)
            if len(data_str.encode('utf-8')) > self.auto_config['max_file_size']:
                # Compression des données si trop grandes
                data_str = json.dumps(data, default=str, ensure_ascii=False, separators=(',', ':'))
                filename = filename.replace('.json', '_compressed.json')
                filepath = self.storage_dir / filename
            
            # Écriture du fichier
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(data_str)
            
            return {
                'success': True,
                'filename': filename,
                'filepath': str(filepath),
                'size': len(data_str.encode('utf-8'))
            }
            
        except Exception as e:
            logger.error(f"Disk save failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _normalize_url(self, url: str) -> str:
        """Normalise une URL pour le stockage"""
        try:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(url.strip())
            # Supprimer les paramètres de session, etc.
            normalized = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, '', ''  # Supprimer query et fragment
            ))
            return normalized
        except Exception:
            return url
    
    def _classify_content(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Classification automatique du contenu"""
        try:
            classification = {
                'primary_type': 'unknown',
                'data_richness': 'low',
                'economic_relevance': 'unknown'
            }
            
            # Analyse du contenu structuré
            structured_data = data.get('structured_data', {})
            if structured_data:
                extracted_values = structured_data.get('extracted_values', {})
                if len(extracted_values) > 10:
                    classification['data_richness'] = 'high'
                elif len(extracted_values) > 3:
                    classification['data_richness'] = 'medium'
                
                # Vérification des indicateurs économiques tunisiens
                target_indicators = sum(1 for v in extracted_values.values() 
                                      if v.get('is_target_indicator', False))
                if target_indicators > 0:
                    classification['economic_relevance'] = 'high'
                elif any('tunisi' in str(v).lower() for v in extracted_values.values()):
                    classification['economic_relevance'] = 'medium'
            
            # Analyse de l'URL source
            urls = data.get('urls', [data.get('url')] if data.get('url') else [])
            for url in urls:
                if url:
                    url_lower = url.lower()
                    if any(gov in url_lower for gov in ['bct.gov.tn', 'ins.tn', '.gov.']):
                        classification['primary_type'] = 'government_official'
                        break
                    elif 'api.' in url_lower or '.json' in url_lower:
                        classification['primary_type'] = 'api_data'
                        break
                    else:
                        classification['primary_type'] = 'web_content'
            
            return classification
            
        except Exception as e:
            logger.warning(f"Content classification failed: {e}")
            return {'primary_type': 'unknown', 'data_richness': 'unknown', 'economic_relevance': 'unknown'}
    
    def load_from_disk(self, filename: str) -> Dict[str, Any]:
        """Charge des données depuis le disque"""
        try:
            filepath = self.storage_dir / filename
            
            if not filepath.exists():
                return {'success': False, 'error': f'File not found: {filename}'}
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                'success': True,
                'data': data,
                'filename': filename,
                'size': filepath.stat().st_size
            }
            
        except Exception as e:
            logger.error(f"Failed to load from disk: {e}")
            return {'success': False, 'error': str(e)}
    
    def cleanup_old_files(self, days: int = None) -> Dict[str, Any]:
        """Nettoyage intelligent des anciens fichiers"""
        try:
            retention_days = days or self.auto_config['retention_days']
            cutoff_date = datetime.utcnow().timestamp() - (retention_days * 24 * 3600)
            
            cleaned_files = []
            total_size_freed = 0
            
            for filepath in self.storage_dir.glob('*.json'):
                if filepath.stat().st_mtime < cutoff_date:
                    file_size = filepath.stat().st_size
                    filepath.unlink()
                    cleaned_files.append(str(filepath.name))
                    total_size_freed += file_size
            
            return {
                'success': True,
                'files_removed': len(cleaned_files),
                'size_freed': total_size_freed,
                'retention_days': retention_days
            }
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Statistiques de stockage intelligentes"""
        try:
            # Statistiques disque
            disk_files = list(self.storage_dir.glob('*.json'))
            total_disk_size = sum(f.stat().st_size for f in disk_files)
            
            # Statistiques base de données
            db_stats = {'total_tasks': 0, 'completed_tasks': 0}
            try:
                with next(get_db()) as db:
                    db_stats['total_tasks'] = db.query(ScrapingTask).count()
                    db_stats['completed_tasks'] = db.query(ScrapingTask).filter(
                        ScrapingTask.status == 'completed'
                    ).count()
            except Exception as e:
                logger.warning(f"Could not get DB stats: {e}")
            
            return {
                'disk_storage': {
                    'files_count': len(disk_files),
                    'total_size': total_disk_size,
                    'storage_dir': str(self.storage_dir)
                },
                'database_storage': db_stats,
                'configuration': self.auto_config,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {'error': str(e)}
    
    def export_data(self, task_id: str, format: str = 'json') -> Dict[str, Any]:
        """Export intelligent des données"""
        try:
            # Récupération depuis la base de données
            with next(get_db()) as db:
                task = db.query(ScrapingTask).filter(ScrapingTask.task_id == task_id).first()
                
                if not task:
                    return {'success': False, 'error': f'Task {task_id} not found'}
                
                # Préparation des données d'export
                export_data = {
                    'task_info': {
                        'task_id': task.task_id,
                        'status': task.status,
                        'created_at': task.created_at.isoformat() if task.created_at else None,
                        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                        'urls': task.urls
                    },
                    'results': task.results or [],
                    'metrics': task.metrics or {},
                    'export_metadata': {
                        'export_timestamp': datetime.utcnow().isoformat(),
                        'export_format': format,
                        'exporter_version': '2.0_smart'
                    }
                }
                
                if format == 'json':
                    filename = f"export_{task_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                    save_result = self._save_to_disk(export_data, f"export_{task_id}")
                    
                    return {
                        'success': save_result['success'],
                        'filename': save_result.get('filename'),
                        'format': format,
                        'data': export_data
                    }
                else:
                    return {'success': False, 'error': f'Format {format} not supported'}
                    
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {'success': False, 'error': str(e)}

# Instance globale pour faciliter l'utilisation
smart_storage = SmartStorageManager()

# Fonctions de compatibilité avec l'ancien système
def save_to_disk(data: Dict[str, Any], filename: str = None) -> str:
    """Fonction de compatibilité pour sauvegarde disque"""
    result = smart_storage._save_to_disk(data, filename)
    return result.get('filename', 'unknown') if result['success'] else None

def save_to_db(data: Dict[str, Any]) -> Optional[int]:
    """Fonction de compatibilité pour sauvegarde DB"""
    result = smart_storage._save_to_database(data)
    return result.get('id') if result['success'] else None

class StorageManager:
    """Classe de compatibilité avec l'ancien système"""
    
    @staticmethod
    def save_to_disk(data: Dict[str, Any], filename: str = None):
        return save_to_disk(data, filename)
    
    @staticmethod
    def save_to_db(data: Dict[str, Any]):
        return save_to_db(data)

# Export des fonctions et classes principales
__all__ = [
    'SmartStorageManager',
    'smart_storage',
    'StorageManager',
    'save_to_disk',
    'save_to_db'
]