"""
A GUI Module by Swaraaj Arora based on tkinter.
Example (Hello, World!):
```python
from sgm import SGMApplication, SGMText
app = SGMApplication(title="Window", resizable=True)
text = SGMText(parent=app, text="Hello, World!", width=25, height=3, size=10)
text.Show()
app.StartLoop()
```
"""

import tkinter as m

_m = None
_c = []

def pkwargs(kwargs, names):
    tr = {}
    for name in names:
        if name in kwargs:
            tr[name] = kwargs[name]
    return tr

class SGMParentError(Exception):
    pass

class SGMApplication():
    def __init__(self, title: str = "sgm", resizable: bool = True):
        global _m
        """
        Main window for SGM.
        
        # Arguments
        
        `title`: Sets the title of the window, defaults to 'sgm'.
        
        `resizable`: Chooses that the window is resizable or not, defaults to True.
        """
        self.win = m.Tk()
        self.app_title = title
        self.APP_RESIZABLE = resizable
        self.win.title(title)
        self.win.resizable(resizable, resizable)
        _m = self.win
        
    def StartLoop(self):
        self.win.mainloop()
        
    def EditProperty(self, **kwargs):
        givenproperties = pkwargs(kwargs, ["background", "width", "height", "resizable", "title"])
        properties = ["background", "width", "height", "resizable", "title"]
        for property in properties:
            if property in givenproperties:
                if property == "background":
                    self.win.config(bg=givenproperties[property])
                elif property == "width":
                    self.win.update_idletasks()          # make sure size info is fresh
                    if self.APP_RESIZABLE:
                        h = self.win.winfo_height()
                        self.win.geometry(f"{givenproperties[property]}x{h}")
                elif property == "height":
                    self.win.update_idletasks()          # make sure size info is fresh
                    if self.APP_RESIZABLE:
                        w = self.win.winfo_width()
                        self.win.geometry(f"{w}x{givenproperties[property]}")
                elif property == "resizable":
                    self.win.resizable(givenproperties[property], givenproperties[property])
                    self.APP_RESIZABLE = givenproperties[property]
                elif property == "title":
                    self.win.title(givenproperties[property])
                    self.APP_TITLE = givenproperties[property]
                    
    def Hide(self) -> None:
        self.win.withdraw()
        
    def UnHide(self) -> None:
        self.win.deiconify()
        
    def Minimize(self) -> None:
        self.win.iconify()
        
    def UnMinimize(self) -> None:
        self.win.deiconify()
        
    def Close(self) -> None:
        self.win.destroy()
        
    def GetProperty(self, property: str) -> str | int | bool:
        if property == "background":
            return self.win.cget("bg")
        elif property == "width":
            self.win.update_idletasks()          # make sure size info is fresh
            if self.APP_RESIZABLE:
                w = self.win.winfo_width()
                return int(w)
        elif property == "height":
            self.win.update_idletasks()          # make sure size info is fresh
            if self.APP_RESIZABLE:
                h = self.win.winfo_height()
                return int(h)
        elif property == "resizable":
            return self.APP_RESIZABLE
        elif property == "title":
            return self.APP_TITLE
                    
    
    def __repr__(self):
        return f"SGMApplication(title='{self.APP_TITLE}', resizable={self.APP_RESIZABLE})"
    

