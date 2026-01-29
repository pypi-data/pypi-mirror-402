from tkinter import messagebox as m
from tkinter import simpledialog as s


class SGMParentError(Exception):
    pass


class SGMMessageBox:
    def __init__(self, parent):
        try:
            self.p = parent.win
        except AttributeError:
            raise SGMParentError("Invalid parent.")

    def Alert(self, _type: str = "info", message: str = "Message."):
        if _type == "info":
            m.showinfo("-", message, parent=self.p)
        elif _type == "warning":
            m.showwarning("-", message, parent=self.p)
        elif _type == "error":
            m.showerror("-", message, parent=self.p)
        else:
            raise ValueError(f"Unknown alert type: {_type}")


class SGMDialog:
    def __init__(self, parent):
        try:
            self.p = parent.win
        except AttributeError:
            raise SGMParentError("Invalid parent.")

    def Ask(self, _type: str = "string", message: str = "Message."):
        if _type == "string":
            return s.askstring("-", message, parent=self.p)
        elif _type == "integer":
            return s.askinteger("-", message, parent=self.p)
        elif _type == "float":
            return s.askfloat("-", message, parent=self.p)
        else:
            raise ValueError(f"Unknown dialog type: {_type}")
