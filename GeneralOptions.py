"""
Options for the schedule card creator program.

self.IncludeHourDivisions - boolean for the inclusion of lines at each hour.
self.BackgroundColor - QColor background color for the schedule item area.
self.DaysTimesBackgroundColor - QColor background color for the days and times area.
self.DaysTimesTextColor - QColor font color for the days and times text.
self.DaysTimesTextFont - QFont font for the days and times text.
self.MinimumFontSize - Starting size for fonts in auto-resize mode, the actual font size in fixed mode.
self.FontSizeAdjustment - Points to decrease the automatic resizing.
self.OutlineColor - QColor color of the outline and day division lines.
self.HourDivisionColor - QColor color of the division lines at each hour.
self.ScheduleTimeRange - TimeSlot the start and end times for the schedule card.
self.PrintDimensions - list of floats, dimensions of the printed image in inches.
self.PrintOffset  - list of floats, amount of printing offset from the upper left corner of the printed image.
self.PrintScaling - int # 0-None 1-Scale height to width, 2-Scale width to height
                    None uses the dimensions given in the PrintDimensions.
                    Scale height to width, will change the height to match the width and the aspect ratio of the screen image.
                    Scale width to height, will change the width to match the height and the aspect ratio of the screen image.
self.FontResizeMode - int # 0-global 1-fixed, 2-none
                    Global will automatically scale all fonts equally to best fit the space available.
                        This is the default mode of the program and the images are best in this mode.
                    Fixed will set all fonts to the MinimumFontSize.
                    None will use the font sizes fron the font selections.
                    Note that printing will use Global mode regardless of this setting.
"""

from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt

from TimeSlot import TimeSlot


class GeneralOptions:
    def __init__(self):
        self.IncludeHourDivisions = True
        self.BackgroundColor = QColor(Qt.white)
        self.DaysTimesBackgroundColor = QColor()
        self.DaysTimesBackgroundColor.setRgb(240, 240, 240)
        self.DaysTimesTextColor = QColor(Qt.black)
        self.DaysTimesTextFont = QFont('Arial', 10)
        self.MinimumFontSize = 8
        self.FontSizeAdjustment = 0
        self.OutlineColor = QColor(Qt.black)
        self.HourDivisionColor = QColor()
        self.HourDivisionColor.setRgb(240, 240, 240)
        self.ScheduleTimeRange = TimeSlot()
        self.PrintDimensions = [7.5, 4.75]
        self.PrintOffset = [0.5, 0.5]
        self.PrintScaling = 0  # 0-None 1-scale height to Width, 2-Scale width to height
        self.FontResizeMode = 0  # 0-global 1-fixed, 2-none

        self.ScheduleTimeRange.setData("", 8, 0, 18, 0)  # 8 AM to 6 PM

    def toList(self) -> []:
        """
        Creates a list of all data in the class for saving to a file.

        Returns: List of class data.
        """
        retlist = []
        retlist.append(self.IncludeHourDivisions)
        retlist.append(self.BackgroundColor.rgb())
        retlist.append(self.DaysTimesBackgroundColor.rgb())
        retlist.append(self.DaysTimesTextColor.rgb())
        retlist.append(self.DaysTimesTextFont.toString())
        retlist.append(self.MinimumFontSize)
        retlist.append(self.FontSizeAdjustment)
        retlist.append(self.OutlineColor.rgb())
        retlist.append(self.HourDivisionColor.rgb())
        retlist.append(self.ScheduleTimeRange)
        retlist.append(self.PrintDimensions)
        retlist.append(self.PrintOffset)
        retlist.append(self.PrintScaling)
        retlist.append(self.FontResizeMode)
        return retlist

    def fromList(self, datalist: []) -> bool:
        """
        Loads the data from the list into the class variables.

        Parameters:
            datalist - list of class data as was returned from toList.
        Returns: True if all data was loaded successfully and False otherwise.
        """
        try:
            self.IncludeHourDivisions = datalist[0]
            self.BackgroundColor.setRgb(datalist[1])
            self.DaysTimesBackgroundColor.setRgb(datalist[2])
            self.DaysTimesTextColor.setRgb(datalist[3])
            self.DaysTimesTextFont.fromString(datalist[4])
            self.MinimumFontSize = datalist[5]
            self.FontSizeAdjustment = datalist[6]
            self.OutlineColor.setRgb(datalist[7])
            self.HourDivisionColor.setRgb(datalist[8])
            self.ScheduleTimeRange = datalist[9]
            self.PrintDimensions = datalist[10]
            self.PrintOffset = datalist[11]
            self.PrintScaling = datalist[12]
            self.FontResizeMode = datalist[13]
            return True
        except:
            return False
