
# minilineplot.py is a single module producing an SVG image of a chart with one or more plotted lines.
#
# Intended to be as simple as possible, with no dependencies.
#
# The chart has a left vertical axis and a bottom horizontal axis, grid lines are possible,
#
# Two classes are defined.
#
# Line, containg x,y points which creates a line to be plotted 
#
# Axis which creates the axis, and to which Line objects can be added.
#
# The Axis class has methods to create an svg string suitable for embedding in an html document
# it can also create an svg image, either as a bytes object, or saved to a file.


from dataclasses import dataclass, field
import xml.etree.ElementTree as ET

import decimal, time

D = decimal.Decimal


def _brkt(vmax, vmin):
    "Bracket vmax and vmin"
    vdmax = D(vmax)
    vdmin = D(vmin)
    span = vdmax - vdmin
    spanplus = span + span/D(4)  # increase span by 25%
    if vdmin > D(0) and vdmax < spanplus:
        # vdmin is positive and close to zero, so prefer it to be zero
        bot = D(0)
        for prec in range(1, 20):
            ctx = decimal.Context(prec=prec)
            top = ctx.next_plus(vdmax)
            if top <= spanplus:
                break
    elif vdmax < D(0) and vdmin.copy_abs() < spanplus:
        # vdmax is negative and close to zero, so prefer it to be zero
        top = D(0)
        for prec in range(1, 20):
            ctx = decimal.Context(prec=prec)
            bot = ctx.next_minus(vdmin)
            if bot.copy_abs() <= spanplus:
                break
    else:
        for prec in range(1, 20):
            ctx = decimal.Context(prec=prec)
            top = ctx.next_plus(vdmax)
            bot = ctx.next_minus(vdmin)
            if ctx.subtract(top,bot) <= spanplus:
                break

    if bot >= D(0) and top < spanplus:
        bot = D(0)
    elif top <= D(0) and bot.copy_abs() < spanplus:
        top = D(0)

    dnum1 = _numbers_after_point(top, bot)
    dnum2 = _numbers_after_point(vdmax, bot)
    dnum3 = _numbers_after_point(top, vdmin)
    dnum4 = _numbers_after_point(vdmax, vdmin)

    dnum = min(dnum1, dnum2, dnum3, dnum4)
    if dnum == dnum4:
        top = vdmax
        bot = vdmin
    elif dnum == dnum3:
        bot = vdmin
    elif dnum == dnum2:
        top = vdmax
 
    # Add zero below gets rid of negative zeros

    return float(top)+0, float(bot)+0, f".{dnum}f"


def _numbers_after_point(vmax, vmin):
    "get decimal numbers after the . when axis divides this into four"
    dnums = []
    part = (vmax - vmin)/D(4)
    value = vmin
    for n in range(5):
        s = f"{value:.6f}".rstrip("0")
        if '.' in s:
            dnums.append( len(s.split('.')[1]) )
        value += part

    if dnums:
        dnum = max(dnums)
    else:
        dnum = 0

    return dnum


@dataclass
class Line:
    "Defines a Line"
    values:list[tuple]
    color:str
    stroke:int = 3
    label:str = ""


# Note values is normally a list of (x,y) tuples, x and y being integers or floats.
# The values argument could also be a deque holding (x,y) tuples, which may be useful if
# measurements are being appended and a maximum number of points are to be retained.

# x values should be increasing values, and any outside of the xmin xmax Axis values
# will not cause an error, but will not be plotted

# y values should be values between the ymin and ymax Axis attributes, if any are outside
# then a ValueError will be raised when the image is created.

# color is an SVG color, using standard strings such as

# Color Names: "red", "blue" etc.
# Hex Codes: "#FF0000" for red.
# RGB/RGBA: "rgb(255,0,0)" or "rgba(255,0,0,0.5)" (with opacity).
# HSL/HSLA: "hsl(0,100%,50%)" or "hsla(0,100%,50%,0.5)" (hue, saturation, lightness, alpha)

# stroke is the width of the plotted line in SVG drawing units, 1 for a thin line
# label is a text label used in a key, if not given, the key will not be drawn



