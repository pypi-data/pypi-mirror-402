# GChat

Biblioteca python para envio de mensagens formatadas via webHook do google chat

## Uso

### Importando a Biblioteca

```python
from gChat import GChat
```

### Criando uma Instância

```python
from gchat import GChat

g = GChat(webhook="SEU_WEB_HOOK")

#CRIA O CARD COM O TITULO E O ICONE APENAS
base_message = g.titled_card(
            title = "NOME DO ROBO",
            icon  = "https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f699.png", #ICONE TDO TITULO
        )

#ENVIA A MENSAGEM SO COM O TITULO
base_message.send()
```
![Base Card](readme_images/base_card.png)


### Envios Simples

```python
from gchat import GChat
from gchat.sections import SectionSuccess,SectionWarn,SectionError

g = GChat(webhook="SEU_WEB_HOOK")

#SESSAO DE SUCESSO
successSection = SectionSuccess(
    title = "A tarefa foi concluída com sucesso.",
    text  = "Todos os processos foram validados."
)

#SESSAO DE ERRO
errorSection = SectionError(
    title = "A tarefa foi concluída com erro.",
    text  = '''Message: no such element: Unable to locate element: {"method":"xpath","selector":"//input[@type="email"]"}
  (Session info: chrome=140.0.7339.186); For documentation on this error, please visit: https://www.selenium.dev/documentation/webdriver/troubleshooting/errors#nosuchelementexception
Stacktrace:
	GetHandleVerifier [0x0x7ff65c5c6b55+79621]
	Get'''
)

#SESSAO WARN
warnSection = SectionWarn(
    title = "A tarefa foi com alertas.",
    text  = "Atençao...."
)
#CRIA O CARD COM O TITULO E O ICONE APENAS
card = g.titled_card(
            title     = "NOME DO ROBO",
            icon      = "https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f699.png", #ICONE TDO TITULO
            sections  = [successSection,errorSection,warnSection] #ADCIONA AS SECOES ABAIXO DO TITULO
        )

card.send()
```

![Logo do Robô](readme_images/card_simples.png)

## Criando Resumo RPA
``` python

from gchat.sections import *
from gchat.uikit import UiButton


#CRIA O RESUMO
sectionResumo = SectionResumo(
            data_start = "23/12/1991",   #DATA DE EXECUCAO
            hora_start = "18:43:02",     #HORA DE INICIO
            hora_end   = "19:20:45",     #HORA DE TERMINO
            duracao    = "00:37:57",     #TEMPO DE EXECUCAO
            target     = f"5 / 10",      #QUANTOS ITENS CONCLUIDOS
)

resume_card = g.titled_card(
            title     = "NOME DO ROBO",
            icon      = "https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f699.png", #ICONE TDO TITULO
            sections=[sectionResumo]
        )

resume_card.send()

```

![Logo do Robô](readme_images/resume_sample.png)

## Exemplos de Texto
```python
from gchat import GChat
from gchat.sections import SectionText

textSection = SectionText(
    title = "Texto Simples", #OPCIONAL
    text  = "Texto de exemplo\nOutro texto\nFim"
)
textSection2 = SectionText(
    text  = "Texto sem titulo"
)
textSection3 = SectionText(
    title = "Texto Simples", #OPCIONAL
    text  = "Texto de exemplo com Icone",
    icon  = "https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f916.png"
)

textSection4 = SectionText(
    title = "Texto Simples", #OPCIONAL
    text  = "Texto de exemplo com Botoes a direita",
    icon  = "https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f916.png",
    right_button = UiButton(text="Google",url="https://www.google.com")
)

textSection5 = SectionText(
    title = "Texto Simples", #OPCIONAL
    text  = "Texto de exemplo com Botoes a baixo",
    icon  = "https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f916.png",
    bottom_buttons= [
        UiButton(text="Google",url="https://www.google.com"),
        UiButton(text="Youtube",url="https://www.youtube.com"),
        ]
)

#CRIA O CARD COM O TITULO E O ICONE APENAS
text_card = g.titled_card(
            title     = "NOME DO ROBO",
            icon      = "https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f699.png", #ICONE TDO TITULO
            sections=[textSection,textSection2,textSection3,textSection4,textSection5]
        )

text_card.send()

```
![Logo do Robô](readme_images/text_samples.png)


## Exemplo de ETAPA
```python
from gchat import GChat
from gchat.sections import SectionEtapa

#CRIA O OBJETO DAS ETAPAS COM A COLUNA DE CADA ETAPA E ATRIBUI UM ID PARA CADA
sectionEtapa = SectionEtapa(
            [
                Etapa(titulo="Azul",icone="✈️",id_etapa="azul"),
                Etapa(titulo="Soma",icone="➕",id_etapa="soma"),
                Etapa(titulo="Susep",icone="🛡️",id_etapa="susep"),
                Etapa(titulo="Upload",icone="⬆️",id_etapa="upload"),
                Etapa(titulo="Elaw",icone="⚖️",id_etapa="elaw")
            ]
        )

#ADCIONA UM ITEM NA LISTA
sectionEtapa.add_job(
                descricao = "NOME DO PROCESSO",
                etapas = [
                    ItemEtapa(id_etapa='azul',   status=ItemEtapa.STS_SUCC ), 
                    ItemEtapa(id_etapa='soma',   status=ItemEtapa.STS_WARN),
                    ItemEtapa(id_etapa='susep',  status=ItemEtapa.STS_DANG),
                    ItemEtapa(id_etapa='upload', status=ItemEtapa.STS_BLUE),
                    ItemEtapa(id_etapa='elaw',   status=ItemEtapa.STS_BLCK) 
                    ]
                )

#CRIA O CARD COM O TITULO E O ICONE APENAS
etapa_card = g.titled_card(
            title     = "NOME DO ROBO",
            icon      = "https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u1f699.png", #ICONE TDO TITULO
            sections=[sectionEtapa]
        )

etapa_card.send()

```

![Logo do Robô](readme_images/etapa_sample.png)