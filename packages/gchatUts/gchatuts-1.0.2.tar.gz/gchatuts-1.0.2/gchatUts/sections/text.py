import json,os
from gchatUts.uikit import Uikit, UiButton



class SectionText:

    def __init__(self,title=None,text=None,icon=None,right_button:UiButton=None,bottom_buttons:list[UiButton]=None):
        self.title          = title
        self.text           = text
        self.icon           = icon
        self.right_button   = right_button
        self.bottom_buttons = bottom_buttons
    

    def section(self):
        widgets = []
        text = self.text.replace("\n",'<br>')
        widgets.append(Uikit.decoratedText(
            text         = self.title,
            bottom_label = text,
            icon_url     = self.icon,
            right_button = self.right_button
            )
        )
        if self.bottom_buttons:
            widgets.append(Uikit.buttonList(buttons = self.bottom_buttons))

        base = Uikit.section(widgets=widgets)

        return base


