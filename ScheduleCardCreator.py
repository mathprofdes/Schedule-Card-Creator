#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created: 7/4/2022
Revised: 6/25/2024

@author: Don Spickler

This program allows the user to create and print out a weekly schedule card.  The card has a header
area for titles, which may be viewed ot not.  There are column headers for the days of the week and
row headers for the hours in use.  The program allows the user to select the time range for the
card.  There are 10 style categories for the items in the schedule, each where the user can define
the background color, font, font color, and text justification properties.  The program offers file
saving and loading, option saving and loading as well as printing and image copy and save.

"""

import pickle
import platform
import sys
import os
import copy
import math
import webbrowser

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import*
from PySide6.QtPrintSupport import *

from CSS_Class import appcss
from GeneralOptions import GeneralOptions
from HeaderOptions import HeaderOptions
from StyleOptions import StyleOptions
from TimeSlot import TimeSlot

# For the Mac OS
os.environ['QT_MAC_WANTS_LAYER'] = '1'


class WeekViewer(QWidget):
    """
    Specialized control for viewing a weekly schedule.  Has mouse tracking to highlight and
    select schedule items.  Incorporates font resizing as well.  The class is not an independent
    structure, although it could be made to be so, its function is closely related to the
    main scheduling program.  Hence it takes a parmaeter to the main appliction in which it calls
    functions from the main in a callback style.
    """

    def __init__(self, parent=None, ma=None):
        super(WeekViewer, self).__init__(parent)
        self.Parent = parent
        self.mainapp = ma

        self.setMouseTracking(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        self.headerHeight = 0
        self.numberDays = 5
        self.timecolwidth = 0
        self.displaysize = QPoint(1, 1)

        self.mousePosition = QPoint(0, 0)
        self.daysofweek = "MTWRFSU"

    def paintCourseRect(self, qp: QPainter, day: str, sh: int, sm: int, eh: int, em: int,
                        text: str, bordercol: QColor, backcol: QColor, textcol: QColor,
                        justify: int, align: int, spacing: bool):
        """
        Paint function used by the main paint function for the widget.  This will paint
        a single rectangle given by timeslot information, colors, and text.

        :param qp: Painter object.
        :param day: String of a single character day.
        :param sh: Starting Hour
        :param sm: Starting Minute
        :param eh: Ending Hour
        :param em: Ending Minute
        :param text: Test to be displayed in the box.
        :param bordercol: Border color for the box.
        :param backcol: Background color for the box.
        :param textcol: Text color.
        :param justify: left, center, or right justification.
        :param align: Top, middle, or bottom placement.
        :param spacing: Include spacing of lines or condence lines.
        """

        # Set positioning on the widget.
        stvpos = math.floor(self.vertPositionAtTime(sh, sm))
        endvpos = math.floor(self.vertPositionAtTime(eh, em))
        colindex = self.daysofweek.find(day)
        colwidth = self.displaysize.x() / self.numberDays
        hpos = math.floor(colindex * colwidth + self.timecolwidth)
        nexthpos = math.floor((colindex + 1) * colwidth + self.timecolwidth)

        # Draw in background color.
        if backcol != None:
            qp.fillRect(hpos, stvpos, nexthpos - hpos, endvpos - stvpos, backcol)

        # Draw in text.
        text = text.rstrip().lstrip()
        if text != "" and textcol != None:
            qp.setPen(textcol)

            # Break string over newline character into separate lines.
            textlines = text.split("\n")
            textlines = [item.rstrip().lstrip() for item in textlines]
            divwidth = (endvpos - stvpos) / len(textlines)

            for line in textlines:
                linenum = textlines.index(line)
                topofspace = stvpos + linenum * divwidth
                fm = QFontMetrics(qp.font())
                fontheight = fm.height()

                # Determine the baseline position given the options.
                baseline = 0
                if align == 0:
                    if spacing:
                        baseline = topofspace + fontheight - fm.descent()
                    else:
                        baseline = stvpos + (linenum + 1) * fontheight - fm.descent()
                elif align == 1:
                    if spacing:
                        baseline = topofspace + divwidth / 2 + fontheight / 2 - fm.descent()
                    else:
                        textstart = ((endvpos - stvpos) - fontheight * len(textlines)) / 2 + stvpos
                        baseline = textstart + (linenum + 1) * fontheight - fm.descent()
                else:
                    if spacing:
                        baseline = topofspace + divwidth - fm.descent()
                    else:
                        baseline = endvpos - fontheight * len(textlines) - fm.descent() + (linenum + 1) * fontheight

                # Determine the horizontal starting position given the options.
                htextstart = 0
                if justify == 0:
                    htextstart = hpos + fm.horizontalAdvance("0")
                elif justify == 1:
                    htextstart = (hpos + nexthpos - fm.horizontalAdvance(line)) / 2
                else:
                    htextstart = nexthpos - fm.horizontalAdvance(line + "0")
                qp.drawText(QPoint(htextstart, baseline), line)

        # Draw in the border
        if bordercol != None:
            qp.setPen(bordercol)
            qp.drawRect(hpos, stvpos, nexthpos - hpos, endvpos - stvpos)

    def paintTimeslot(self, qp: QPainter, timeslot: TimeSlot, text: str,
                      bordercol: QColor, backcol: QColor, textcol: QColor,
                      justify: int, align: int, spacing: bool):
        """
        Paint function used by the main paint function for the widget.  This will call the
        rectangle painter for each day in the list of days in the timeslot.

        :param qp: Painter object.
        :param timeslot: TimeSlot
        :param text: Test to be displayed in the box.
        :param bordercol: Border color for the box.
        :param backcol: Background color for the box.
        :param textcol: Text color.
        :param justify: left, center, or right justification.
        :param align: Top, middle, or bottom placement.
        :param spacing: Include spacing of lines or condence lines.
        """
        for daychar in timeslot.Days:
            self.paintCourseRect(qp, daychar, timeslot.StartHour, timeslot.StartMinute,
                                 timeslot.EndHour, timeslot.EndMinute, text, bordercol,
                                 backcol, textcol, justify, align, spacing)

    def paintEvent(self, event):
        """
        Override of widget paint event.  Creates a weekly view using the data from the main application.
        """
        ww = self.width()
        wh = self.height()
        days = ["Time", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.numberDays = 5

        # Find the number of days to render.
        if len(self.mainapp.schedule) > 0:
            for scheditem in self.mainapp.schedule:
                if ("S" in scheditem[1].Days):
                    self.numberDays = 6
                if ("U" in scheditem[1].Days):
                    self.numberDays = 7

        ###################################
        # Find correct font size for global scaling.
        ###################################

        ResizeMode = self.mainapp.generaloptions.FontResizeMode

        # Save the font sizes of all fonts for resetting after render.  Since Qt objects
        # are all references the update of these in the renderer will alter the sizes.
        oldfontsizes = [self.mainapp.styleoptions[i].TextFont.pointSize() for i in range(10)]
        oldfontsizes.append(self.mainapp.generaloptions.DaysTimesTextFont.pointSize())
        oldfontsizes.append(self.mainapp.headeroptions.TextFont.pointSize())

        # If the auto-resizing is set to global determine the best font size for the render.
        # This is done by increasing the font size by one each iteration and checking if the
        # new font metrics keep the text inside their given space.  Once something is too big
        # the incrementing stops and the font size is found.
        if ResizeMode == 0:
            fontsize = self.mainapp.generaloptions.MinimumFontSize

            fontfits = True
            while fontfits:
                fontsize += 1

                # Set header height and check text widths of header.
                self.headerHeight = 0
                if self.mainapp.headeroptions.Include:
                    font = self.mainapp.headeroptions.TextFont
                    font.setPointSize(fontsize)
                    fm = QFontMetrics(font)
                    fontheight = fm.height()
                    self.headerHeight += 1.5 * fontheight
                    if fm.horizontalAdvance(self.mainapp.headeroptions.CenterText + "00") > ww / 3:
                        fontfits = False
                    if fm.horizontalAdvance(self.mainapp.headeroptions.LeftText + "00") > ww / 3:
                        fontfits = False
                    if fm.horizontalAdvance(self.mainapp.headeroptions.RightText + "00") > ww / 3:
                        fontfits = False

                # Set days and times positions and check text widths of weekdays and times.
                daycolwidth = 0
                if fontfits:
                    font = self.mainapp.generaloptions.DaysTimesTextFont
                    font.setPointSize(fontsize)
                    fm = QFontMetrics(font)
                    fontheight = fm.height()
                    self.headerHeight += 1.5 * fontheight
                    timecolwidth = fm.horizontalAdvance("12:0000")
                    self.displaysize = QPoint(int(ww - timecolwidth), int(wh - self.headerHeight))
                    daycolwidth = self.displaysize.x() / self.numberDays

                    for daytext in days[:self.numberDays + 1]:
                        if fm.horizontalAdvance(daytext + "00") > daycolwidth:
                            fontfits = False

                    starttime = self.mainapp.generaloptions.ScheduleTimeRange.StartHour
                    if self.mainapp.generaloptions.ScheduleTimeRange.StartMinute > 0:
                        starttime += 1
                    endtime = self.mainapp.generaloptions.ScheduleTimeRange.EndHour
                    if (endtime - starttime + 2) * fontheight > self.displaysize.y():
                        fontfits = False

                # Check sizes of schedule items.
                if fontfits:
                    for displayitem in self.mainapp.schedule:
                        font = self.mainapp.styleoptions[displayitem[2]].TextFont
                        font.setPointSize(fontsize)
                        fm = QFontMetrics(font)
                        fontheight = fm.height()

                        itemtext = displayitem[0]
                        itemtextlist = itemtext.split("\n")
                        tw = 0
                        checkfontheight = False
                        for line in itemtextlist:
                            line = line.lstrip().rstrip()
                            if line != "":
                                checkfontheight = True
                            if tw < fm.horizontalAdvance(line + "0"):
                                tw = fm.horizontalAdvance(line + "0")

                        if tw > daycolwidth:
                            fontfits = False

                        if checkfontheight:
                            timeslot = displayitem[1]
                            stvpos = self.vertPositionAtTime(timeslot.StartHour, timeslot.StartMinute)
                            endvpos = self.vertPositionAtTime(timeslot.EndHour, timeslot.EndMinute)
                            if (fontheight * len(itemtextlist) > endvpos - stvpos):
                                fontfits = False

            fontsize -= 1
            fontsize -= self.mainapp.generaloptions.FontSizeAdjustment
            if fontsize < self.mainapp.generaloptions.MinimumFontSize:
                fontsize = self.mainapp.generaloptions.MinimumFontSize
        else:
            fontsize = self.mainapp.generaloptions.MinimumFontSize

        ###################################
        # Render the weekly image.
        ###################################

        qp = QPainter()
        qp.begin(self)

        # Setup widths and heights for use in the layout.

        # Set header height if included.
        self.headerHeight = 0
        if self.mainapp.headeroptions.Include:
            font = self.mainapp.headeroptions.TextFont
            if ResizeMode != 2:
                font.setPointSize(fontsize)
            qp.setFont(font)
            fm = QFontMetrics(font)
            fontheight = fm.height()
            self.headerHeight += 1.5 * fontheight

        font = self.mainapp.generaloptions.DaysTimesTextFont
        if ResizeMode != 2:
            font.setPointSize(fontsize)

        # Set days height and time column width if included.
        qp.setFont(font)
        fm = QFontMetrics(font)
        fontheight = fm.height()
        DaysTimesVPosStart = int(self.headerHeight)
        self.headerHeight += 1.5 * fontheight
        self.headerHeight = int(self.headerHeight)

        self.timecolwidth = fm.horizontalAdvance(days[0] + "00")
        if self.timecolwidth < fm.horizontalAdvance("12:0000"):
            self.timecolwidth = fm.horizontalAdvance("12:0000")

        self.displaysize = QPoint(ww - self.timecolwidth, wh - self.headerHeight)
        colwidth = self.displaysize.x() / self.numberDays

        # Draw background
        qp.fillRect(0, 0, ww, wh, self.mainapp.generaloptions.BackgroundColor)

        # Set the start and end time for the card layout.
        starttime = self.mainapp.generaloptions.ScheduleTimeRange.StartHour
        if self.mainapp.generaloptions.ScheduleTimeRange.StartMinute > 0:
            starttime += 1
        endtime = self.mainapp.generaloptions.ScheduleTimeRange.EndHour

        # Draw in hour markers.
        if self.mainapp.generaloptions.IncludeHourDivisions:
            for i in range(starttime, endtime + 1):
                vpos = self.vertPositionAtTime(i, 0)
                qp.setPen(self.mainapp.generaloptions.HourDivisionColor)
                qp.drawLine(self.timecolwidth, vpos, self.width(), vpos)

        # Draw in schedule items.
        for displayitem in self.mainapp.schedule:
            text = displayitem[0]
            slot = displayitem[1]
            style = self.mainapp.styleoptions[displayitem[2]]
            backcolor = style.BackgroundColor
            boarderColor = self.mainapp.generaloptions.OutlineColor
            textcolor = style.TextColor
            textfont = style.TextFont
            justify = style.Justify
            align = style.Alignment
            spacing = style.Spaced
            oldfontsize = textfont.pointSize()

            if ResizeMode != 2:
                textfont.setPointSize(fontsize)

            qp.setFont(textfont)
            d, h, m = self.timeAtPosition(self.mousePosition.x(), self.mousePosition.y())
            if slot.timeInSlot(d, h, m):
                oldbrush = qp.brush()
                newbrush = QBrush(Qt.DiagCrossPattern)
                newbrush.setColor(QColor(Qt.lightGray))
                qp.setBrush(newbrush)
                newbackcolor = QColor(Qt.white)
                newtextcolor = QColor(Qt.black)
                self.paintTimeslot(qp, slot, text, boarderColor, newbackcolor, newtextcolor,
                                   justify, align, spacing)
                qp.setBrush(oldbrush)
            else:
                self.paintTimeslot(qp, slot, text, boarderColor, backcolor, textcolor,
                                   justify, align, spacing)

            textfont.setPointSize(oldfontsize)

        #############################
        # Draw in headers and times.
        #############################

        qp.fillRect(0, 0, ww, DaysTimesVPosStart, self.mainapp.headeroptions.BackgroundColor)
        qp.fillRect(0, DaysTimesVPosStart, ww, self.headerHeight - DaysTimesVPosStart,
                    self.mainapp.generaloptions.DaysTimesBackgroundColor)
        qp.fillRect(0, DaysTimesVPosStart, self.timecolwidth, wh, self.mainapp.generaloptions.DaysTimesBackgroundColor)
        qp.setPen(self.mainapp.generaloptions.DaysTimesTextColor)

        font = self.mainapp.generaloptions.DaysTimesTextFont
        if ResizeMode != 2:
            font.setPointSize(fontsize)

        qp.setFont(font)
        fm = QFontMetrics(font)

        # Draw in days and times.
        text = days[0]
        w = fm.horizontalAdvance(text)
        hpos = 0.5 * (self.timecolwidth - w)
        qp.drawText(QPoint(hpos, fontheight + DaysTimesVPosStart), text)

        for i in range(1, self.numberDays + 1):
            text = days[i]
            w = fm.horizontalAdvance(text)
            hpos = self.timecolwidth + (i - 1) * colwidth + 0.5 * (colwidth - w)
            qp.drawText(QPoint(hpos, fontheight + DaysTimesVPosStart), text)

        qp.setPen(self.mainapp.generaloptions.OutlineColor)
        for i in range(1, self.numberDays + 1):
            qp.drawLine(self.timecolwidth + i * colwidth, DaysTimesVPosStart, self.timecolwidth + i * colwidth,
                        self.headerHeight)

        # Draw in times on the left.
        for i in range(starttime, endtime + 1):
            vpos = self.vertPositionAtTime(i, 0)
            qp.setPen(self.mainapp.generaloptions.OutlineColor)
            qp.drawLine(0, vpos, self.timecolwidth, vpos)

        qp.setPen(self.mainapp.generaloptions.DaysTimesTextColor)
        for i in range(starttime, endtime + 1):
            if i == 0:
                text = "12:00"
            elif i > 12:
                text = str(i - 12) + ":00"
            else:
                text = str(i) + ":00"

            w = fm.horizontalAdvance(text)
            vpos = self.vertPositionAtTime(i, 0) + fontheight - fm.descent() / 2
            hpos = 0.5 * (self.timecolwidth - w)
            if vpos <= self.height():
                qp.drawText(QPoint(hpos, vpos), text)

        # Draw in header items.
        if self.mainapp.headeroptions.Include:
            qp.setPen(self.mainapp.headeroptions.TextColor)
            font = self.mainapp.headeroptions.TextFont
            if ResizeMode != 2:
                font.setPointSize(fontsize)
            qp.setFont(font)
            fm = QFontMetrics(font)

            vpos = 1.25 * fm.height() - fm.descent()
            onesp = fm.horizontalAdvance("0")
            qp.drawText(QPoint(onesp, vpos), self.mainapp.headeroptions.LeftText)
            qp.drawText(QPoint((ww - fm.horizontalAdvance(self.mainapp.headeroptions.CenterText)) / 2, vpos),
                        self.mainapp.headeroptions.CenterText)
            qp.drawText(QPoint(ww - fm.horizontalAdvance(self.mainapp.headeroptions.RightText) - onesp, vpos),
                        self.mainapp.headeroptions.RightText)

        # Outlines.
        qp.setPen(self.mainapp.generaloptions.OutlineColor)
        qp.drawRect(0, 0, ww - 1, wh - 1)
        qp.drawRect(0, DaysTimesVPosStart, ww - 1, self.headerHeight - DaysTimesVPosStart)
        qp.drawRect(0, 0, ww - 1, DaysTimesVPosStart)
        qp.drawLine(self.timecolwidth, DaysTimesVPosStart, self.timecolwidth, wh)
        for i in range(self.numberDays + 1):
            qp.drawLine(self.timecolwidth + i * colwidth, DaysTimesVPosStart, self.timecolwidth + i * colwidth, wh)

        qp.end()

        # Reset font sizes.
        for i in range(10):
            self.mainapp.styleoptions[i].TextFont.setPointSize(oldfontsizes[i])
        self.mainapp.generaloptions.DaysTimesTextFont.setPointSize(oldfontsizes[10])
        self.mainapp.headeroptions.TextFont.setPointSize(oldfontsizes[11])

    # Convert hours and minutes to minutes.
    def minuteInDay(self, h: int, m: int) -> int:
        return h * 60 + m

    # Calculate the vertical position on the schedule to match the given hours and minute input.
    def vertPositionAtTime(self, h: int, m: int):
        timerange = self.mainapp.generaloptions.ScheduleTimeRange
        daystart = self.minuteInDay(timerange.StartHour, timerange.StartMinute)
        minutes = timerange.getTimeRangeMinutes()
        inputMinutes = self.minuteInDay(h, m)

        vposdec = (inputMinutes - daystart) / minutes
        vpos = vposdec * self.displaysize.y() + self.headerHeight
        return vpos

    # Calculate the time (days, hours, minutes) at the given (x, y) position on the schedule.
    def timeAtPosition(self, x: int, y: int):
        vpos = y - self.headerHeight
        hpos = x - self.timecolwidth
        timerange = self.mainapp.generaloptions.ScheduleTimeRange
        daystart = self.minuteInDay(timerange.StartHour, timerange.StartMinute)
        minutes = timerange.getTimeRangeMinutes()

        timedec = vpos / self.displaysize.y() * minutes + daystart
        hour = int(timedec / 60)
        minute = int(timedec - hour * 60)

        daypos = int(hpos / self.displaysize.x() * self.numberDays)
        if daypos < 0:
            daypos = 0
        elif daypos >= self.numberDays:
            daypos = self.numberDays - 1
        days = ["M", "T", "W", "R", "F", "S", "U"]

        return days[daypos], hour, minute

    # Override for the double click event.
    def mouseDoubleClickEvent(self, e):
        epos = e.position()
        self.mousePosition = QPoint(epos.x(), epos.y())
        d, h, m = self.timeAtPosition(self.mousePosition.x(), self.mousePosition.y())
        self.mainapp.EditItemAt(d, h, m)

    # Override for the mouse pressed event.
    def mousePressEvent(self, e):
        epos = e.position()
        self.mousePosition = QPoint(epos.x(), epos.y())
        self.repaint()

        if e.button() == Qt.LeftButton:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ControlModifier:
                d, h, m = self.timeAtPosition(self.mousePosition.x(), self.mousePosition.y())
                self.mainapp.EditItemAt(d, h, m)

    # Override for the mouse move event.
    def mouseMoveEvent(self, e: QMouseEvent):
        epos = e.position()
        self.mousePosition = QPoint(epos.x(), epos.y())
        self.repaint()

    # Override for the mouse leave event.
    def leaveEvent(self, e: QMouseEvent):
        self.mousePosition = QPoint(-1, -1)
        self.repaint()


class ScheduleListWidget(QListWidget):
    """
    Child class of QListWidget for the list of schedule items.  Functional overrides.
    """

    def __init__(self, parent=None, ma=None):
        super(ScheduleListWidget, self).__init__(parent)
        self.Parent = parent
        self.mainapp = ma

    # Override of the key pressed event.
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.mainapp.DeleteScheduleItem()
        elif event.key() == Qt.Key_Return:
            self.mainapp.updateScheduleItem()
        QListWidget.keyPressEvent(self, event)

    # Override of the mouse double click event.
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mainapp.updateScheduleItem()
        QListWidget.mouseDoubleClickEvent(self, event)


class OptionsTreeWidget(QTreeWidget):
    """
    Child class os the QTreeWidget holding the options.  Functional overrides.
    """

    def __init__(self, parent=None, ma=None):
        super(OptionsTreeWidget, self).__init__(parent)
        self.Parent = parent
        self.mainapp = ma

    # Override of the key pressed event.
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.mainapp.optionsUserUpdate()
        QTreeWidget.keyPressEvent(self, event)

    # Override of the mouse double click event.
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mainapp.optionsUserUpdate()
        QTreeWidget.mouseDoubleClickEvent(self, event)


class ScheduleCardCreator(QMainWindow):
    """
    Main program application window.
    """

    def __init__(self, parent=None):
        super().__init__()

        # About information for the app.
        self.authors = "Don Spickler"
        self.version = "2.4.1"
        self.program_title = "Schedule Card Creator"
        self.copyright = "2025"

        self.licence = "\nThis software is distributed under the GNU General Public License version 3.\n\n" + \
        "This program is free software: you can redistribute it and/or modify it under the terms of the GNU " + \
        "General Public License as published by the Free Software Foundation, either version 3 of the License, " + \
        "or (at your option) any later version. This program is distributed in the hope that it will be useful, " + \
        "but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A " + \
        "PARTICULAR PURPOSE. See the GNU General Public License for more details http://www.gnu.org/licenses/."

        self.Platform = platform.system()
        styles = QStyleFactory.keys()
        if "Fusion" in styles:
            app.setStyle('Fusion')

        self.mainapp = self
        self.Parent = parent
        self.clipboard = QApplication.clipboard()
        self.initializeUI()
        self.loadedFilename = ""

        self.schedule = []  # Schedule item list, form  [[text, timeslot, style], ...]
        self.scheduleUndoRedoList = [[]]  # List of schedule item lists for undo and redo history.
        self.UndoRedoIndex = 0  # Position of the undo/redo index in the list.

        # Option class containers.
        self.generaloptions = GeneralOptions()
        self.headeroptions = HeaderOptions()
        self.styleoptions = []  # [style option 1, style option 2, ..., style option 10]
        for i in range(10):
            self.styleoptions.append(StyleOptions())

        icon = QIcon(self.resource_path("icons/ProgramIcon.png"))
        self.setWindowIcon(icon)

        self.blocktext = "\u2586\u2586\u2586\u2586"
        self.changemade = False
        self.internalHelp = None
        self.initOptions()

    # Adjoin a relative path for icons and help system.
    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    # Updates the title bar to contain the loaded file path if used and an * if a change has been made.
    def updateProgramWindowTitle(self):
        title = self.program_title
        if self.loadedFilename != "":
            title = title + " - " + self.loadedFilename
        if self.changemade:
            title = title + "*"
        self.setWindowTitle(title)

    # Support function to track changes.
    def ChangeMade(self, saved=False, reset=False):
        if saved:
            self.changemade = False
        else:
            self.changemade = True
        self.updateProgramWindowTitle()

    # Adds to or resets the history list udes for undo and redo.
    def ScheduleChangeMade(self, saved=False, reset=False):
        if not reset:
            if self.UndoRedoIndex < len(self.scheduleUndoRedoList) - 1:
                self.scheduleUndoRedoList = self.scheduleUndoRedoList[:self.UndoRedoIndex + 1]

            self.scheduleUndoRedoList.append(copy.deepcopy(self.schedule))
            self.UndoRedoIndex = len(self.scheduleUndoRedoList) - 1
        else:
            self.scheduleUndoRedoList = []
            self.scheduleUndoRedoList.append(copy.deepcopy(self.schedule))
            self.UndoRedoIndex = 0
        self.ChangeMade(saved)

    # Called when the user selects to undo an edit.
    def UndoEdit(self):
        if self.UndoRedoIndex > 0:
            self.UndoRedoIndex -= 1
            self.schedule = copy.deepcopy(self.scheduleUndoRedoList[self.UndoRedoIndex])
            self.updateScheduleItemList()

    # Called when the user selects to redo an edit.
    def RedoEdit(self):
        if self.UndoRedoIndex < len(self.scheduleUndoRedoList) - 1:
            self.UndoRedoIndex += 1
            self.schedule = copy.deepcopy(self.scheduleUndoRedoList[self.UndoRedoIndex])
            self.updateScheduleItemList()

    # Close event override.  Prompts the user if a change has been made and not saved.
    def closeEvent(self, event):
        if self.changemade:
            close = QMessageBox.warning(self, "Exit Program",
                                         "Changes have been made to the schedule and will be lost.  " +
                                         "Are you sure want to exit the program?",
                                         QMessageBox.Yes | QMessageBox.No)
            if close == QMessageBox.Yes:
                event.accept()
                if self.internalHelp:
                    self.internalHelp.close()
            else:
                event.ignore()
        else:
            event.accept()
            if self.internalHelp:
                self.internalHelp.close()

    # Initialize the window, calls create methods to set up the GUI.
    def initializeUI(self):
        self.setMinimumSize(800, 600)
        self.setWindowTitle('Schedule Card Creator')
        icon = QIcon(self.resource_path("icons/ProgramIcon.png"))
        self.setWindowIcon(icon)

        self.createMenu()
        self.createToolBar()
        self.OptionsTree = OptionsTreeWidget(self, self)

        header = self.OptionsTree.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

        self.ScheduleItemsList = ScheduleListWidget(self, self)
        self.WeekView = WeekViewer(self, self)

        weekanditemview = QSplitter(Qt.Vertical)
        weekanditemview.addWidget(self.WeekView)
        weekanditemview.setCollapsible(0, False)
        weekanditemview.addWidget(self.ScheduleItemsList)

        mainview = QSplitter(Qt.Horizontal)
        mainview.setHandleWidth(5)
        mainview.addWidget(self.OptionsTree)
        mainview.addWidget(weekanditemview)

        self.setCentralWidget(mainview)
        self.show()

    # Creates a display string for the specified font.  Used in the options window.
    def createFontString(self, font: QFont) -> str:
        fontstr = font.family() + ", " + str(font.pointSize()) + "pt."
        if font.bold():
            fontstr += ", bold"
        if font.italic():
            fontstr += ", italic"

        return fontstr

    # Initialize the options tree.
    def initOptions(self):
        self.OptionsTree.setMinimumWidth(200)
        self.OptionsTree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.OptionsTree.setColumnCount(2)
        self.OptionsTree.setHeaderLabels(["Option", "Value"])
        self.OptionsTree.header().setMinimumSectionSize(100)
        self.OptionsTree.header().resizeSection(0, 100)
        self.OptionsTree.header().setSectionsMovable(False)

        # General options.
        parent = QTreeWidgetItem(None, ["General", ""])
        ft = parent.font(0)
        ft.setBold(True)
        parent.setFont(0, ft)
        self.OptionsTree.addTopLevelItem(parent)

        timestr = self.generaloptions.ScheduleTimeRange.getDescriptionNoDays()
        child = QTreeWidgetItem(None, ["Time Range", timestr])
        parent.addChild(child)

        child = QTreeWidgetItem(None, ["Background Color", self.blocktext])
        # child.setTextColor(1, self.generaloptions.BackgroundColor)
        child.setForeground(1, QBrush(self.generaloptions.BackgroundColor))
        parent.addChild(child)

        child = QTreeWidgetItem(None, ["Outline Color", self.blocktext])
        # child.setTextColor(1, self.generaloptions.OutlineColor)
        child.setForeground(1, QBrush(self.generaloptions.OutlineColor))
        parent.addChild(child)

        fontresizemodestr = ""
        if self.generaloptions.FontResizeMode == 0:
            fontresizemodestr = "Global"
        elif self.generaloptions.FontResizeMode == 1:
            fontresizemodestr = "Fixed"
        else:
            fontresizemodestr = "Off"

        child = QTreeWidgetItem(None, ["Font Auto-Resize", fontresizemodestr])
        parent.addChild(child)

        fontstr = str(self.generaloptions.MinimumFontSize)
        child = QTreeWidgetItem(None, ["Minimum Font Size", fontstr])
        parent.addChild(child)

        fontstr = str(self.generaloptions.FontSizeAdjustment)
        child = QTreeWidgetItem(None, ["Resize Adjustment", fontstr])
        parent.addChild(child)

        # Days and times options.
        parent = QTreeWidgetItem(None, ["Days & Times", ""])
        ft = parent.font(0)
        ft.setBold(True)
        parent.setFont(0, ft)
        self.OptionsTree.addTopLevelItem(parent)

        child = QTreeWidgetItem(None, ["Background Color", self.blocktext])
        # child.setTextColor(1, self.generaloptions.DaysTimesBackgroundColor)
        child.setForeground(1, QBrush(self.generaloptions.DaysTimesBackgroundColor))
        parent.addChild(child)

        child = QTreeWidgetItem(None, ["Text Color", self.blocktext])
        # child.setTextColor(1, self.generaloptions.DaysTimesTextColor)
        child.setForeground(1, QBrush(self.generaloptions.DaysTimesTextColor))
        parent.addChild(child)

        fontstr = self.createFontString(self.generaloptions.DaysTimesTextFont)
        child = QTreeWidgetItem(None, ["Font", fontstr])
        parent.addChild(child)

        # Hour Divisions options.
        parent = QTreeWidgetItem(None, ["Hour Divisions", ""])
        ft = parent.font(0)
        ft.setBold(True)
        parent.setFont(0, ft)
        self.OptionsTree.addTopLevelItem(parent)

        hourdivisionstr = ""
        if self.generaloptions.IncludeHourDivisions:
            hourdivisionstr = "Yes"
        else:
            hourdivisionstr = "No"

        child = QTreeWidgetItem(None, ["Include", hourdivisionstr])
        parent.addChild(child)

        child = QTreeWidgetItem(None, ["Color", self.blocktext])
        # child.setTextColor(1, self.generaloptions.HourDivisionColor)
        child.setForeground(1, QBrush(self.generaloptions.HourDivisionColor))
        parent.addChild(child)

        # Printing options.
        parent = QTreeWidgetItem(None, ["Printing", ""])
        ft = parent.font(0)
        ft.setBold(True)
        parent.setFont(0, ft)
        self.OptionsTree.addTopLevelItem(parent)

        printsizestr = str(self.generaloptions.PrintDimensions[0]) + " in. X "
        printsizestr += str(self.generaloptions.PrintDimensions[1]) + " in."
        child = QTreeWidgetItem(None, ["Dimensions", printsizestr])
        parent.addChild(child)

        printsizestr = str(self.generaloptions.PrintOffset[0]) + " in. X "
        printsizestr += str(self.generaloptions.PrintOffset[1]) + " in."
        child = QTreeWidgetItem(None, ["Offset", printsizestr])
        parent.addChild(child)

        printscalingstr = ""
        if self.generaloptions.PrintScaling == 0:
            printscalingstr = "None"
        elif self.generaloptions.PrintScaling == 1:
            printscalingstr = "Height to Width"
        else:
            printscalingstr = "Width to Height"
        child = QTreeWidgetItem(None, ["Scaling", printscalingstr])
        parent.addChild(child)

        # Header options.
        parent = QTreeWidgetItem(None, ["Header", ""])
        ft = parent.font(0)
        ft.setBold(True)
        parent.setFont(0, ft)
        self.OptionsTree.addTopLevelItem(parent)

        includeheaderstr = ""
        if self.headeroptions.Include:
            includeheaderstr = "Yes"
        else:
            includeheaderstr = "No"

        child = QTreeWidgetItem(None, ["Include", includeheaderstr])
        parent.addChild(child)

        child = QTreeWidgetItem(None, ["Background Color", self.blocktext])
        # child.setTextColor(1, self.headeroptions.BackgroundColor)
        child.setForeground(1, QBrush(self.headeroptions.BackgroundColor))
        parent.addChild(child)

        child = QTreeWidgetItem(None, ["Text Color", self.blocktext])
        # child.setTextColor(1, self.headeroptions.TextColor)
        child.setForeground(1, QBrush(self.headeroptions.TextColor))
        parent.addChild(child)

        fontstr = self.createFontString(self.headeroptions.TextFont)
        child = QTreeWidgetItem(None, ["Font", fontstr])
        parent.addChild(child)

        child = QTreeWidgetItem(None, ["Left Text", self.headeroptions.LeftText])
        parent.addChild(child)

        child = QTreeWidgetItem(None, ["Center Text", self.headeroptions.CenterText])
        parent.addChild(child)

        child = QTreeWidgetItem(None, ["Right Text", self.headeroptions.RightText])
        parent.addChild(child)

        # Style options.
        for i in range(len(self.styleoptions)):
            style = self.styleoptions[i]
            parent = QTreeWidgetItem(None, ["Style " + str(i + 1), ""])
            ft = parent.font(0)
            ft.setBold(True)
            parent.setFont(0, ft)
            self.OptionsTree.addTopLevelItem(parent)

            child = QTreeWidgetItem(None, ["Background Color", self.blocktext])
            # child.setTextColor(1, style.BackgroundColor)
            child.setForeground(1, QBrush(style.BackgroundColor))
            parent.addChild(child)

            child = QTreeWidgetItem(None, ["Text Color", self.blocktext])
            # child.setTextColor(1, style.TextColor)
            child.setForeground(1, QBrush(style.TextColor))
            parent.addChild(child)

            fontstr = self.createFontString(style.TextFont)
            child = QTreeWidgetItem(None, ["Font", fontstr])
            parent.addChild(child)

            justifystr = ""
            if style.Justify == 0:
                justifystr = "Left"
            elif style.Justify == 1:
                justifystr = "Center"
            else:
                justifystr = "Right"
            child = QTreeWidgetItem(None, ["Justification", justifystr])
            parent.addChild(child)

            alignmentstr = ""
            if style.Alignment == 0:
                alignmentstr = "Top"
            elif style.Alignment == 1:
                alignmentstr = "Middle"
            else:
                alignmentstr = "Bottom"
            child = QTreeWidgetItem(None, ["Alignment", alignmentstr])
            parent.addChild(child)

            spacingstr = ""
            if style.Spaced:
                spacingstr = "Yes"
            else:
                spacingstr = "No"
            child = QTreeWidgetItem(None, ["Spacing", spacingstr])
            parent.addChild(child)

        self.OptionsTree.expandAll()
        self.updateOptions()

    # Updater for the options tree.  These are updated positionally so if a change or addition
    # is made to the options list above, this function will need to be updated as well.
    def updateOptions(self):
        for i in range(self.OptionsTree.topLevelItemCount()):
            topitem = self.OptionsTree.topLevelItem(i)
            topitemstr = topitem.text(0)

            if topitemstr == "General":
                timestr = self.generaloptions.ScheduleTimeRange.getDescriptionNoDays()
                topitem.child(0).setText(1, timestr)
                # topitem.child(1).setTextColor(1, self.generaloptions.BackgroundColor)
                # topitem.child(2).setTextColor(1, self.generaloptions.OutlineColor)

                topitem.child(1).setForeground(1, QBrush(self.generaloptions.BackgroundColor))
                topitem.child(2).setForeground(1, QBrush(self.generaloptions.OutlineColor))

                fontresizemodestr = ""
                if self.generaloptions.FontResizeMode == 0:
                    fontresizemodestr = "Global"
                elif self.generaloptions.FontResizeMode == 1:
                    fontresizemodestr = "Fixed"
                else:
                    fontresizemodestr = "Off"
                topitem.child(3).setText(1, fontresizemodestr)
                topitem.child(4).setText(1, str(self.generaloptions.MinimumFontSize))
                topitem.child(5).setText(1, str(self.generaloptions.FontSizeAdjustment))
            elif topitemstr == "Days & Times":
                # topitem.child(0).setTextColor(1, self.generaloptions.DaysTimesBackgroundColor)
                # topitem.child(1).setTextColor(1, self.generaloptions.DaysTimesTextColor)

                topitem.child(0).setForeground(1, QBrush(self.generaloptions.DaysTimesBackgroundColor))
                topitem.child(1).setForeground(1, QBrush(self.generaloptions.DaysTimesTextColor))

                fontstr = self.createFontString(self.generaloptions.DaysTimesTextFont)
                topitem.child(2).setText(1, fontstr)
            elif topitemstr == "Hour Divisions":
                hourdivisionstr = ""
                if self.generaloptions.IncludeHourDivisions:
                    hourdivisionstr = "Yes"
                else:
                    hourdivisionstr = "No"
                topitem.child(0).setText(1, hourdivisionstr)
                # topitem.child(1).setTextColor(1, self.generaloptions.HourDivisionColor)

                topitem.child(1).setForeground(1, QBrush(self.generaloptions.HourDivisionColor))

            elif topitemstr == "Printing":
                printsizestr = str(self.generaloptions.PrintDimensions[0]) + " in. X "
                printsizestr += str(self.generaloptions.PrintDimensions[1]) + " in."
                topitem.child(0).setText(1, printsizestr)
                printsizestr = str(self.generaloptions.PrintOffset[0]) + " in. X "
                printsizestr += str(self.generaloptions.PrintOffset[1]) + " in."
                topitem.child(1).setText(1, printsizestr)
                printscalingstr = ""
                if self.generaloptions.PrintScaling == 0:
                    printscalingstr = "None"
                elif self.generaloptions.PrintScaling == 1:
                    printscalingstr = "Height to Width"
                else:
                    printscalingstr = "Width to Height"
                topitem.child(2).setText(1, printscalingstr)
            elif topitemstr == "Header":
                includeheaderstr = ""
                if self.headeroptions.Include:
                    includeheaderstr = "Yes"
                else:
                    includeheaderstr = "No"
                topitem.child(0).setText(1, includeheaderstr)
                # topitem.child(1).setTextColor(1, self.headeroptions.BackgroundColor)
                # topitem.child(2).setTextColor(1, self.headeroptions.TextColor)

                topitem.child(1).setForeground(1, QBrush(self.headeroptions.BackgroundColor))
                topitem.child(2).setForeground(1, QBrush(self.headeroptions.TextColor))

                fontstr = self.createFontString(self.headeroptions.TextFont)
                topitem.child(3).setText(1, fontstr)
                topitem.child(4).setText(1, self.headeroptions.LeftText)
                topitem.child(5).setText(1, self.headeroptions.CenterText)
                topitem.child(6).setText(1, self.headeroptions.RightText)
            elif topitemstr.find("Style") > -1:
                index = int(topitem.text(0).split(" ")[1]) - 1
                # topitem.child(0).setTextColor(1, self.styleoptions[index].BackgroundColor)
                # topitem.child(1).setTextColor(1, self.styleoptions[index].TextColor)

                topitem.child(0).setForeground(1, QBrush(self.styleoptions[index].BackgroundColor))
                topitem.child(1).setForeground(1, QBrush(self.styleoptions[index].TextColor))

                fontstr = self.createFontString(self.styleoptions[index].TextFont)
                topitem.child(2).setText(1, fontstr)

                justifystr = ""
                if self.styleoptions[index].Justify == 0:
                    justifystr = "Left"
                elif self.styleoptions[index].Justify == 1:
                    justifystr = "Center"
                else:
                    justifystr = "Right"
                topitem.child(3).setText(1, justifystr)

                alignmentstr = ""
                if self.styleoptions[index].Alignment == 0:
                    alignmentstr = "Top"
                elif self.styleoptions[index].Alignment == 1:
                    alignmentstr = "Middle"
                else:
                    alignmentstr = "Bottom"
                topitem.child(4).setText(1, alignmentstr)

                spacingstr = ""
                if self.styleoptions[index].Spaced:
                    spacingstr = "Yes"
                else:
                    spacingstr = "No"
                topitem.child(5).setText(1, spacingstr)

        self.WeekView.repaint()

    # Finds the selected item in the schedule item list and calls the editor on that item.
    def updateScheduleItem(self):
        items = self.ScheduleItemsList.selectedItems()
        if items:
            item = items[0]
            index = self.ScheduleItemsList.row(item)
            self.updateScheduleItemAt(index)

    # Loads the item at the given index into the schedule item editor.  Replaces the item
    # in the list with the edited item.
    def updateScheduleItemAt(self, index):
        edititem = copy.deepcopy(self.schedule[index])
        dialog = ScheduleItemDialog(self, "Edit Schedule Item", edititem)
        if dialog.exec():
            times = TimeSlot()
            dt = dialog.getTimes()
            times.setData(dialog.getDayString(), dt[0], dt[1], dt[2], dt[3])
            self.schedule[index] = [dialog.getItemText(), times, dialog.getStyleIndex()]
            self.ScheduleChangeMade()
            self.schedule.sort()
            self.updateScheduleItemList()

    # Makes a copy of the currently selected item in the schedule item list.
    def cloneScheduleItem(self):
        items = self.ScheduleItemsList.selectedItems()
        if items:
            item = items[0]
            index = self.ScheduleItemsList.row(item)
            newitem = copy.deepcopy(self.schedule[index])
            self.schedule.append(newitem)
            self.ScheduleChangeMade()
            self.schedule.sort()
            self.updateScheduleItemList()

    # Finds the schedule item at the given day, hour, and minute and invokes the editor.
    def EditItemAt(self, d, h, m):
        i = 0
        index = -1
        for item in self.schedule:
            slot = item[1]
            if slot.timeInSlot(d, h, m):
                index = i
            i += 1

        if index > -1:
            self.updateScheduleItemAt(index)

    # Deletes the currently selected item from the schedule item list.
    def DeleteScheduleItem(self):
        items = self.ScheduleItemsList.selectedItems()
        if items:
            item = items[0]
            index = self.ScheduleItemsList.row(item)
            del self.schedule[index]
            self.ScheduleChangeMade()
            self.schedule.sort()
            self.updateScheduleItemList()

    # Deletes the entrie schedule and resets the undo/redo history.
    def DeleteSchedule(self):
        messagestr = "This will remove the entire schedule, do you wish to remove the schedule?"
        result = QMessageBox.warning(self, "Delete Entire Schedule", messagestr, QMessageBox.Yes | QMessageBox.No)

        if result == QMessageBox.Yes:
            self.schedule = []
            self.ScheduleChangeMade(True, True)
            self.headeroptions.LeftText = ""
            self.headeroptions.RightText = ""
            self.headeroptions.CenterText = ""
            self.updateScheduleItemList()
            self.updateOptions()

    # Function for updating any of the options in the option tree. Takes the currently
    # selected item by name and the name of its parent (category) and invoking the
    # correct dialog box for updating.
    def optionsUserUpdate(self):
        selectedItems = self.OptionsTree.selectedItems()
        # If no selected item, abort.
        if selectedItems == []:
            return

        # If selected item is the category name, abort.
        selectedTreeWidgetItem = selectedItems[0]
        if not selectedTreeWidgetItem.parent():
            return

        categorystr = selectedTreeWidgetItem.parent().text(0)
        optionstr = selectedTreeWidgetItem.text(0)

        if categorystr == "General":
            if optionstr == "Time Range":
                roomtimeselect = TimeRangeDialogInfo(self, "Schedule Time Range", self.generaloptions.ScheduleTimeRange)

                if roomtimeselect.exec():
                    self.ChangeMade()
                    bh, bm, eh, em = roomtimeselect.getTimes()
                    newrange = TimeSlot()
                    newrange.setData("", bh, bm, eh, em)
                    self.generaloptions.ScheduleTimeRange = newrange

            elif optionstr == "Background Color":
                colordialog = QColorDialog(self)
                colordialog.setCurrentColor(self.generaloptions.BackgroundColor)
                if colordialog.exec():
                    self.ChangeMade()
                    color = colordialog.selectedColor()
                    self.generaloptions.BackgroundColor = color
            elif optionstr == "Outline Color":
                colordialog = QColorDialog(self)
                colordialog.setCurrentColor(self.generaloptions.OutlineColor)
                if colordialog.exec():
                    self.ChangeMade()
                    color = colordialog.selectedColor()
                    self.generaloptions.OutlineColor = color
            elif optionstr == "Minimum Font Size":
                self.ChangeMade()
                result = QInputDialog.getInt(self, "Minimum Font Size", "Enter the minimum font size:",
                                             self.generaloptions.MinimumFontSize, 2, 50)
                self.generaloptions.MinimumFontSize = result[0]
            elif optionstr == "Resize Adjustment":
                self.ChangeMade()
                result = QInputDialog.getInt(self, "Font Resize Adjustment", "Enter the font resize adjustment:",
                                             self.generaloptions.FontSizeAdjustment, 0, 50)
                self.generaloptions.FontSizeAdjustment = result[0]
            elif optionstr == "Font Auto-Resize":
                self.ChangeMade()
                self.generaloptions.FontResizeMode = (self.generaloptions.FontResizeMode + 1) % 3

        elif categorystr == "Days & Times":
            if optionstr == "Background Color":
                colordialog = QColorDialog(self)
                colordialog.setCurrentColor(self.generaloptions.DaysTimesBackgroundColor)
                if colordialog.exec():
                    self.ChangeMade()
                    color = colordialog.selectedColor()
                    self.generaloptions.DaysTimesBackgroundColor = color
            elif optionstr == "Text Color":
                colordialog = QColorDialog(self)
                colordialog.setCurrentColor(self.generaloptions.DaysTimesTextColor)
                if colordialog.exec():
                    self.ChangeMade()
                    color = colordialog.selectedColor()
                    self.generaloptions.DaysTimesTextColor = color
            elif optionstr == "Font":
                fontdialog = QFontDialog(self)
                fontdialog.setCurrentFont(self.generaloptions.DaysTimesTextFont)
                if fontdialog.exec():
                    self.ChangeMade()
                    font = fontdialog.selectedFont()
                    self.generaloptions.DaysTimesTextFont = font

        elif categorystr == "Hour Divisions":
            if optionstr == "Include":
                self.ChangeMade()
                self.generaloptions.IncludeHourDivisions = not self.generaloptions.IncludeHourDivisions
            elif optionstr == "Color":
                colordialog = QColorDialog(self)
                colordialog.setCurrentColor(self.generaloptions.HourDivisionColor)
                if colordialog.exec():
                    self.ChangeMade()
                    color = colordialog.selectedColor()
                    self.generaloptions.HourDivisionColor = color

        elif categorystr == "Printing":
            if optionstr == "Dimensions":
                printdimselect = DimensionSelectionDialog(self, "Print Area Dimensions",
                                                          "Input W X H in inches: ",
                                                          self.generaloptions.PrintDimensions[0],
                                                          self.generaloptions.PrintDimensions[1],
                                                          0.01, 100.0, 0.01)

                if printdimselect.exec():
                    self.ChangeMade()
                    w, h = printdimselect.getDimensions()
                    self.generaloptions.PrintDimensions = [w, h]

            elif optionstr == "Offset":
                printdimselect = DimensionSelectionDialog(self, "Print Area Offset",
                                                          "Input H X V offset in inches: ",
                                                          self.generaloptions.PrintOffset[0],
                                                          self.generaloptions.PrintOffset[1],
                                                          0.01, 100.0, 0.01)

                if printdimselect.exec():
                    self.ChangeMade()
                    h, v = printdimselect.getDimensions()
                    self.generaloptions.PrintOffset = [h, v]
            elif optionstr == "Scaling":
                self.ChangeMade()
                self.generaloptions.PrintScaling = (self.generaloptions.PrintScaling + 1) % 3

        elif categorystr == "Header":
            if optionstr == "Include":
                self.ChangeMade()
                self.headeroptions.Include = not self.headeroptions.Include
            elif optionstr == "Background Color":
                colordialog = QColorDialog(self)
                colordialog.setCurrentColor(self.headeroptions.BackgroundColor)
                if colordialog.exec():
                    self.ChangeMade()
                    color = colordialog.selectedColor()
                    self.headeroptions.BackgroundColor = color
            elif optionstr == "Text Color":
                colordialog = QColorDialog(self)
                colordialog.setCurrentColor(self.headeroptions.TextColor)
                if colordialog.exec():
                    self.ChangeMade()
                    color = colordialog.selectedColor()
                    self.headeroptions.TextColor = color
            elif optionstr == "Font":
                fontdialog = QFontDialog(self)
                fontdialog.setCurrentFont(self.headeroptions.TextFont)
                if fontdialog.exec():
                    self.ChangeMade()
                    font = fontdialog.selectedFont()
                    self.headeroptions.TextFont = font
            elif optionstr == "Left Text":
                result = QInputDialog.getText(self, "Left Header Text", "Enter the left header text:",
                                              QLineEdit.Normal, self.headeroptions.LeftText)
                if result[1]:
                    self.ChangeMade()
                    self.headeroptions.LeftText = result[0]
            elif optionstr == "Center Text":
                result = QInputDialog.getText(self, "Center Header Text", "Enter the center header text:",
                                              QLineEdit.Normal, self.headeroptions.CenterText)
                if result[1]:
                    self.ChangeMade()
                    self.headeroptions.CenterText = result[0]
            elif optionstr == "Right Text":
                result = QInputDialog.getText(self, "Right Header Text", "Enter the right header text:",
                                              QLineEdit.Normal, self.headeroptions.RightText)
                if result[1]:
                    self.ChangeMade()
                    self.headeroptions.RightText = result[0]

        elif categorystr.find("Style") > -1:
            index = int(categorystr.split(" ")[1]) - 1
            if optionstr == "Background Color":
                colordialog = QColorDialog(self)
                colordialog.setCurrentColor(self.styleoptions[index].BackgroundColor)
                if colordialog.exec():
                    self.ChangeMade()
                    color = colordialog.selectedColor()
                    self.styleoptions[index].BackgroundColor = color
            elif optionstr == "Text Color":
                colordialog = QColorDialog(self)
                colordialog.setCurrentColor(self.styleoptions[index].TextColor)
                if colordialog.exec():
                    self.ChangeMade()
                    color = colordialog.selectedColor()
                    self.styleoptions[index].TextColor = color
            elif optionstr == "Font":
                fontdialog = QFontDialog(self)
                fontdialog.setCurrentFont(self.styleoptions[index].TextFont)
                if fontdialog.exec():
                    self.ChangeMade()
                    font = fontdialog.selectedFont()
                    self.styleoptions[index].TextFont = font
            elif optionstr == "Justification":
                self.ChangeMade()
                self.styleoptions[index].Justify = (self.styleoptions[index].Justify + 1) % 3
            elif optionstr == "Alignment":
                self.ChangeMade()
                self.styleoptions[index].Alignment = (self.styleoptions[index].Alignment + 1) % 3
            elif optionstr == "Spacing":
                self.ChangeMade()
                self.styleoptions[index].Spaced = not self.styleoptions[index].Spaced

        self.updateOptions()

    # Setup all menu and toolbar actions as well as create the menu.
    def createMenu(self):
        self.file_open_act = QAction(QIcon(self.resource_path('icons/FileOpen.png')), "&Open...", self)
        self.file_open_act.setShortcut('Ctrl+O')
        self.file_open_act.triggered.connect(self.openFile)

        self.file_save_act = QAction(QIcon(self.resource_path('icons/FileSave.png')), "&Save", self)
        self.file_save_act.setShortcut('Ctrl+S')
        self.file_save_act.triggered.connect(self.saveFile)

        self.file_saveas_act = QAction("Save &As...", self)
        self.file_saveas_act.triggered.connect(self.saveFileAs)

        self.file_saveoptionsas_act = QAction("Save Op&tions As...", self)
        self.file_saveoptionsas_act.triggered.connect(self.saveOptionsAs)

        self.file_openoptions_act = QAction("Op&en Options...", self)
        self.file_openoptions_act.triggered.connect(self.openOptions)

        self.printImage_act = QAction(QIcon(self.resource_path('icons/print.png')), "&Print...", self)
        self.printImage_act.setShortcut('Ctrl+P')
        self.printImage_act.triggered.connect(self.printImage)

        self.printPreviewImage_act = QAction(QIcon(self.resource_path('icons/preview.png')), "Print Pre&view...", self)
        self.printPreviewImage_act.triggered.connect(self.printPreviewImage)

        quit_act = QAction("Exit", self)
        quit_act.triggered.connect(self.close)

        # Create edit menu actions
        self.edit_newitem_act = QAction(QIcon(self.resource_path('icons/NewTimeslots.png')),
                                        "&Add New Schedule Item...",
                                        self)
        self.edit_newitem_act.setShortcut('Ctrl+A')
        self.edit_newitem_act.triggered.connect(self.AddNewScheduleItem)

        self.edit_deleteitem_act = QAction(QIcon(self.resource_path('icons/Delete.png')), "&Delete Schedule Item",
                                           self)
        self.edit_deleteitem_act.triggered.connect(self.DeleteScheduleItem)

        self.edit_deleteentireschedule_act = QAction("Delete &Schedule...", self)
        self.edit_deleteentireschedule_act.triggered.connect(self.DeleteSchedule)

        self.edit_edititem_act = QAction(QIcon(self.resource_path('icons/Preferences.png')), "&Edit Schedule Item...",
                                         self)
        self.edit_edititem_act.triggered.connect(self.updateScheduleItem)

        self.edit_cloneitem_act = QAction(QIcon(self.resource_path('icons/Clone.png')), "&Clone Schedule Item", self)
        self.edit_cloneitem_act.triggered.connect(self.cloneScheduleItem)

        self.copyImage_act = QAction(QIcon(self.resource_path('icons/CopyImage.png')), "Copy &Image", self)
        self.copyImage_act.setShortcut('Ctrl+C')
        self.copyImage_act.triggered.connect(self.copyImageToClipboard)

        self.saveImage_act = QAction(QIcon(self.resource_path('icons/CopyImage2.png')), "Save &Image As...", self)
        self.saveImage_act.triggered.connect(self.saveAsImage)

        self.expandOptions_act = QAction(QIcon(self.resource_path('icons/Expand.png')), "Ex&pand Options List", self)
        self.expandOptions_act.triggered.connect(self.expandList)

        self.expandCollapse_act = QAction(QIcon(self.resource_path('icons/Collapse.png')), "Co&llapse Options List",
                                          self)
        self.expandCollapse_act.triggered.connect(self.collapseList)

        self.editUndo = QAction(QIcon(self.resource_path('icons/Undo.png')), "&Undo", self)
        self.editUndo.setShortcut('Ctrl+Z')
        self.editUndo.triggered.connect(self.UndoEdit)

        self.editRedo = QAction(QIcon(self.resource_path('icons/Redo.png')), "&Redo", self)
        self.editRedo.setShortcut('Shift+Ctrl+Z')
        self.editRedo.triggered.connect(self.RedoEdit)

        selectTheme_act = QAction("&Theme...", self)
        selectTheme_act.triggered.connect(self.SelectTheme)

        # Create help menu actions
        self.help_about_act = QAction(QIcon(self.resource_path('icons/About.png')), "&About...", self)
        self.help_about_act.triggered.connect(self.aboutDialog)

        self.help_help_act = QAction(QIcon(self.resource_path('icons/Help2.png')), "&Help...",
                                     self)
        self.help_help_act.triggered.connect(self.onHelp)

        # Create the menu bar
        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False)

        # Create file menu and add actions
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(self.file_open_act)
        file_menu.addAction(self.file_save_act)
        file_menu.addAction(self.file_saveas_act)
        file_menu.addSeparator()
        file_menu.addAction(self.saveImage_act)
        file_menu.addSeparator()
        file_menu.addAction(self.file_openoptions_act)
        file_menu.addAction(self.file_saveoptionsas_act)
        file_menu.addSeparator()
        file_menu.addAction(self.printImage_act)
        file_menu.addAction(self.printPreviewImage_act)
        file_menu.addSeparator()
        file_menu.addAction(quit_act)

        # Create edit menu and add actions
        edit_menu = menu_bar.addMenu('&Edit')
        edit_menu.addAction(self.edit_newitem_act)
        edit_menu.addAction(self.edit_edititem_act)
        edit_menu.addAction(self.edit_cloneitem_act)
        edit_menu.addSeparator()
        edit_menu.addAction(self.edit_deleteitem_act)
        edit_menu.addAction(self.edit_deleteentireschedule_act)
        edit_menu.addSeparator()
        edit_menu.addAction(self.copyImage_act)
        edit_menu.addSeparator()
        edit_menu.addAction(selectTheme_act)
        edit_menu.addSeparator()
        edit_menu.addAction(self.expandOptions_act)
        edit_menu.addAction(self.expandCollapse_act)
        edit_menu.addSeparator()
        edit_menu.addAction(self.editUndo)
        edit_menu.addAction(self.editRedo)

        # Create help menu and add actions
        help_menu = menu_bar.addMenu('&Help')
        help_menu.addAction(self.help_help_act)
        help_menu.addSeparator()
        help_menu.addAction(self.help_about_act)

    # Set up toolbar
    def createToolBar(self):
        tool_bar = QToolBar("Main Toolbar")
        tool_bar.setIconSize(QSize(16, 16))
        self.addToolBar(tool_bar)

        # Add actions to toolbar
        tool_bar.addAction(self.file_open_act)
        tool_bar.addAction(self.file_save_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.edit_newitem_act)
        tool_bar.addAction(self.edit_edititem_act)
        tool_bar.addAction(self.edit_cloneitem_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.copyImage_act)
        tool_bar.addAction(self.saveImage_act)
        tool_bar.addAction(self.printImage_act)
        tool_bar.addAction(self.printPreviewImage_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.editUndo)
        tool_bar.addAction(self.editRedo)
        tool_bar.addSeparator()
        tool_bar.addAction(self.help_help_act)
        tool_bar.addAction(self.help_about_act)

    # Display information about program dialog box
    def aboutDialog(self):
        QMessageBox.about(self, self.program_title + "  Version " + self.version,
                          self.authors + "\nVersion " + self.version +
                          "\nCopyright " + self.copyright +
                          "\nDeveloped in Python using the PySide6 GUI toolset.\n" +
                          self.licence
                          )

    # Open the help system in the systems default browser.
    def onHelp(self):
        self.url_home_string = "file://" + self.resource_path("Help/index.html")
        webbrowser.open(self.url_home_string)

    # Collapse the options tree.
    def collapseList(self):
        self.OptionsTree.collapseAll()

    # Expand the options tree.
    def expandList(self):
        self.OptionsTree.expandAll()

    def SelectTheme(self):
        items = QStyleFactory.keys()
        if len(items) <= 1:
            return

        items.sort()
        item, ok = QInputDialog.getItem(self, "Select Theme", "Available Themes", items, 0, False)

        if ok:
            self.Parent.setStyle(item)

    # Creates a list of information from each of the option classes and schedule.  This
    # is primarily for saving the program data to a file.
    def ListFromDatabases(self, includescheduleitems=True):
        filecontents = []
        filecontents.append(self.generaloptions.toList())
        filecontents.append(self.headeroptions.toList())
        for i in range(10):
            filecontents.append(self.styleoptions[i].toList())

        if includescheduleitems:
            filecontents.append(self.schedule)
        return filecontents

    # Populates each of the option class data and schedule from the given list, as would be created
    # from the ListFromDatabases function.  This is primarily for loading saved data from a
    # file to the program.  Returns True if the loading is successful and false otherwise.
    def DatabasesFromList(self, filecontents: [], includescheduleitems=True):
        try:
            self.generaloptions.fromList(filecontents[0])
            self.headeroptions.fromList(filecontents[1])
            for i in range(10):
                self.styleoptions[i].fromList(filecontents[i + 2])

            if includescheduleitems:
                self.schedule = filecontents[12]

            return True
        except:
            return False

    # Open a binary file containing option and schedule data.
    def openFile(self, file_name=None):
        if self.changemade:
            close = QMessageBox.question(self, "Schedule Changed",
                                         "Changes have been made to the schedule and will be lost when opening a new file.  " +
                                         "Are you sure want to open a new file?",
                                         QMessageBox.Yes | QMessageBox.No)
            if close == QMessageBox.No:
                return

        if not file_name:
            file_name, _ = QFileDialog.getOpenFileName(self, "Open File",
                                                       "", "Schedule Files (*.pas);;All Files (*.*)")

        if file_name:
            tempDatabaseList = self.ListFromDatabases()
            with open(file_name, 'rb') as f:
                try:
                    filecontents = pickle.load(f)
                    if not self.DatabasesFromList(filecontents):
                        self.DatabasesFromList(tempDatabaseList)
                    else:
                        self.loadedFilename = file_name
                        self.updateProgramWindowTitle()
                        self.ScheduleChangeMade(True, True)
                except:
                    self.DatabasesFromList(tempDatabaseList)
                    QMessageBox.warning(self, "File Not Loaded", "The file " + file_name + " could not be loaded.",
                                        QMessageBox.Ok)

            self.updateScheduleItemList()
            self.updateOptions()

    # Saves option and schedule data to a binary file with the given filename (and path).
    def saveDataToFile(self, filename: str = ""):
        if filename == "":
            return

        filecontents = self.ListFromDatabases()
        with open(filename, 'wb') as f:
            try:
                pickle.dump(filecontents, f)
                self.loadedFilename = filename
                self.ScheduleChangeMade(True)
                self.updateProgramWindowTitle()
            except:
                QMessageBox.warning(self, "File Not Saved", "The file " + filename + " could not be saved.",
                                    QMessageBox.Ok)

    # Invokes the save as dialog box to obtain a file name and path for saving and then invokes
    # the saving function.
    def saveFileAs(self):
        dialog = QFileDialog(self)
        dialog.setFilter(dialog.filter() | QDir.Hidden)
        dialog.setDefaultSuffix('pas')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(['Schedule Files (*.pas)'])
        dialog.setWindowTitle('Save As')

        if dialog.exec() == QDialog.Accepted:
            filelist = dialog.selectedFiles()
            if len(filelist) > 0:
                file_name = filelist[0]
                self.saveDataToFile(file_name)

    # If there is a loaded file the function will save the updated information to the
    # same file.  If no filename is present the function will invoke the save as function
    # to obtain a filename.
    def saveFile(self):
        if self.loadedFilename != "":
            self.saveDataToFile(self.loadedFilename)
        else:
            self.saveFileAs()

    # Saves the option information to a file.  No schedule information is saved to these files.
    def saveOptionsAs(self):
        dialog = QFileDialog(self)
        dialog.setFilter(dialog.filter() | QDir.Hidden)
        dialog.setDefaultSuffix('pso')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(['Schedule Options Files (*.pso)'])
        dialog.setWindowTitle('Save Options As')

        file_name = ""
        if dialog.exec() == QDialog.Accepted:
            filelist = dialog.selectedFiles()
            if len(filelist) > 0:
                file_name = filelist[0]

        if file_name == "":
            return

        filecontents = self.ListFromDatabases(False)
        with open(file_name, 'wb') as f:
            try:
                pickle.dump(filecontents, f)
            except:
                QMessageBox.warning(self, "File Not Saved", "The file " + file_name + " could not be saved.",
                                    QMessageBox.Ok)

    # Opens the option information file and loads the option data.
    # No schedule information is altered.
    def openOptions(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File",
                                                   "", "Schedule Options Files (*.pso);;All Files (*.*)")

        if file_name:
            tempDatabaseList = self.ListFromDatabases(False)
            headleft = self.headeroptions.LeftText
            headcenter = self.headeroptions.CenterText
            headright = self.headeroptions.RightText
            with open(file_name, 'rb') as f:
                try:
                    filecontents = pickle.load(f)
                    if not self.DatabasesFromList(filecontents, False):
                        self.DatabasesFromList(tempDatabaseList, False)
                    else:
                        self.headeroptions.LeftText = headleft
                        self.headeroptions.CenterText = headcenter
                        self.headeroptions.RightText = headright
                        self.ChangeMade()
                except:
                    self.DatabasesFromList(tempDatabaseList)
                    QMessageBox.warning(self, "File Not Loaded", "The file " + file_name + " could not be loaded.",
                                        QMessageBox.Ok)

            self.updateOptions()

    # Copies the schedule image to the system clipboard.
    def copyImageToClipboard(self):
        pixmap = QPixmap(self.WeekView.size())
        self.WeekView.render(pixmap)
        self.clipboard.setPixmap(pixmap)

    # Saves the schedule image to an image file.  Defaults to a png file but the file type
    # is determined by the extension on the filename the user selects.
    def saveAsImage(self):
        dialog = QFileDialog(self)
        dialog.setFilter(dialog.filter() | QDir.Hidden)
        dialog.setDefaultSuffix('png')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(['PNG Files (*.png)', 'JPEG Files (*.jpg)', 'Bitmap Files (*.bmp)'])
        dialog.setWindowTitle('Save Image As')

        if dialog.exec() == QDialog.Accepted:
            filelist = dialog.selectedFiles()
            if len(filelist) > 0:
                file_name = filelist[0]
                try:
                    pixmap = QPixmap(self.WeekView.size())
                    self.WeekView.render(pixmap)
                    pixmap.save(file_name)
                except:
                    QMessageBox.warning(self, "File Not Saved", "The file " + file_name + " could not be saved.",
                                        QMessageBox.Ok)

    # Prints the current schedule to the printer using the selected printer options from the
    # options list.  This function does some initial setup, calls the print dialog box for
    # user input, and then calls printPreview which invokes the printing.
    def printImage(self):
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        printer.setDocName("WeeklySchedule")
        leftoffset = self.generaloptions.PrintOffset[0] * 72
        topoffset = self.generaloptions.PrintOffset[0] * 72
        printer.setResolution(300)
        pl = QPageLayout(QPageSize(QPageSize.Letter), QPageLayout.Landscape,
                         QMarginsF(leftoffset, topoffset, 36, 36))
        printer.setPageLayout(pl)
        if dialog.exec() == QDialog.Accepted:
            self.printPreview(printer)

    # Invokes a print preview of the current schedule using the selected printer options from the
    # options list.  This function does some initial setup, calls the print preview dialog box,
    # and then calls printPreview which invokes the printing.
    def printPreviewImage(self):
        printer = QPrinter()
        dialog = QPrintPreviewDialog(printer, self)
        printer.setDocName("WeeklySchedule")
        leftoffset = self.generaloptions.PrintOffset[0] * 72
        topoffset = self.generaloptions.PrintOffset[0] * 72
        printer.setResolution(300)
        pl = QPageLayout(QPageSize(QPageSize.Letter), QPageLayout.Portrait,
                         QMarginsF(leftoffset, topoffset, 36, 36))
        printer.setPageLayout(pl)

        dialog.paintRequested.connect(self.printPreview)
        dialog.exec()

    # This function does the printing by invoking an off-screen version of the WeekViewer and
    # rendering it to a pixmap.  This pixmap is then drawn as an image to the painter object
    # attached to the printer.
    def printPreview(self, printer):
        printviewer = WeekViewer(self, self.mainapp)
        printres = printer.resolution()

        wid = self.generaloptions.PrintDimensions[0] * printres
        hei = self.generaloptions.PrintDimensions[1] * printres

        if self.generaloptions.PrintScaling == 1:
            hei = wid * self.WeekView.height() / self.WeekView.width()
        elif self.generaloptions.PrintScaling == 2:
            wid = hei * self.WeekView.width() / self.WeekView.height()

        oldmode = self.generaloptions.FontResizeMode
        self.generaloptions.FontResizeMode = 0

        printviewer.setFixedSize(QSize(round(wid), round(hei)))
        pixmap = QPixmap(printviewer.size())
        printviewer.render(pixmap)
        painter = QPainter(printer)
        painter.drawPixmap(QPoint(0, 0), pixmap)
        painter.end()

        self.generaloptions.FontResizeMode = oldmode

    # Ending dummy function for print completion.
    def print_completed(self, success):
        pass  # Nothing needs to be done.

    # Resets the schedule item list to match the schedule item data.  If there is time overlaps
    # of items they are drawn in red.
    def updateScheduleItemList(self):
        self.ScheduleItemsList.clear()

        for i in range(len(self.schedule)):
            scheditem = self.schedule[i]
            schstr = ""
            message = scheditem[0].replace("\n", " // ")
            schstr += message + "  |  "
            schstr += scheditem[1].getDescription() + "  |  "
            schstr += "Style " + str(scheditem[2] + 1)
            self.ScheduleItemsList.addItem(schstr)
            overlap = False

            for j in range(len(self.schedule)):
                if i != j:
                    if scheditem[1].overlap(self.schedule[j][1]):
                        overlap = True

            if overlap:
                self.ScheduleItemsList.item(self.ScheduleItemsList.count() - 1).setForeground(Qt.red)

        self.WeekView.repaint()

    # Adds in a new schedule item to the schedule item list using the user-input values from
    # the dialog boxes.
    def AddNewScheduleItem(self):
        dialog = ScheduleItemDialog(self)
        if dialog.exec():
            # self.ChangeMade()
            times = TimeSlot()
            dt = dialog.getTimes()
            times.setData(dialog.getDayString(), dt[0], dt[1], dt[2], dt[3])
            scheditem = [dialog.getItemText(), times, dialog.getStyleIndex()]
            self.schedule.append(scheditem)
            self.ScheduleChangeMade()
            self.schedule.sort()
            self.updateScheduleItemList()


########################################################################
# Dialog box classes for the user input of information.
########################################################################

class GenSeparator(QFrame):
    """
    Simple class that will create a horizontal line divider.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)


