from PyQt6.QtGui import QValidator
from PyQt6.QtWidgets import QSpinBox


class QSpinHex(QSpinBox):
    def __init__(self):
        QSpinBox.__init__(self)

    def valueFromText(self, val: str) ->int:
        return int(val, 16)

    def textFromValue(self, val: int)->str:
        return "0x{:02X}".format(val)

    def validate(self, val:str, cursor_pos:int) -> (QValidator.State, str,int):
        try:
            int(val,16)
            if len(val) == 4:
                validation = QValidator.State.Acceptable
            else:
                validation = QValidator.State.Intermediate
        except ValueError:
            if val[0:2] == "0x" and len(val) in (2,3,4):
                validation= QValidator.State.Intermediate
            else:
                validation = QValidator.State.Invalid
        #hex_letter_list = ('A', 'a', 'B','b', 'C','c', 'D','d', 'E','e', 'F','f')
        return validation, val, cursor_pos
