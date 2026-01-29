## minilineplot

minilineplot.py is a single Python module, with no dependencies, producing an SVG image of a chart with one or more plotted lines.

The chart has a left vertical axis and a bottom horizontal axis, grid lines are possible,

Two classes are defined.

**Line**, containing x,y points which creates a line to be plotted 

**Axis** which creates the axis, and to which Line objects can be added.

The Axis class has methods to create an svg string suitable for embedding in an html document
it can also create an svg image, either as a bytes object, or saved to a file.

# Line

**Arguments (and attributes)**

*values*  a list of x,y tuples, x and y being integers or floats.

*color*  an SVG color of the line, such as 'blue'.

*stroke*  line width, 1 for a thin line, default is 3.

*label*  A label string for a key, if not given, the key will not be drawn

x values should be increasing values, and any outside of the xmin and xmax values set
into the Axis object will not cause an error, but will not be plotted.

y values should be values between the ymin and ymax Axis attributes, if any are outside
then a ValueError will be raised when the SVG image is created.

Instead of a list, the values argument could also be a deque holding (x,y) tuples, which may be
useful if measurements are being appended and a maximum number of points are to be retained.

color is an SVG color, using standard strings such as

Color Names: "red", "blue" etc.

Hex Codes: "#FF0000" for red.

RGB/RGBA: "rgb(255,0,0)" or "rgba(255,0,0,0.5)" (with opacity).

HSL/HSLA: "hsl(0,100%,50%)" or "hsla(0,100%,50%,0.5)" (hue, saturation, lightness, alpha)


# Axis

**Arguments (and attributes)**

*lines* list of Line objects

*fontsize*  default 24

*imagewidth*  default 800

*imageheight* default 600

*xstrings* an optional list of strings used as the x axis values, use for text values such as months, etc.,

If xstrings is left empty, the following two arguments will define the x axis text

*xformat* default string ".1f" Sets how the x axis numbers are formatted.

*xintervals* default 5, the interval spacing of values along the x axis, 5 would be five intervals and six values.

The above values are ignored if xstrings is populated, intervals are taken from the number of strings.

*xmin* default 0, the minimum plotted x value

*xmax* default 100, the maximum plotted x value

xmin and xmax can be set manually, either as class arguments, or setting the attributes after an Axis object is instantiated. They can also be set automatically by calling the auto_x() method.

If xstrings is set with strings, xmin should be set to the value corresponding to the first string, and xmax to the value corresponding to the last string, this aligns values with the axis strings.

*ystrings* an optional list of strings used as the y axis values.

If ystrings is left empty, the following two arguments will define the y axis text

*yformat* default string ".1f" Sets how the y axis numbers are formatted.

*yintervals* default 5, the interval spacing of values along the y axis, 5 would be five intervals and six values.

The above values are ignored if ystrings is populated, intervals are taken from the number of strings.

*ymin* default 0, the minimum y value

*ymax* default 100, the maximum y value

*title* default empty string. If given this will be printed at the top of the chart.

*description* default empty string. If given this will be printed at the bottom of the chart.

*verticalgrid* default 1

0 is no vertical grid lines, 1 is a line for every x axis interval, 2 is a line for every second interval etc.,

*horizontalgrid* default 1

0 is no horizontal grid lines, 1 is a line for every y axis interval, 2 is a line for every second interval etc.,

The following colors are SVG colors, using standard strings

*gridcol* default "grey" Color of the chart grid

*axiscol* default "black" Color of axis, title and description

*chartbackcol* default "white" the background colour of the chart

*backcol* default "white" The background colour of the whole image

xformat and yformat are strings describing how numbers are printed, for example the string ".2f" gives a number to two decimal places.

If chart text starts overlapping, either decrease font size, or increase the image size while keeping fontsize the same.

All arguments are also object attributes, and can be changed as required.

**Methods**

*auto_x()*

If xstrings has a value this does nothing, just returns. Otherwise it inspects the lines and auto chooses x axis values which it sets into self.xmax, self.xmin, self.xformat and self.xintervals.

This could be useful for generated line data, or for initiall viewing after which better values could be chosen.

*auto_y()*

If ystrings has a value this does nothing, just returns. Otherwise it inspects the lines and auto chooses y axis values which it sets into self.ymax, self.ymin, self.yformat and self.yintervals.

*auto_time_x(hourspan = 4, localtime = True)*

If this is called, all x values should be times in seconds since the epoch, such as that returned by time.time().

hourspan should be the number of hours to display along the x axis with a value from 1 to 48. The hours shown will be the given span of hours up to the latest value. So the latest measurement will be shown.

This method sets self.xmax, self.xmin to the appropriate seconds values, and self.xstrings to display strings along the x axis as hours. These will be local hours if localtime is True, or UTC hours if False. So it could be used to produce a chart as measurements are created with (time.time(), y) tuples.

The following methods produce the SVG chart.

*to_string(xml_declaration = False)*

Returns a string SVG object. If xml_declaration is True, an xml tag will be included in the returned string which is usually required when creating an svg image file but not required if embedding the code directly into an html document.

*to_bytes(xml_declaration = True)*

Returns a bytes SVG object.

*to_file(filepath)*

Saves the plot to an svg image file

To install, either use Pypi, or simply copy minilineplot.py to your own project files. The code is public domain.

A typical example might be:

    line1 = Line(values = [(0,15), (2,20), (4, 50), (6, 75), (10, 60)],
                 color = "green",
                 label = "green line")
    line2 = Line(values = [(0,95), (2,80), (5, 60), (7, 55), (8, 35), (9, 25), (10, 10)],
                color = "blue",
                label = "blue line")
    line3 = Line(values = list((x,x**2) for x in range(11)),
                color = "red",
                label = "y = x squared")
    example = Axis( [line1, line2, line3],
                    title = "Example Chart",
                    description = "Fig 1 : Example chart")
    example.auto_x()
    example.auto_y()
    example.to_file("test.svg")

![Test image](https://raw.githubusercontent.com/bernie-skipole/minilineplot/main/test.svg)


