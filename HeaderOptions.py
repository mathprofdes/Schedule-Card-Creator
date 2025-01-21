"""
Options for the header area in the schedule card creator program.

self.Include - boolean to include a header area or not.
self.LeftText - String of text for the left portion of the header.
self.CenterText - String of text for the center portion of the header.
self.RightText - String of text for the right portion of the header.
self.BackgroundColor - QColor background color for the area.
self.TextColor - QColor font color for the area.
self.TextFont - QFont font for the area.

"""

from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt


class HeaderOptions:
    def __init__(self):
        self.Include = True
        self.LeftText = ""
        self.CenterText = ""
        self.RightText = ""
        self.BackgroundColor = QColor(Qt.white)
        self.TextColor = QColor(Qt.black)
        self.TextFont = QFont('Arial', 10)

    def toList(self):
        """
        Creates a list of all data in the class for saving to a file.

        Returns: List of class data.
        """
        retlist = []
        retlist.append(self.Include)
        retlist.append(self.LeftText)
        retlist.append(self.CenterText)
        retlist.append(self.RightText)
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
            self.Include = datalist[0]
            self.LeftText = datalist[1]
            self.CenterText = datalist[2]
            self.RightText = datalist[3]
            self.TextFont.fromString(datalist[4])
            self.BackgroundColor.setRgb(datalist[5])
            self.TextColor.setRgb(datalist[6])
            return True
        except:
            return False
