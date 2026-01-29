import requests
from datetime import datetime
from typing import Dict, Any
from .sections.etapa import SectionEtapa
import json,os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GCard:
    sections = None
    
    def __init__(self,webhook,headers,message_json):
        self.webhook      = webhook
        self.headers      = headers
        self.message_json = message_json

    def send(self,replaces=[]):   #[("{body}","meu conteudo!")]
        payload = json.dumps(self.message_json)
        for rp in replaces:
            payload = payload.replace(rp[0],rp[1])

        payload = json.loads(payload)

        response = requests.post(self.webhook, json=payload, headers=self.headers, timeout=30, verify=False)


class GChat:
    def __init__(self, webhook: str):
        self.webhook = webhook
        self.headers = {"Content-Type": "application/json; charset=UTF-8"}
    
    def titled_card(self,title, icon, sections = []):
        default_data = json.load(open(os.path.join(os.path.dirname(__file__), 'default.json'),'r',encoding="utf-8"))

        default_data["cardsV2"][0]["card"]["header"]["title"] = title
        default_data["cardsV2"][0]["card"]["header"]["imageUrl"] = icon

        for section in sections:
            if isinstance(section,SectionEtapa):
                legendas = section.section_legendas()
                etapas = section.section_etapas()
                default_data["cardsV2"][0]["card"]["sections"].append(legendas)
                default_data["cardsV2"][0]["card"]["sections"].append(etapas)
            else:
                default_data["cardsV2"][0]["card"]["sections"].append(section.section())

        return GCard(self.webhook,self.headers,default_data)
