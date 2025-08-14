from enum import Enum
from app.config.settings import settings

class TunisianSource(Enum):
    BCT = "Banque Centrale de Tunisie"
    INS = "Institut National de Statistique"
    TUNISIE_INDUSTRIE = "Tunisie Industrie"

SOURCE_CONFIG = {
    TunisianSource.BCT: {
        "base_url": "https://www.bct.gov.tn",
        "indicators": {
            "PIB": {
                "path": "/bct/siteprod/actualites.jsp?id=1165",
                "selectors": {
                    "table": "table.data-table",
                    "rows": "tr.data-row",
                    "year": "td.year",
                    "value": "td.value"
                }
            }
        }
    },
    TunisianSource.INS: {
        "base_url": "http://www.ins.tn",
        "indicators": {
            "IPC": {
                "path": "/themes/prix",
                "selectors": {
                    "table": "table.table-indicateurs",
                    "rows": "tbody tr"
                }
            }
        }
    }
}

def get_source_config(source: TunisianSource, indicator: str = None):
    """Retourne la config pour une source et un indicateur donné"""
    config = SOURCE_CONFIG.get(source)
    if indicator:
        return config["indicators"].get(indicator)
    return config