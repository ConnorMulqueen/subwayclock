#!/usr/bin/python3

from tkinter import *
from mta import *
from argparse import ArgumentParser
import os
import glob
import json
import datetime

# Command-line arguments
aparse = ArgumentParser()
aparse.add_argument('-f','--fullscreen', action="store_true", default=False,
                    help="fullscreen")



args = aparse.parse_args()

stations = []

# Font
fontName = "sans"

# A minute's worth of milliseconds
oneMinute = 60000

# Interval in minutes between MTA data fetches
fetchInterval = 3




# Format a list of arrival times into a string for display
def formatMinutes(mList):

    # If the list is empty, return empty string
    if (len(mList) == 0):
        return("")

    # Slice off the first three or four times and turn them into a
    # comma-separated list

    # If the first item in the list is two digits, then only return
    # the first three items, otherwise the first four. This is so as
    # to not wind up with a string too long to display.

    n = 4
    if (mList[0] > 9):
        n = 3

    return(" " + ', '.join(map(str, mList[:n])))

# Decrement each minute on a list of arrival times, roll off any 0's
def decList(l):
    return([i-1 for i in l if i-1 > 0])

# Will be called every minute
def callBack():
    global minuteCounter
    global trainTimes
    global current_times

    # Decrement all the arrival times by a minute (unless it's the first
    # time through)
    if (minuteCounter != 0):
        # ~ decrement arrival times
        for station in current_times.keys():
            for train_line in current_times[station].keys():
                try:
                    current_times[station][train_line] = decList(current_times[station][train_line])
                except:
                    breakpoint()
                
        # ~ set strings
        for station in current_times.keys():
            for train_line in current_times[station].keys():
                stations[station][train_line].set(', '.join(str(time) for time in current_times[station][train_line][0:4]))
        
        


    # If it's time to fetch fresh MTA data, do so.
    if ((minuteCounter % fetchInterval) == 0):
        try:
            lines = [station_object['station_name'] for station_object in config['stations']]
            trainTimes = getTrainTimesList(lines)
            current_times = {}
            for line in trainTimes:
    
                
                strings = {}
                current_times[line] = {}
                for time_and_line_tuple in trainTimes[line]:
                    if time_and_line_tuple[1] in strings:
                        current_times[line][time_and_line_tuple[1]].append(time_and_line_tuple[0])
                        strings[time_and_line_tuple[1]].append(str(time_and_line_tuple[0])+',')
                    else:
                        current_times[line][time_and_line_tuple[1]] = [time_and_line_tuple[0]]
                        strings[time_and_line_tuple[1]] = [str(time_and_line_tuple[0]) +',']
                for train in strings:
                    print('setting ', line, ' for ', train)
                    stations[line][train].set(' '.join(strings[train][0:4])[:-1])
                

            # If we successfully got MTA API data, set our text to black

        except Exception as e:
            print('exception thrown', e)
            # If the last MTA API call failed, set our text to red

            # If the API called failed, then bump the minute counter
            # down. This will force another API call on the next
            # firing of the callback.
            minuteCounter -= 1


        


    # Increment our minute counter
    minuteCounter += 1

    # See 'ya again in a minute
    
    print('callback fin', datetime.datetime.now())
    m.after(oneMinute,callBack)


# Create main application window
m = Tk()

# Are we fullscreen
if (args.fullscreen):
    m.attributes("-fullscreen", True)
    m.overrideredirect(1)

displayWidth = m.winfo_screenwidth()
displayHeight = m.winfo_screenheight()

# Get display DPI
dpi = int(m.winfo_pixels('1i'))

# Calculate points per pixel
ppx = dpi / 72

# Font size of time text should be 10% of screen height
timeTextFontSize = int((displayHeight * 0.010) * ppx)

# Label font size should be 5% of screen height
labelFontSize = int((displayHeight * 0.015) * ppx)

# Make our background white
m.configure(background='white')

# Target size of images is 37.5% of display height
imageSize = int(displayHeight * 0.05)


# Map train letters to images. Scale the images as necessary. The results
# of scaling the images are not great, it's STRONGLY recommended that you
# create images which are already of the correct size (37.5% of display height).

images = {}

# Grab each PNG in the icons subdirectory
for f in (glob.glob('assets%s*.png'%(os.sep))):

    # Index on the basename of the PNG file. For example the "A" train will
    # have its image in the file icons/A.png
    l = os.path.basename(os.path.splitext(f)[0])
    images[l] = PhotoImage(file=f)

    # If the image is not square, we're just not going to deal with it.
    if (images[l].height() != images[l].width()):
        raise Exception("Image icons%s%s.png is not square"%(os.sep,l))

    # Are we scaling down?
    if ((images[l].height() > imageSize)):
        scale = int(1 / (imageSize/images[l].width()))
        images[l] = images[l].subsample(scale, scale)

    # Are we scaling up?
    if ((images[l].height() < imageSize)):
        scale = int(imageSize/images[l].width())
        images[l] = images[l].zoom(scale, scale)



with open("stationsconfig.json", "r") as json_config:
    config = json.load(json_config)
    print("Successfully fetched config")

row = 0
column = 0
stations = {}
for station_object in config['stations']:
    firstRowColumns = 0
    stations[station_object['station_name']] = {}


    train_station_string = StringVar()
    train_station_string.set(station_object['description'])
    Label(m,
      font=(fontName, labelFontSize),
      anchor='w',
      justify='left',

      textvariable=train_station_string).grid(row=row,
                                   column=firstRowColumns,
                                   columnspan=4, pady=3
                                )


    train_image_1 = Label(m)
    train_image_1.config(bg='gray51', fg='gray51')
    train_image_1['image'] = images[station_object['available_lines'][0]]
    train_image_1.grid(row=row+1, column=0, sticky=W)

    train_string_line_1 = StringVar()
    train_string_line_1.set('no trains running')
    train_text_1 = Label(m,
                    font=(fontName, timeTextFontSize),
                    justify='left',
                    textvariable=train_string_line_1)
    train_text_1.grid(row=row+1, column=1, sticky=W)

    
    train_image_2 = Label(m)
    train_image_2.config(bg='gray51', fg='gray51')
    train_image_2['image'] = images[station_object['available_lines'][1]]
    train_image_2.grid(row=row+1, column=2)

    train_string_line_2 = StringVar()
    train_string_line_2.set('no trains running')
    train_text_2 = Label(m,
                    anchor='w',
                    justify='left',
                    font=(fontName, timeTextFontSize),
                    textvariable=train_string_line_2)
    train_text_2.grid(row=row+1, column=3, sticky=W)

    
    stations[station_object['station_name']][station_object['available_lines'][0]] = train_string_line_1
    
    stations[station_object['station_name']][station_object['available_lines'][1]] = train_string_line_2

    # Draw horizontal line seperating uptown/downtown times
    lineMargin = 20
    c = Canvas(m, width=displayWidth,
               height=lineMargin,
               bd=0,
               highlightthickness=0,
               relief='ridge')
    c.grid(row=row+2, column=0, columnspan=4)
    c.create_line(0, lineMargin, displayWidth, lineMargin, width=3)


    row+=3

# Make all widgets have the same bg color as the main window
for c in m.winfo_children():
    c.configure(background=m['background'])

# Counts the number of minutes we've been running
minuteCounter = 0


# Kick off the callback
callBack()

# Run the UI
m.geometry('1080x1920')
m.update_idletasks()
m.mainloop()



