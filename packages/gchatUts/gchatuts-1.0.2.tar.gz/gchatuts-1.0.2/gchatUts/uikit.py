class UiButton:
    def __init__(self,text,url):
        self.text = text
        self.url  = url
    def render(self):
        return {"text": self.text,"onClick": { "openLink": { "url": self.url} }}


class Uikit:
    def section(widgets=[]):
        return {"widgets": widgets }

    def decoratedText(top_label=None,text=None,bottom_label=None,icon_url=None,right_button:UiButton=None):
        base =  {
                "decoratedText": {
                    "topLabel"   : top_label,
                    "text"       : text,
                    "bottomLabel": bottom_label
                    }
                }
        
        if icon_url:
            base["decoratedText"]["startIcon"] = { "iconUrl": icon_url }

        if right_button:
            base["decoratedText"]["button"] = right_button.render()

        return base
    
    def buttonList(buttons:list[UiButton]):
        return  {"buttonList": {"buttons": [btn.render() for btn in buttons]}}

