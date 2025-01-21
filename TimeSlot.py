"""
Class structure for defining a slot of time during a week.

self.Days - string of day characters MTWRFSU
self.StartHour - Starting hour for 24 hour clock, 0-23.
self.StartMinute - Starting minute 0-59.
self.EndHour - Ending hour for 24 hour clock, 0-23.
self.EndMinute - Ending minute 0-59.

"""


class TimeSlot:
    def __init__(self):
        self.Days = ""
        self.StartHour = 0
        self.StartMinute = 0
        self.EndHour = 0
        self.EndMinute = 0

    def getDescription(self) -> str:
        """
        Creates and returns a string representation of the timeslot with 12 hour clock.

        Returns: String representation of the timeslot with 12 hour clock.
        """
        sh = self.StartHour
        sm = self.StartMinute
        sampm = "AM"
        eh = self.EndHour
        em = self.EndMinute
        eampm = "AM"
        if sh >= 12:
            sampm = "PM"
        if sh > 12:
            sh -= 12
        if eh >= 12:
            eampm = "PM"
        if eh > 12:
            eh -= 12
        smstr = str(sm)
        emstr = str(em)
        if len(smstr) < 2:
            smstr = "0" + smstr
        if len(emstr) < 2:
            emstr = "0" + emstr

        shstr = str(sh)
        ehstr = str(eh)
        if sh == 0:
            shstr = '12'
        if eh == 0:
            ehstr = '12'

        return self.Days + ' ' + shstr + ':' + smstr + " " + sampm + " - " + \
               ehstr + ':' + emstr + " " + eampm

    def getDescriptionNoDays(self) -> str:
        """
        Creates and returns a string representation of the timeslot with 12 hour clock without
        day designations.

        Returns: String representation of the timeslot with 12 hour clock, no days.
        """
        sh = self.StartHour
        sm = self.StartMinute
        sampm = "AM"
        eh = self.EndHour
        em = self.EndMinute
        eampm = "AM"
        if sh >= 12:
            sampm = "PM"
        if sh > 12:
            sh -= 12
        if eh >= 12:
            eampm = "PM"
        if eh > 12:
            eh -= 12
        smstr = str(sm)
        emstr = str(em)
        if len(smstr) < 2:
            smstr = "0" + smstr
        if len(emstr) < 2:
            emstr = "0" + emstr

        shstr = str(sh)
        ehstr = str(eh)
        if sh == 0:
            shstr = '12'
        if eh == 0:
            ehstr = '12'

        return shstr + ':' + smstr + " " + sampm + " - " + \
               ehstr + ':' + emstr + " " + eampm

    def getDescription24Hr(self) -> str:
        """
        Creates and returns a string representation of the timeslot with 24 hour clock.

        Returns: String representation of the timeslot with 24 hour clock.
        """

        sh = self.StartHour
        sm = self.StartMinute
        eh = self.EndHour
        em = self.EndMinute
        smstr = str(sm)
        emstr = str(em)
        if len(emstr) < 2:
            smstr = "0" + smstr
        if len(emstr) < 2:
            emstr = "0" + emstr
        shstr = str(sh)
        ehstr = str(eh)
        if sh == 0:
            shstr = '12'
        if eh == 0:
            ehstr = '12'

        return self.Days + ' ' + shstr + ':' + smstr + " - " + ehstr + ':' + emstr

    def clean(self):
        """
        Cleans the timeslot so that days are in order and times are adjusted if the minutes are
        over 60.
        """
        cleandays = ""
        self.Days = self.Days.upper().rstrip().lstrip()
        if self.Days.find("M") != -1:
            cleandays += "M"
        if self.Days.find("T") != -1:
            cleandays += "T"
        if self.Days.find("W") != -1:
            cleandays += "W"
        if self.Days.find("R") != -1:
            cleandays += "R"
        if self.Days.find("F") != -1:
            cleandays += "F"
        if self.Days.find("S") != -1:
            cleandays += "S"
        if self.Days.find("U") != -1:
            cleandays += "U"

        self.Days = cleandays
        self.StartHour += self.StartMinute // 60
        self.StartMinute = self.StartMinute % 60
        self.EndHour += self.EndMinute // 60
        self.EndMinute = self.EndMinute % 60

    def isValid(self) -> bool:
        """
        Tests to see if the timeslot is valid.

        Returns: True if the timeslot is valid and False otherwise.
        """
        self.clean()
        if self.StartHour < 0 or self.StartHour > 23:
            return False
        if self.EndHour < 0 or self.EndHour > 23:
            return False

        return True

    def combine(self, time2):
        """
        Combines the current timeslot and the time2 slot if possible.  Combining is done if the
        two timeslots are at the same beginning and ending times, the days are combined, or if
        the two slots are adjacent in time and on the same days then the times are concatenated.

        Parameters: time2 - a second timeslot.

        Returns: A new timeslot that is a combination of the current and time2 if a combination
        can be made and None is no combination can be made.
        """
        self.clean()
        time2.clean()

        if self.timeequals(time2):
            newslot = TimeSlot()
            newslot.setData(self.Days + time2.Days, self.StartHour, self.StartMinute, self.EndHour, self.EndMinute)
            newslot.clean()
            return newslot

        if self.Days == time2.Days:
            okcomb = False
            okcomb = okcomb or self.timeInSlotNoDays(time2.StartHour, time2.StartMinute)
            okcomb = okcomb or self.timeInSlotNoDays(time2.EndHour, time2.EndMinute)
            okcomb = okcomb or time2.timeInSlotNoDays(self.StartHour, self.StartMinute)
            okcomb = okcomb or time2.timeInSlotNoDays(self.EndHour, self.EndMinute)

            if okcomb:
                selfst = self.StartHour * 60 + self.StartMinute
                selfet = self.EndHour * 60 + self.EndMinute
                t2st = time2.StartHour * 60 + time2.StartMinute
                t2et = time2.EndHour * 60 + time2.EndMinute
                if selfst < t2st:
                    newsth = self.StartHour
                    newstm = self.StartMinute
                else:
                    newsth = time2.StartHour
                    newstm = time2.StartMinute

                if selfet > t2et:
                    newseh = self.EndHour
                    newsem = self.EndMinute
                else:
                    newseh = time2.EndHour
                    newsem = time2.EndMinute

                newslot = TimeSlot()
                newslot.setData(self.Days, newsth, newstm, newseh, newsem)
                newslot.clean()
                return newslot

        return None

    def equals(self, time2) -> bool:
        """
        Tests if the current slot and time2 are equal.  Both the days and times must be equal for
        the function to return true.

        Parameters: time2 - timeslot to be tested with the current slot.

        Returns: True if the two timeslots are equal and False otherwise.
        """
        self.clean()
        time2.clean()
        timesequal = True
        if self.Days != time2.Days:
            timesequal = False
        if self.StartHour != time2.StartHour:
            timesequal = False
        if self.StartMinute != time2.StartMinute:
            timesequal = False
        if self.EndHour != time2.EndHour:
            timesequal = False
        if self.EndMinute != time2.EndMinute:
            timesequal = False

        return timesequal

    def timeequals(self, time2) -> bool:
        """
        Tests if the current slot and time2 are equal.  This simply checks if the times are equal for
        the function to return true.

        Parameters: time2 - timeslot to be tested with the current slot.

        Returns: True if the two times of the timeslots are equal and False otherwise.
        """
        self.clean()
        time2.clean()
        timesequal = True
        if self.StartHour != time2.StartHour:
            timesequal = False
        if self.StartMinute != time2.StartMinute:
            timesequal = False
        if self.EndHour != time2.EndHour:
            timesequal = False
        if self.EndMinute != time2.EndMinute:
            timesequal = False

        return timesequal

    def __repr__(self) -> str:
        """
        String representation of the timeslot.
        """
        return "{" + self.getDescription24Hr() + "}"

    def __str__(self) -> str:
        """
        String representation of the timeslot, better for printing.
        """
        return self.getDescription()

    def getFieldList(self) -> []:
        """
        Returns: A list of data stored in the class.
        """
        return [self.Days, self.StartHour, self.StartMinute, self.EndHour, self.EndMinute]

    def setData(self, days: str, bh: int, bm: int, eh: int, em: int):
        """
        Sets the data of the class.
        """
        self.Days = days.upper()
        self.StartHour = bh
        self.StartMinute = bm
        self.EndHour = eh
        self.EndMinute = em

    def getTimeRangeMinutes(self) -> int:
        """
        Returns the number of minutes in the timeslot, days are not included in the calculation.
        """
        hourdif = self.EndHour - self.StartHour
        minutedif = self.EndMinute - self.StartMinute
        dayminutes = hourdif * 60 + minutedif
        return dayminutes

    def getMinutes(self) -> int:
        """
        Returns the number of minutes in the timeslot, days are included in the calculation.
        """
        hourdif = self.EndHour - self.StartHour
        minutedif = self.EndMinute - self.StartMinute
        dayminutes = hourdif * 60 + minutedif
        total = dayminutes * len(self.Days)
        return total

    def timeInSlot(self, d: str, h: int, m: int) -> bool:
        """
        Checks to see if the given day and time are in the current timeslot.

        Parameters:
            d, h, m: Day string (one character day), hour and minute in 24 hour clock.

        Returns: True if the given time is in the current timeslot, False otherwise.
        """
        if d not in self.Days:
            return False

        starttime = self.StartHour * 60 + self.StartMinute
        endtime = self.EndHour * 60 + self.EndMinute
        thistime = h * 60 + m
        return starttime <= thistime <= endtime

    def timeInSlotNoDays(self, h: int, m: int) -> bool:
        """
        Checks to see if the given time is in the current timeslot, no days are checked here.

        Parameters:
            h, m: Hour and minute in 24 hour clock.

        Returns: True if the given time is in the current timeslot, False otherwise.
        """
        starttime = self.StartHour * 60 + self.StartMinute
        endtime = self.EndHour * 60 + self.EndMinute
        thistime = h * 60 + m
        return starttime <= thistime <= endtime

    def timeStrictlyInSlot(self, d: str, h: int, m: int) -> bool:
        """
        Checks to see if the given day and time are strictly in the current timeslot.

        Parameters:
            d, h, m: Day string (one character day), hour and minute in 24 hour clock.

        Returns: True if the given time is strictly inside the current timeslot, False otherwise.
        """
        if d not in self.Days:
            return False

        starttime = self.StartHour * 60 + self.StartMinute
        endtime = self.EndHour * 60 + self.EndMinute
        thistime = h * 60 + m
        return starttime < thistime < endtime

    def overlap(self, timeslot) -> bool:
        """
        Checks if there is overlap between the current timeslot and the parameter timeslot.

        Parameters:
            timeslot - Timeslot to be checked against the current timeslot for overlap.

        Returns: True if the given timeslot overlaps the current timeslot, False otherwise.
        """
        if timeslot is None:
            return False

        retval = False
        for day in timeslot.Days:
            retval = retval or self.timeStrictlyInSlot(day, timeslot.StartHour, timeslot.StartMinute)
            retval = retval or self.timeStrictlyInSlot(day, timeslot.EndHour, timeslot.EndMinute)
            retval = retval or ((day in self.Days) and self.timeequals(timeslot))

        for day in self.Days:
            retval = retval or timeslot.timeStrictlyInSlot(day, self.StartHour, self.StartMinute)
            retval = retval or timeslot.timeStrictlyInSlot(day, self.EndHour, self.EndMinute)
            retval = retval or ((day in timeslot.Days) and self.timeequals(timeslot))

        return retval

    def __lt__(self, rhs):
        """
        Checks if the start time of the current timeslot is less than the start time for the
        rhs timeslot parameter.  Overloaded <.

        Parameters:
            rhs - Timeslot to be checked against the current timeslot.

        Returns: True if the current timeslot is less than the given timeslot, False otherwise.
        """
        sm = self.StartHour * 60 + self.StartMinute
        rhsm = rhs.StartHour * 60 + rhs.StartMinute
        return sm < rhsm