class SGMChildWindow():
    def __init__(self, parent, title: str = "sgm", resizable: bool = True):
        """
        Child window.
        
        :param parent: Parent of window. Note: if parent window closed this window automatically closes.
        :param title: Sets the title of the window
        :type title: str
        :param resizable: Decides if window resizable or not.
        :type resizable: bool
        """
        global _c
        if parent.win == _m:
            self.parent = parent
            self.win = m.Toplevel(self.parent.win)
            _c.append(self.win)
        elif parent in _c:
            self.parent = parent
            self.win = m.Toplevel(self.parent.win)
            _c.append(self.win)
        else:
            raise SGMParentError("Invalid parent object.")
            
        self.app_title = title
        self.APP_RESIZABLE = resizable
        self.win.title(title)
        self.win.resizable(resizable, resizable)
        
        
    def EditProperty(self, **kwargs):
        givenproperties = pkwargs(kwargs, ["background", "width", "height", "resizable", "title"])
        properties = ["background", "width", "height", "resizable", "title"]
        for property in properties:
            if property in givenproperties:
                if property == "background":
                    self.win.config(bg=givenproperties[property])
                elif property == "width":
                    self.win.update_idletasks()          # make sure size info is fresh
                    if self.APP_RESIZABLE:
                        h = self.win.winfo_height()
                        self.win.geometry(f"{givenproperties[property]}x{h}")
                elif property == "height":
                    self.win.update_idletasks()          # make sure size info is fresh
                    if self.APP_RESIZABLE:
                        w = self.win.winfo_width()
                        self.win.geometry(f"{w}x{givenproperties[property]}")
                elif property == "resizable":
                    self.win.resizable(givenproperties[property], givenproperties[property])
                    self.APP_RESIZABLE = givenproperties[property]
                elif property == "title":
                    self.win.title(givenproperties[property])
                    self.APP_TITLE = givenproperties[property]
                    
    def Hide(self) -> None:
        self.win.withdraw()
        
    def UnHide(self) -> None:
        self.win.deiconify()
        
    def Minimize(self) -> None:
        self.win.iconify()
        
    def UnMinimize(self) -> None:
        self.win.deiconify()
        
        
    def Close(self) -> None:
        _c.remove(self.win)
        self.win.destroy()
        
    def GetProperty(self, property: str) -> str | int | bool:
        if property == "background":
            return self.win.cget("bg")
        elif property == "width":
            self.win.update_idletasks()          # make sure size info is fresh
            if self.APP_RESIZABLE:
                w = self.win.winfo_width()
                return int(w)
        elif property == "height":
            self.win.update_idletasks()          # make sure size info is fresh
            if self.APP_RESIZABLE:
                h = self.win.winfo_height()
                return int(h)
        elif property == "resizable":
            return self.APP_RESIZABLE
        elif property == "title":
            return self.APP_TITLE
                    
    
    def __repr__(self):
        return f"SGMChildWindow(parent='{str(self.parent)}', title='{self.APP_TITLE}', resizable={self.APP_RESIZABLE})"
    
class SGMText():
    def __init__(self, parent, text: str = "", width: int = 1, height: int = 1, font: str = "Courier", fontsize: int = 1, bg: str = "white", fg: str = "black"):
        """
        Label widget.
        
        :param parent: Window to build widget in.
        :param text: Text to put in widget.
        :type text: str
        :param width: Width of widget.
        :type width: int
        :param height: Height of widget.
        :type height: int
        :param font: Font of text in widget.
        :type font: str
        :param fontsize: Size of text of font in widget.
        :type fontsize: int
        :param bg: Background.
        :type bg: str
        :param fg: Foreground.
        :type fg: str
        """
        self.valid = False
        
        if parent.win == _m:
            self.valid = True
            self.parent = parent
            self.tkparent = self.parent.win
        elif parent in _c:
            self.valid = True
            self.parent = parent
            self.tkparent = self.parent.win
            
        if not self.valid:
            raise SGMParentError("Invalid parent object.")
            
        self.valid = None
        self.TEXT = text
        self.WIDTH = width
        self.HEIGHT = height
        self.FONT = font
        self.FONTSIZE = fontsize
        self.BG = bg
        self.FG = fg
        
        self.FP = m.Label(master=self.tkparent, text=self.TEXT, width=self.WIDTH, height=self.HEIGHT, font=(self.FONT, self.FONTSIZE), bg=bg, fg=fg)
        
    def Show(self):
        self.FP.pack()
        
    def Show_XY(self, x: int = 0, y: int = 0):
        self.FP.place(x=x, y=y)
        
    def Show_GRID(self, row: int = 0, column: int = 0):
        self.FP.grid(row=row, column=column)
    
    def Destroy(self):
        self.FP.destroy()
        
    def __repr__(self):
        return f"SGMText(parent={self.parent}, text={self.TEXT}, width={self.WIDTH}, height={self.HEIGHT}, font={self.FONT}, fontsize={self.FONTSIZE}, bg={self.BG}, fg={self.FG})"
        
