import json,os
from dataclasses import dataclass

@dataclass
class Etapa:
    titulo    :str= None
    icone     :str= None
    id_etapa  :str= None

@dataclass
class ItemEtapa:
    STS_SUCC = "🟩"
    STS_WARN = "🟨"
    STS_DANG = "🟥"
    STS_BLUE = "🟦"
    STS_WHIT = "⬜"
    STS_BLCK = "⬛"
    STS_NOIC = "⠀"

    id_etapa: str
    status   : str

class SectionEtapa:
    etapas = None
    jobs = None

    def __init__(self,etapas:list[Etapa],title="<b>📁 Processo</b>"):
        self.etapas = etapas
        self.jobs = {}
        self.title=title
    
    def add_job(self,descricao,etapas=list[ItemEtapa]):
        self.jobs[descricao] = etapas
    
    def section_legendas(self):
        return {
        "header": "Legenda",
        "widgets": [
            {"decoratedText": {
                "text": " ".join([f"{x.icone}{x.titulo}" for x in self.etapas])
            }
            }
        ]
        }


    def section_etapas(self,job_icon="📑"):
        default_etapa = json.load(open(os.path.join(os.path.dirname(__file__), 'etapa.json'),'r',encoding="utf-8"))

        #TITLE
        default_etapa["widgets"][0]["columns"]["columnItems"][0]["widgets"].append({"decoratedText": {"text": self.title}})
        #TITLE ICONS
        default_etapa["widgets"][0]["columns"]["columnItems"][1]["widgets"].append({"decoratedText": {"text": " ".join([x.icone for x in self.etapas])}})
        
        #ITEMS
        for desc,job_etapas in self.jobs.items():
            default_etapa["widgets"][0]["columns"]["columnItems"][0]["widgets"].append({"decoratedText": {"text": f"{job_icon} {desc}"}})
            
            icn_etapas = []
            for etapa in self.etapas:
                icn = [x.status for x in job_etapas if x.id_etapa == etapa.id_etapa] or [ItemEtapa.STS_NOIC]
                icn_etapas.append(icn[0])

            default_etapa["widgets"][0]["columns"]["columnItems"][1]["widgets"].append({"decoratedText": {"text": " ".join(icn_etapas)}})




        return default_etapa


