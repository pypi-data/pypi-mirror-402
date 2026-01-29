import json,os
from gchatUts.uikit import Uikit



class SectionError:

    def __init__(self,title,text=None):
        self.title = title
        self.text  = text
    

    def section(self):
        text = self.text.replace("\n",'<br>')
        dec_text = Uikit.decoratedText(
            text         = f"<b>{self.title}</b>",
            bottom_label = text,
            icon_url     = "https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/128/emoji_u274c.png"
            )
        base = Uikit.section(widgets=[dec_text])

        return base