class SGMButton():
    def __init__(self, parent, text: str = "", width: int = 1, height: int = 1, font: str = "Courier", command=lambda: None, fontsize: int = 1, bg: str = "white", fg: str = "black"):
        """
        Label widget.
        
        :param parent: Window to build widget in.
        :param text: Text to put in widget.
        :type text: str
        :param width: Width of widget.
        :type width: int
        :param height: Height of widget.
        :type height: int
        :param font: Font of text in widget.
        :type font: str
        :param fontsize: Size of text of font in widget.
        :type fontsize: int
        :param bg: Background.
        :type bg: str
        :param fg: Foreground.
        :type fg: str
        :param command: Command to execute if button was pressed. Tip: use lambda if command has multiple args.
        
        """
        self.valid = False
        
        if parent.win == _m:
            self.valid = True
            self.parent = parent
            self.tkparent = self.parent.win
        elif parent in _c:
            self.valid = True
            self.parent = parent
            self.tkparent = self.parent.win
            
        if not self.valid:
            raise SGMParentError("Invalid parent object.")
            
        self.valid = None
        self.TEXT = text
        self.WIDTH = width
        self.HEIGHT = height
        self.FONT = font
        self.FONTSIZE = fontsize
        self.COMMAND = command
        self.BG = bg
        self.FG = fg
        
        self.FP = m.Button(master=self.tkparent, bg=bg, fg=fg, command=self.COMMAND, text=self.TEXT, width=self.WIDTH, height=self.HEIGHT, font=(self.FONT, self.FONTSIZE))
        
    def Show(self):
        self.FP.pack()
        
    def Show_XY(self, x: int = 0, y: int = 0):
        self.FP.place(x=x, y=y)
        
    def Show_GRID(self, row: int = 0, column: int = 0):
        self.FP.grid(row=row, column=column)
    
    def Destroy(self):
        self.FP.destroy()
        
    def __repr__(self):
        return f"SGMButton(parent={self.parent}, text={self.TEXT}, width={self.WIDTH}, height={self.HEIGHT}, font={self.FONT}, fontsize={self.FONTSIZE}, bg={self.BG}, fg={self.FG})"
        
class SGMTextInput():
    def __init__(self, parent, width: int = 1, height: int = 1, font: str = "Courier", fontsize: int = 1, bg: str = "white", fg: str = "black"):
        """
        TextInput widget.
        
        :param parent: Window to build widget in.
        :param text: Text to put in widget.
        :type text: str
        :param width: Width of widget.
        :type width: int
        :param height: Height of widget.
        :type height: int
        :param font: Font of text in widget.
        :type font: str
        :param fontsize: Size of text of font in widget.
        :type fontsize: int
        :param bg: Background.
        :type bg: str
        :param fg: Foreground.
        :type fg: str
        """
        self.valid = False
        
        if parent.win == _m:
            self.valid = True
            self.parent = parent
            self.tkparent = self.parent.win
        elif parent in _c:
            self.valid = True
            self.parent = parent
            self.tkparent = self.parent.win
            
        if not self.valid:
            raise SGMParentError("Invalid parent object.")
            
        self.valid = None
        self.WIDTH = width
        self.HEIGHT = height
        self.FONT = font
        self.FONTSIZE = fontsize
        self.BG = bg
        self.FG = fg
        
        self.FP = m.Text(master=self.tkparent, width=self.WIDTH, height=self.HEIGHT, font=(self.FONT, self.FONTSIZE), bg=bg, fg=fg)
        
    def Show(self):
        self.FP.pack()
        
    def Show_XY(self, x: int = 0, y: int = 0):
        self.FP.place(x=x, y=y)
        
    def Show_GRID(self, row: int = 0, column: int = 0):
        self.FP.grid(row=row, column=column)
    
    def Destroy(self):
        self.FP.destroy()
        
    def __repr__(self):
        return f"SGMTextInput(parent={self.parent}, text={self.TEXT}, width={self.WIDTH}, height={self.HEIGHT}, font={self.FONT}, fontsize={self.FONTSIZE}, bg={self.BG}, fg={self.FG})"