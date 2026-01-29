import json,os
from gchatUts.uikit import Uikit



class SectionResumo:

    def __init__(self,data_start,hora_start,hora_end,duracao,target):
        self.data_start = data_start
        self.hora_start = hora_start
        self.hora_end = hora_end
        self.duracao = duracao
        self.target = target
    

    def section(self):
        base = json.load(open(os.path.join(os.path.dirname(__file__), 'resumo.json'),'r',encoding="utf-8"))
        periodo = Uikit.decoratedText(
            top_label    = "Período",
            text         = "📅" + self.data_start,
            bottom_label = "Início: {} | Fim: {}".format(self.hora_start,self.hora_end)
            )

        base["widgets"].insert(0,periodo)
        base["widgets"][1]["columns"]["columnItems"][0]["widgets"][0]["decoratedText"]["text"] = f"⏱️ {self.duracao}"
        base["widgets"][1]["columns"]["columnItems"][1]["widgets"][0]["decoratedText"]["text"] = f"🎯 {self.target}"

        return base