class MinuteSpinBox(QSpinBox):
    """
    Special spin box for minute input, 00, 01, ..., 59.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 59)

    def textFromValue(self, value):
        return "%02d" % value


class TimeRangeDialogInfo(QDialog):
    """
    Dialog box for the input of the time range for the schedule card.
    """

    def __init__(self, parent=None, title="Schedule Time Range", timeslot=None):
        super().__init__(parent)
        self.setWindowTitle(title)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        buttonBox.button(QDialogButtonBox.Ok).setAutoDefault(True)
        buttonBox.button(QDialogButtonBox.Ok).setDefault(True)
        buttonBox.button(QDialogButtonBox.Cancel).setAutoDefault(False)
        buttonBox.button(QDialogButtonBox.Cancel).setDefault(False)

        starttimelayout = QHBoxLayout()
        starttimelayout.addWidget(QLabel("Start Time: "))
        self.starthourinput = QSpinBox()
        self.starthourinput.setMinimum(0)
        self.starthourinput.setMaximum(24)
        starttimelayout.addWidget(self.starthourinput)
        starttimelayout.addWidget(QLabel(":"))
        self.startminuteinput = MinuteSpinBox()
        starttimelayout.addWidget(self.startminuteinput)
        starttimelayout.addStretch(0)

        endtimelayout = QHBoxLayout()
        endtimelayout.addWidget(QLabel("End Time: "))
        self.endhourinput = QSpinBox()
        self.endhourinput.setMinimum(0)
        self.endhourinput.setMaximum(24)
        endtimelayout.addWidget(self.endhourinput)
        endtimelayout.addWidget(QLabel(":"))
        self.endminuteinput = MinuteSpinBox()
        endtimelayout.addWidget(self.endminuteinput)
        endtimelayout.addStretch(0)

        timeslayout = QVBoxLayout()
        timeslayout.addLayout(starttimelayout)
        timeslayout.addLayout(endtimelayout)
        timeslayout.addWidget(buttonBox)

        if timeslot:
            self.starthourinput.setValue(timeslot.StartHour)
            self.startminuteinput.setValue(timeslot.StartMinute)
            self.endhourinput.setValue(timeslot.EndHour)
            self.endminuteinput.setValue(timeslot.EndMinute)

        self.setLayout(timeslayout)
        self.adjustSize()
        self.setFixedSize(self.size())

    def getTimes(self) -> [int]:
        sh, sm, eh, em = self.starthourinput.value(), self.startminuteinput.value(), self.endhourinput.value(), self.endminuteinput.value()

        # Swap times if they are out of order.
        if 60 * sh + sm > 60 * eh + em:
            sh, sm, eh, em = eh, em, sh, sm

        return sh, sm, eh, em


class DimensionSelectionDialog(QDialog):
    """
    Dialog for selecting the dimensions and offsets for the printing options.
    """

    def __init__(self, parent=None, title="Dimension Selection", message="Input Dimensions: ", w=0.0, h=0.0, min=0.0,
                 max=1000.0, step=0.01):
        super().__init__(parent)
        self.setWindowTitle(title)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        buttonBox.button(QDialogButtonBox.Ok).setAutoDefault(True)
        buttonBox.button(QDialogButtonBox.Ok).setDefault(True)
        buttonBox.button(QDialogButtonBox.Cancel).setAutoDefault(False)
        buttonBox.button(QDialogButtonBox.Cancel).setDefault(False)

        dimselectlayout = QHBoxLayout()
        dimselectlayout.addWidget(QLabel(message))
        self.Dim1 = QDoubleSpinBox()
        self.Dim1.setMinimum(min)
        self.Dim1.setMaximum(max)
        self.Dim1.setValue(w)
        self.Dim1.setSingleStep(step)
        dimselectlayout.addWidget(self.Dim1)
        dimselectlayout.addWidget(QLabel(" X "))
        self.Dim2 = QDoubleSpinBox()
        self.Dim2.setMinimum(min)
        self.Dim2.setMaximum(max)
        self.Dim2.setValue(h)
        self.Dim2.setSingleStep(step)
        dimselectlayout.addWidget(self.Dim2)

        timeslayout = QVBoxLayout()
        timeslayout.addLayout(dimselectlayout)
        timeslayout.addWidget(buttonBox)

        self.setLayout(timeslayout)
        self.adjustSize()
        self.setFixedSize(self.size())

    def getDimensions(self) -> [int]:
        return self.Dim1.value(), self.Dim2.value()


class ScheduleItemDialog(QDialog):
    """
    Dialog box for input and editing of schedule items.
    """

    def __init__(self, parent=None, title="Add New Schedule Item", edititem=[]):
        super().__init__(parent)
        self.setWindowTitle(title)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        buttonBox.button(QDialogButtonBox.Ok).setAutoDefault(True)
        buttonBox.button(QDialogButtonBox.Ok).setDefault(True)
        buttonBox.button(QDialogButtonBox.Cancel).setAutoDefault(False)
        buttonBox.button(QDialogButtonBox.Cancel).setDefault(False)

        self.StyleSelector = QComboBox()
        for i in range(10):
            self.StyleSelector.addItem(str(i + 1))

        stylelistlayout = QHBoxLayout()
        stylelistlayout.addWidget(QLabel("Style: "))
        stylelistlayout.addWidget(self.StyleSelector)
        stylelistlayout.addStretch(0)

        textlabel = QLabel("Item Text")
        textfont = textlabel.font()
        textfont.setUnderline(True)
        textlabel.setFont(textfont)

        self.itemtext = QTextEdit()
        self.itemtext.setLineWrapMode(QTextEdit.NoWrap)

        textinputlayout = QVBoxLayout()
        textinputlayout.addWidget(GenSeparator())
        textinputlayout.addWidget(textlabel)
        textinputlayout.addWidget(self.itemtext)

        self.MondayCB = QCheckBox("Monday")
        self.TuesdayCB = QCheckBox("Tuesday")
        self.WednesdayCB = QCheckBox("Wednesday")
        self.ThursdayCB = QCheckBox("Thursday")
        self.FridayCB = QCheckBox("Friday")
        self.SaturdayCB = QCheckBox("Saturday")
        self.SundayCB = QCheckBox("Sunday")

        dayslayout = QHBoxLayout()
        daysleftlayout = QVBoxLayout()
        daysleftlayout.addWidget(self.MondayCB)
        daysleftlayout.addWidget(self.WednesdayCB)
        daysleftlayout.addWidget(self.FridayCB)
        daysleftlayout.addWidget(self.SaturdayCB)

        daysrightlayout = QVBoxLayout()
        daysrightlayout.addWidget(self.TuesdayCB)
        daysrightlayout.addWidget(self.ThursdayCB)
        daysrightlayout.addStretch(0)
        daysrightlayout.addWidget(self.SundayCB)

        dayslayout.addLayout(daysleftlayout)
        dayslayout.addLayout(daysrightlayout)

        dayslabel = QLabel("Days")
        daysfont = dayslabel.font()
        daysfont.setUnderline(True)
        dayslabel.setFont(daysfont)

        alldaysleftlayout = QVBoxLayout()
        alldaysleftlayout.addWidget(GenSeparator())
        alldaysleftlayout.addWidget(dayslabel)
        alldaysleftlayout.addLayout(dayslayout)
        alldaysleftlayout.addWidget(GenSeparator())

        timeslabel = QLabel("Times")
        timesfont = timeslabel.font()
        timesfont.setUnderline(True)
        timeslabel.setFont(timesfont)

        starttimelayout = QHBoxLayout()
        starttimelayout.addWidget(QLabel("Start Time: "))
        self.starthourinput = QSpinBox()
        self.starthourinput.setMinimum(0)
        self.starthourinput.setMaximum(23)
        starttimelayout.addWidget(self.starthourinput)
        starttimelayout.addWidget(QLabel(":"))
        self.startminuteinput = MinuteSpinBox()
        starttimelayout.addWidget(self.startminuteinput)
        starttimelayout.addStretch(0)

        endtimelayout = QHBoxLayout()
        endtimelayout.addWidget(QLabel("End Time: "))
        self.endhourinput = QSpinBox()
        self.endhourinput.setMinimum(0)
        self.endhourinput.setMaximum(23)
        endtimelayout.addWidget(self.endhourinput)
        endtimelayout.addWidget(QLabel(":"))
        self.endminuteinput = MinuteSpinBox()
        endtimelayout.addWidget(self.endminuteinput)
        endtimelayout.addStretch(0)

        timeslayout = QVBoxLayout()
        timeslayout.addWidget(timeslabel)
        timeslayout.addLayout(starttimelayout)
        timeslayout.addLayout(endtimelayout)

        if edititem != []:
            self.StyleSelector.setCurrentIndex(edititem[2])
            self.itemtext.setText(edititem[0])
            timeslot = edititem[1]
            self.MondayCB.setChecked("M" in timeslot.Days)
            self.TuesdayCB.setChecked("T" in timeslot.Days)
            self.WednesdayCB.setChecked("W" in timeslot.Days)
            self.ThursdayCB.setChecked("R" in timeslot.Days)
            self.FridayCB.setChecked("F" in timeslot.Days)
            self.SaturdayCB.setChecked("S" in timeslot.Days)
            self.SundayCB.setChecked("U" in timeslot.Days)
            self.starthourinput.setValue(timeslot.StartHour)
            self.startminuteinput.setValue(timeslot.StartMinute)
            self.endhourinput.setValue(timeslot.EndHour)
            self.endminuteinput.setValue(timeslot.EndMinute)

        centerlayout = QVBoxLayout()
        centerlayout.addLayout(stylelistlayout)
        centerlayout.addLayout(textinputlayout)
        centerlayout.addLayout(alldaysleftlayout)
        centerlayout.addLayout(timeslayout)
        centerlayout.addWidget(buttonBox)
        self.setLayout(centerlayout)
        self.adjustSize()
        self.setFixedSize(self.size())

    def getDayString(self) -> str:
        retstr = ""
        if self.MondayCB.isChecked():
            retstr += "M"
        if self.TuesdayCB.isChecked():
            retstr += "T"
        if self.WednesdayCB.isChecked():
            retstr += "W"
        if self.ThursdayCB.isChecked():
            retstr += "R"
        if self.FridayCB.isChecked():
            retstr += "F"
        if self.SaturdayCB.isChecked():
            retstr += "S"
        if self.SundayCB.isChecked():
            retstr += "U"
        return retstr

    def getTimes(self) -> [int]:
        sh, sm, eh, em = self.starthourinput.value(), self.startminuteinput.value(), self.endhourinput.value(), self.endminuteinput.value()

        # Swap times if they are out of order.
        if 60 * sh + sm > 60 * eh + em:
            sh, sm, eh, em = eh, em, sh, sm

        return sh, sm, eh, em

    def getStyleIndex(self) -> int:
        return self.StyleSelector.currentIndex()

    def getItemText(self) -> str:
        return self.itemtext.toPlainText()


if __name__ == '__main__':
    """
    Initiate the program, loads a file from the agument list if one exists. 
    """
    app = QApplication(sys.argv)
    window = ScheduleCardCreator(app)
    progcss = appcss()
    app.setStyleSheet(progcss.getCSS())

    # Load file parameter if one is given.
    if len(sys.argv) > 1:
        window.openFile(sys.argv[1])

    # plat = platform.system()
    # styles = QStyleFactory.keys()
    #
    # if (plat == "Windows") and ("Windows" in styles):
    #     app.setStyle('Windows')
    # if (plat == "Darwin") and ("Windows" in styles):
    #     app.setStyle('Windows')

    # sys.exit(app.exec_())
    sys.exit(app.exec())
