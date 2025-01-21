"""
Options for each style in the schedule card creator program.

self.BackgroundColor - QColor background color for the style.
self.TextColor - QColor font color for the style.
self.TextFont - QFont font for the style text.
self.Justify - int # 0-Left 1-center 2-right  Horizontal justification.
self.Alignment - int # 0-top 1-middle 2-bottom  Vertical justification.
self.Spaced - bool # True=spacing between lines, False=no spacing between the lines.

"""

from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt


class StyleOptions:
    def __init__(self):
        self.BackgroundColor = QColor(Qt.white)
        self.TextColor = QColor(Qt.black)
        self.TextFont = QFont('Arial', 10)
        self.Justify = 1  # 0-Left 1-center 2-right
        self.Alignment = 1  # 0-top 1-middle 2-bottom
        self.Spaced = True  # True=spacing between lines, False=no spacing

    def toList(self):
        """
        Creates a list of all data in the class for saving to a file.

        Returns: List of class data.
        """
        retlist = []
        retlist.append(self.Justify)
        retlist.append(self.Alignment)
        retlist.append(self.Spaced)
        retlist.append(self.TextFont.toString())
        retlist.append(self.BackgroundColor.rgb())
        retlist.append(self.TextColor.rgb())
        return retlist

    def fromList(self, datalist: []):
        """
        Loads the data from the list into the class variables.

        Parameters:
            datalist - list of class data as was returned from toList.
        Returns: True if all data was loaded successfully and False otherwise.
        """
        try:
            self.Justify = datalist[0]
            self.Alignment = datalist[1]
            self.Spaced = datalist[2]
            self.TextFont.fromString(datalist[3])
            self.BackgroundColor.setRgb(datalist[4])
            self.TextColor.setRgb(datalist[5])
            return True
        except:
            return False