@dataclass
class Axis:
    "Defines the axis of the chart"

    lines:list[Line] = field(default_factory=list)       # list of Line objects

    fontsize:int = 24
    imagewidth:int = 800
    imageheight:int = 600

    xstrings:list[str] = field(default_factory=list)

   # xstrings is an optional list of strings used as the x axis values, use for
   # text values such as months, etc.,
   # If xstrings is left empty, the following two arguments will define the x axis text

    xformat:str = ".1f"            # How the x axis numbers are formatted,
    xintervals:int = 5             # interval spacing of values along the x axis
                                   # 5 would be five intervals and six values.

    # The above values are ignored if xstrings is populated

    xmin:float|int = 0             # minimum x value
    xmax:float|int = 100           # maximum x value

    ystrings:list[str] = field(default_factory=list)

    # ystrings is an optional list of strings used as the y axis values.
    # If ystrings is left empty, the following two arguments will define the y axis text

    yformat:str = ".1f"            # How the y axis numbers are formatted,
    yintervals:int = 5             # interval spacing of values up the y axis,
                                   # 5 would be five intervals and six values.

    # The above values are ignored if ystrings is populated

    # xformat and yformat are format strings describing how numbers are printed
    # for example the string ".2f"   gives a number to two decimal places

    ymin:float|int = 0             # minimum y value
    ymax:float|int = 100           # maximum y value

    # If chart text starts overlapping, either decrease font size,
    # or increase the image size while keeping fontsize the same

    title:str = ""                 # printed at the top of the chart
    description:str = ""           # printed at the bottom of the chart

    verticalgrid:int = 1           # 0 is no vertical grid lines, 1 is a line for every x axis interval, 2 is a line for every second interval.
    horizontalgrid:int = 1         # 0 is no horizontal grid lines, 1 is a line for every y axis interval, 2 is a line for every second interval.

    # The following colors are SVG colors, using standard strings

    gridcol:str="grey"             # Color of the chart grid
    axiscol:str="black"            # Color of axis, title and description
    chartbackcol:str="white"       # the background colour of the chart
    backcol:str="white"            # The background colour of the whole image


    def auto_y(self) -> None:
        """If ystrings has a value this does nothing, just returns.
           Otherwise it inspects the lines and auto picks y axis values
           which it sets into self.ymax, self.ymin, self.yformat and self.yintervals
           """
        if self.ystrings:
            return
        ymax = None
        ymin = None
        for line in self.lines:
            for point in line.values:
                if ymax is None:
                    ymax = point[1]
                    ymin = point[1]
                    continue
                if point[1] < ymin:
                    ymin = point[1]
                if point[1] > ymax:
                    ymax = point[1]

        self.ymax, self.ymin, self.yformat = _brkt(ymax, ymin)
        self.yintervals = 4


    def auto_x(self) -> None:
        """If xstrings has a value this does nothing, just returns.
           Otherwise it inspects the lines and auto picks x axis values
           which it sets into self.xmax, self.xmin, self.xformat and self.xintervals
           """
        if self.xstrings:
            return
        xmax = None
        xmin = None
        for line in self.lines:
            for point in line.values:
                if xmax is None:
                    xmax = point[0]
                    xmin = point[0]
                    continue
                if point[0] < xmin:
                    xmin = point[0]
                if point[0] > xmax:
                    xmax = point[0]


        self.xmax, self.xmin, self.xformat = _brkt(xmax, xmin)
        self.xintervals = 4


    def auto_time_x(self, hourspan:int = 4, localtime:bool=True) -> None:
        """If this is called, all x values should be times in seconds since the
           epoch, such as that returned by time.time().
           hourspan should be the number of hours to display along the x axis
           with a value from 1 to 48. The hours shown will be the given span of
           hours up to the latest value. So the latest measurement will be shown. 
           This method sets self.xmax, self.xmin and self.xstrings to display
           strings along the x axis as hours. These will be local hours if
           localtime is True, or UTC hours if False.
           """
        if not isinstance(hourspan, int):
            raise ValueError("hourspan should be an integer between 1 and 48")
        if hourspan < 1 or hourspan > 48:
            raise ValueError("hourspan should be an integer between 1 and 48")

        xmax = None
        for line in self.lines:
            if xmax is None:
                xmax = line.values[-1][0]
                continue
            lasttimestamp = line.values[-1][0]
            if lasttimestamp > xmax:
                xmax = lasttimestamp

        # time values are in seconds, but the chart axis is labelled in hours,
        # which are modulo 24, local time, daylight saving etc....

        self.xstrings = []

        # get latest timestamp
        lasttimestruct = time.localtime(xmax)
        # sechour will be the timestamp of the hour of the last measurement
        # (found by setting minutes and seconds to zero)
        sechour = round(time.mktime((lasttimestruct.tm_year,
                               lasttimestruct.tm_mon,
                               lasttimestruct.tm_mday,
                               lasttimestruct.tm_hour,
                               0,
                               0,
                               lasttimestruct.tm_wday,
                               lasttimestruct.tm_yday,
                               lasttimestruct.tm_isdst)))
        if hourspan == 1:
            # keep adding 15 minutes until time is greater than xmax, and make that self.xmax
            if xmax < (sechour + 900):
                self.xmax = sechour + 900
            elif xmax < (sechour + 1800):
                self.xmax = sechour + 1800
            elif xmax < (sechour + 2700):
                self.xmax = sechour + 2700
            else:
                self.xmax = sechour + 3600
            self.xmin = self.xmax - 3600
            for seconds in range(self.xmin, self.xmax+900, 900):
                if localtime:
                    self.xstrings.append(f"{time.localtime(seconds).tm_hour}:{time.localtime(seconds).tm_min:02.0f}")
                else:
                    self.xstrings.append(f"{time.gmtime(seconds).tm_hour}:{time.localtime(seconds).tm_min:02.0f}")
        elif hourspan == 2:
            # keep adding 30 minutes until time is greater than xmax, and make that self.xmax
            if xmax < sechour + 1800:
                self.xmax = sechour + 1800
            else:
                self.xmax = sechour + 3600
            self.xmin = self.xmax - 7200
            for seconds in range(self.xmin, self.xmax+1800, 1800):
                if localtime:
                    self.xstrings.append(f"{time.localtime(seconds).tm_hour}:{time.localtime(seconds).tm_min:02.0f}")
                else:
                    self.xstrings.append(f"{time.gmtime(seconds).tm_hour}:{time.localtime(seconds).tm_min:02.0f}")
        else:
            # Add an hours worth of seconds, to get self.xmax - the chart x axis rightmost seconds value
            self.xmax = sechour + 3600
            self.xmin = self.xmax - (3600 * hourspan)   # hours back from maxts - the chart x axis leftmost value
            # create the hour strings for the x axis labels
            xstrings = []
            for seconds in range(self.xmin, self.xmax+3600, 3600):
                if localtime:
                    t = time.localtime(seconds).tm_hour
                else:
                    t = time.gmtime(seconds).tm_hour
                if hourspan <= 6:
                    self.xstrings.append(str(t))
                elif hourspan <= 12:
                    if t % 2 == 0:
                        self.xstrings.append(str(t))
                    else:
                        self.xstrings.append('')
                elif hourspan <= 24:
                    if t % 4 == 0:
                        self.xstrings.append(str(t))
                    else:
                        self.xstrings.append('')
                elif hourspan <= 36:
                    if t % 6 == 0:
                        self.xstrings.append(str(t))
                    else:
                        self.xstrings.append('')
                else:
                    if t % 8 == 0:
                        self.xstrings.append(str(t))
                    else:
                        self.xstrings.append('')
        

    def to_string(self, xml_declaration:bool = False) -> str:
        """Return a string SVG object. If xml_declaration is True,
           an xml tag will be included in the returned string which
           is usually required when creating an svg image file but not
           required if embedding the code directly into an html document"""
        doc = self._render()
        return ET.tostring(doc, encoding="unicode", xml_declaration=xml_declaration)


    def to_bytes(self, xml_declaration:bool = True) -> bytes:
        """Return a bytes SVG object. If xml_declaration is True,
           an xml tag will be included in the returned bytes which
           is usually required when creating an svg image file but not
           required if embedding the code directly into an html document"""
        doc = self._render()
        return ET.tostring(doc, xml_declaration=xml_declaration)


    def to_file(self, filepath:str) -> None:
        "Save the plot to an svg image file"
        tree = ET.ElementTree(self._render())
        tree.write(filepath, xml_declaration=True)


    def _validate(self):
        """Some minimal validation of input values
           x values must be increasing values along the x axis
           y values must be within self.ymin and self.ymax"""
        if self.xmax <= self.xmin:
            raise ValueError("xmax, xmin values incorrect")
        if self.ymax <= self.ymin:
            raise ValueError("ymax, ymin values incorrect")
        if self.xstrings:
            if isinstance(self.xstrings, str):
                raise ValueError("xstrings must be a list of strings")
        if self.ystrings:
            if isinstance(self.ystrings, str):
                raise ValueError("ystrings must be a list of strings")
        for line in self.lines:
            lastx = None
            for point in line.values:
                if not ( isinstance(point[0], int) or isinstance(point[0], float) ):
                    raise ValueError("x values should be either integers or floats")
                if not ( isinstance(point[1], int) or isinstance(point[1], float) ):
                    raise ValueError("y values should be either integers or floats")
                if point[1] < self.ymin or point[1] > self.ymax:
                    raise ValueError("y value exceeds limits")
                if lastx is not None:
                    if lastx > point[0]:
                        raise ValueError("x values must be increasing values")
                lastx = point[0]


    def _render(self) -> ET.Element:
        "Render the svg image as an elementTree element"

        # some limited validation, if you are embedding this code
        # in your own script, and are sure of your input data, you
        # could comment this out to speed things up slightly
        self._validate()          

        # get the spacing around the chart
        if self.title:
            topspace = self.fontsize * 3  # space at top for title
        else:
            topspace = self.fontsize * 2

        if self.description:
            botspace = self.fontsize * 5  # space at bottom for description
        else:
            botspace = self.fontsize * 3

        # initial chartheight
        chartheight = self.imageheight - topspace - botspace

        # get length of the yaxis text which will be on the left side of the chart
        if self.ystrings:
            ytextlen = max( len(ystring) for ystring in self.ystrings )
        else:
            ysetformat = '{:' + self.yformat + '}'
            ytextlen = max( len(ysetformat.format(self.ymin)), len(ysetformat.format(self.ymax)))

        # define width leftspace which will be to the left of the chart
        leftspace =  self.fontsize * ytextlen

        # define width rightspace which will be to the right of the chart, this will contain
        # line keys, if line labels have been defined
        labelengths = tuple(len(line.label) for line in self.lines)
        if labelengths:
            # if labels, increase rightspace to give space for an index
            longest = max(labelengths)
            rightspace = round(max(self.imagewidth // 10, self.fontsize * (6 + longest)//2))
        else: 
            rightspace =  round(self.imagewidth // 10)

        # initial chartwidth
        chartwidth = self.imagewidth - leftspace - rightspace

        # Start the document
        doc = ET.Element('svg', width=str(self.imagewidth), height=str(self.imageheight), version='1.1', xmlns='http://www.w3.org/2000/svg')
        textstyle = ET.SubElement(doc, 'style')
        textstyle.text = f"""text {{
      font-family: Arial, Helvetica, sans-serif;
      font-size: {self.fontsize}px;
      font-weight: Thin;
    }}
"""

        ### rectangle of background colour, the same size as the whole image
        ET.SubElement(doc, 'rect', {"width":str(self.imagewidth), "height":str(self.imageheight), "x":"0","y":"0", "fill":self.backcol})

        ## optimize chart width, so intervals fall on integer pixels

        # to get best width of chart, xintervals = number of intervals on the x axis
        if self.xstrings:
            xintervals = len(self.xstrings) - 1
        else:
            xintervals = self.xintervals

        if self.ystrings:
            yintervals = len(self.ystrings) - 1
        else:
            yintervals = self.yintervals

        # get better sizing of chart, so interval measurements are all in integers
        xintervalwidth = round(chartwidth / xintervals)
        chartwidth = xintervalwidth * xintervals
        rightspace = self.imagewidth - leftspace - chartwidth

        # to get height of chart
        yintervalwidth = round(chartheight / yintervals)
        chartheight = yintervalwidth * yintervals
        botspace = self.imageheight - topspace - chartheight
        
        ### rectangle of chart background color
        ET.SubElement(doc, 'rect', {"width":str(chartwidth), "height":str(chartheight),
                                    "x":str(leftspace), "y":str(topspace), "fill":self.chartbackcol})

        # title at top of chart
        if self.title:
            t = ET.SubElement(doc, 'text', {"x":str(round(leftspace + chartwidth//4)), "y":str(10 + self.fontsize),
                                            "fill":self.axiscol})
            t.text = self.title

        ### x axis
        ET.SubElement(doc, 'line', {"x1":str(leftspace-1), "y1":str(topspace+chartheight),
                                    # note x1 has minus 1 as the stroke is 3, so this covers the corner
                                    "x2":str(leftspace+chartwidth), "y2":str(topspace+chartheight),
                                    "style":f"stroke:{self.axiscol};stroke-width:3"} )
        # add x ticks
        xpos = leftspace
        for tick in range(xintervals+1):
            ET.SubElement(doc, 'line', {"x1":str(xpos), "y1":str(topspace+chartheight-3), 
                                        "x2":str(xpos), "y2":str(topspace+chartheight+6), "style":f"stroke:{self.axiscol};stroke-width:1"} )
            xpos += xintervalwidth


        ### y axis
        ET.SubElement(doc, 'line', {"x1":str(leftspace), "y1":str(topspace),
                                    "x2":str(leftspace), "y2":str(topspace+chartheight+1),
                                                              # note y2 has plus 1 as the stroke is 3, so this covers the corner
                                    "style":f"stroke:{self.axiscol};stroke-width:3"} )
        # add y ticks
        ypos = topspace
        for tick in range(yintervals+1):
            ET.SubElement(doc, 'line', {"x1":str(leftspace-6), "y1":str(ypos),
                                        "x2":str(leftspace+3), "y2":str(ypos), "style":f"stroke:{self.axiscol};stroke-width:1"} )
            ypos += yintervalwidth

        # vertical grid lines
        if self.verticalgrid:
            xpos = leftspace
            increment = xintervalwidth * self.verticalgrid
            for vline in range(xintervals):
                xpos += increment
                if xpos > leftspace+chartwidth:
                    break
                ET.SubElement(doc, 'line', {"x1":str(xpos), "y1":str(topspace),
                                            "x2":str(xpos), "y2":str(topspace+chartheight-1),
                                            "style":f"stroke:{self.gridcol};stroke-width:1"} )

        # horizontal grid lines
        if self.horizontalgrid:
            ypos = topspace+chartheight
            decrement = yintervalwidth * self.horizontalgrid
            for hline in range(yintervals):
                ypos -= decrement
                if ypos < topspace:
                    break
                ET.SubElement(doc, 'line', {"x1":str(leftspace+1), "y1":str(ypos),
                                            "x2":str(leftspace+chartwidth), "y2":str(ypos),
                                            "style":f"stroke:{self.gridcol};stroke-width:1"} )

        # x axis text
        xpos = leftspace - round(self.fontsize//2)
        ypos = topspace+chartheight + 10 + self.fontsize

        if self.xstrings:
            for txt in self.xstrings:
                if txt:
                    tel = ET.SubElement(doc, 'text', {"x":str(xpos), "y":str(ypos),
                                                      "fill":self.axiscol})
                    tel.text = txt
                xpos += xintervalwidth
        else:
            xvalinterval = (self.xmax - self.xmin) / xintervals
            xval = self.xmin
            xsetformat = '{:' + self.xformat + '}'
            for interval in range(xintervals+1):
                tel = ET.SubElement(doc, 'text', {"x":str(xpos), "y":str(ypos),
                                                  "fill":self.axiscol})
                tel.text = xsetformat.format(xval)
                xpos += xintervalwidth
                xval += xvalinterval

        # description at bottom of chart
        if self.description:
            desc = ET.SubElement(doc, 'text', {"x":str(leftspace), "y":str(self.imageheight - 10 - self.fontsize),
                                              "fill":self.axiscol})
            desc.text = self.description

        # y axis text
        ypos = topspace + round(self.fontsize//5)
        if self.ystrings:
            for txt in reversed(self.ystrings):
                if txt:
                    tel = ET.SubElement(doc, 'text', {"x":str(leftspace-10), "y":str(ypos),
                                                      "fill":self.axiscol, "text-anchor":"end"})
                    tel.text = txt
                ypos += yintervalwidth
        else:
            yvalinterval = (self.ymax - self.ymin) / yintervals
            yval = self.ymax
            for interval in range(yintervals+1):
                tel = ET.SubElement(doc, 'text', {"x":str(leftspace-10), "y":str(ypos),
                                                  "fill":self.axiscol, "text-anchor":"end"})
                tel.text = ysetformat.format(yval)
                ypos += yintervalwidth
                yval -= yvalinterval

        # draw the lines
        for line in self.lines:
            points = []
            for x,y in line.values:
                if x < self.xmin or x > self.xmax:
                    continue
                py = round(topspace+chartheight - (y-self.ymin)*chartheight/(self.ymax-self.ymin))
                px = round(leftspace + (x-self.xmin)*chartwidth/(self.xmax-self.xmin))
                points.append(f"{px},{py}")
            if not points:
                continue
            pointstring = " ".join(points)
            ET.SubElement(doc, 'polyline', {"style":f"fill:none;stroke:{line.color};stroke-width:{line.stroke}", "points":pointstring})

        # draw the index
        if labelengths:
            # get lines in order of the last point y value
            sortedlines = sorted(self.lines, key = lambda x:x.values[-1][1], reverse=True)
            ypos = topspace
            xpos = self.imagewidth - rightspace + self.fontsize + self.fontsize
            for line in sortedlines:
                lbl = ET.SubElement(doc, 'text', {"x":str(xpos),
                                                  "y":str(ypos),
                                                  "fill":line.color,
                                                  "font-weight":"Thin"})

                lbl.text = line.label
                ypos += 3*self.fontsize

        return doc
       


if __name__ == "__main__":

    # Example plot

    line1 = Line(values = [(0,15), (2,20), (4, 50), (6, 75), (10, 60)],
                color = "green",
                label = "green line")

    line2 = Line(values = [(0,95), (2,80), (5, 60), (7, 55), (8, 35), (9, 25), (10, 10)],
                color = "blue",
                label = "blue line")

    line3 = Line(values = list((x,x**2) for x in range(11)),
                color = "red",
                label = "y = x squared")

    example1 = Axis( [line1, line2, line3],
                    title = "Example Chart",
                    description = "Fig 1 : Example chart")
    example1.auto_x()
    example1.auto_y()

    print("Creating file test.svg")
    example1.to_file("test.svg")

    import random
    # use random y values

    line4  = Line(values = [],
                color = "black")
    t = round(time.time())
    for x in range(t - 180000, t+300, 300): # simulate samples every 5 minutes for 50 hours
        line4.values.append((x, random.randint(5, 25)))

    example2 = Axis( [line4],
                    title = "Example Time Axis Chart",
                    description = "One hour time axis chart")
    example2.auto_time_x(hourspan=1)
    example2.ymin = 0.0
    example2.ymax = 30.0
    example2.yintervals = 6

    print("Creating file test2.svg")
    example2.to_file("test2.svg")

    example2.auto_time_x(hourspan=2)
    example2.description = "Two hour time axis chart"
    print("Creating file test3.svg")
    example2.to_file("test3.svg")

    example2.auto_time_x(hourspan=4)
    example2.description = "Four hour time axis chart"
    print("Creating file test4.svg")
    example2.to_file("test4.svg")

    example2.auto_time_x(hourspan=8)
    example2.description = "Eight hour time axis chart"
    print("Creating file test5.svg")
    example2.to_file("test5.svg")

    example2.auto_time_x(hourspan=16)
    example2.description = "Sixteen hour time axis chart"
    print("Creating file test6.svg")
    example2.to_file("test6.svg")

    example2.auto_time_x(hourspan=32)
    example2.description = "Thirtytwo hour time axis chart"
    print("Creating file test7.svg")
    example2.to_file("test7.svg")

    example2.auto_time_x(hourspan=48)
    example2.description = "Fortyeight hour time axis chart"
    print("Creating file test8.svg")
    example2.to_file("test8.svg")

    print("Done")

