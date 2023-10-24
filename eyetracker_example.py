import pylink
from pygaze import libscreen, display, eyetracker  # library for the EyeLink eye-tracker
from pygaze import libtime
from pygaze import liblog
from pygaze import libinput
import pygaze
from psychopy import event, visual, core, gui
from psychopy.constants import *
import pygaze.settings as pygset
import tkinter as tk
import random

##---------- Settings & Variables --------------------------------------------------------------------------------------
# TODO put these in a seperate script settings.py

## Obtain actual screen size
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
print(screen_width, screen_height)
disp_size_pix = (screen_width, screen_height)
root.destroy()

# directory for images, stimuli etc.
resources_dir = 'C:/Experiments/Esther_Fatigue/resources/high_resources/english/'
calib_now = True
save_results = True

# ------------------------------------------------------------------------------------------------------------------------
exp_info = {
    u"id": u"",
    u"session": u""
}
dlg = gui.DlgFromDict(dictionary=exp_info,
                      title="KEIKO")  # , fixed=["language"], choices={"language": language_choices})

# # Store aside values from the gui for easier manipulation:
sub_id = int(exp_info['id'])  # Participant's id
sub_session = int(exp_info['session'])

# ----- Eyetracker variables / pygaze settings -----------------------------------------------------------------------
# TODO: put these in a seperate script ??
pygset.LOGFILENAME = exp_info['id'] + "targ"
# pygset.LOGFILE = pygset.LOGFILENAME[:] # .txt; adding path before logfilename is optional; logs responses (NOT eye movements, these are stored in an EDF file!)
bgcolour = 190
pygset.DISPSIZE = (1920, 1080) #(screen_width, screen_height)  # adjust to actual screen
pygset.DISPTYPE = 'psychopy'  # determine pygaze wrapper that is used for stimulus presentation (can also be pygame)
pygset.SCREENNR = 0  # select screen for display if not mirrored starting with 0
pygset.BGC = (bgcolour, bgcolour, bgcolour, bgcolour)
pygset.FULLSCREEN = True
pygset.MOUSEVISIBLE = False # mouse visibility

##---------- Functions communciate with Eyelink-------------------------------------------------------------------------
# - sets parameters for the eyelink (manual adjustments are possible)
# TODO put these in a seperate script pygaze_helper.py
def startup_config(tracker):
    # NEW set EyeLink host PC resolution
    tracker.send_command('screen_pixel_coords = 0 0 1920 1080')
    tracker.send_command('sampling_rate = 500')
    tracker.send_command('binocular_enabled = YES')

    # NEW set EDF file contents
    tracker.send_command("file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT")
    tracker.send_command("file_sample_data  = LEFT,RIGHT,GAZE,AREA,GAZERES,STATUS,HTARGET,INPUT")

    # NEW set link data (used for gaze cursor)
    tracker.send_command("link_event_filter = LEFT,RIGHT,FIXATION,FIXUPDATE,SACCADE,BLINK,BUTTON,INPUT")
    tracker.send_command("link_sample_data  = LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,HTARGET,INPUT")

    # NEW set SR Research host pc to monitor the data register of the parallel port
    tracker.send_command('write_ioport = 0x37A 0x20')
    tracker.send_command('input_data_ports = 0x378')
    tracker.send_command('input_data_ports = 0x378')
    tracker.send_command('pupil_size_diameter = DIAMETER') #NEW: set pupil size measure to diameter

## -------- Set up eyetracker --------------------------------------------------------------------------------------------

# start timing
libtime.expstart()

# Create a display using pygaze
disp = pygaze.libscreen.Display(dispsize=disp_size_pix)
win = pygaze.expdisplay  # get handler to window

# create eyetracker object
tracker = eyetracker.EyeTracker(disp)
tracker.connected()

# create logfile object
log = liblog.Logfile(filename="shit")
log.write(["trialnr", "trialtype", "avg_pupil", "blinks_num"]) #blink start", "blink end", "start-pos", "end-pos"])

# Send intital configurations to eyetracker
startup_config(tracker)  # ususally in pygaze_helper.py

##----------Calibration-------------------------------------------------------------------------------------------------

if calib_now:
    tracker.calibrate()
    print("calibration done")
    calib_success = True
    calib_now = False
else:
    calib_success = False

## ---------- Set up example experiment --------------------------------------------------------------------------------

# Main window object
win = visual.Window(size=disp_size_pix,
                    fullscr=True,
                    useRetina=True,
                    screen=0,
                    color=(166, 166, 166),
                    colorSpace='rgb255',
                    units='pix')

# create list of stimuli
stimuli = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
# for each number create a visual psychopy object
slide_list = []
for each in range(len(stimuli)):
    # Create psychopy visual object:
    stim_slide = visual.TextStim(win=win,
                                 text=stimuli[each],
                                 height=120,
                                 color='black')
    slide_list.append(stim_slide)

# create fixation cross
fix_cross = visual.ImageStim(win=win,
                             image=resources_dir + "fix_cross.png"
                             )

##----------- Start experiment -----------------------------------------------------------------------------------------

# Loop through stimuli
for trial in range(len(slide_list)):

    this_slide = slide_list[trial] # get current stimulus from list
    trialtype = "anything" # here the condition of your trial, e.g. type of stimulus

    if event.getKeys('escape'): # press escape to exit experiment
        tracker.stop_recording()
        sys.exit()

    # start eye tracking
    tracker.start_recording()
    tracker.status_msg("trial %d" % trial)
    tracker.log("start_trial %d trialtype %s" % (trial, trialtype))

    # ----- Present fixation cross -------------------------------------------------------------------------------------
    slide_timer = core.Clock()  # timer to keep track of slide duration
    slide_timer.reset()
    t = slide_timer.getTime()

    while t <= 0.5:
        t = slide_timer.getTime()
        fix_cross.draw()
        tracker.log("fixation")
        win.flip()  # update display
    win.flip()


    # ----- Present stimulus: ----------------------------------------------------------------------------------------
    slide_timer.reset()  # reset timer just in case
    t = slide_timer.getTime()  # get time

    pupil_list = []
    blinks_num = 0
    while t <= 1:
        t = slide_timer.getTime()
        this_slide.draw()
        tracker.log("fixation")
        tracker.log("target %s" % trialtype)
        pupilsize = tracker.pupil_size() # returns pupilsize
        if pupilsize <= 0:
            blinks_num = 1
        else:
            pupil_list.append(pupilsize)
        #sample = tracker.sample() # returns gaze position, negative values are EYEBLINKS
        win.flip()  # update display
    win.flip()

    # Calculate the average pupil size of the trial
    pupil_avg = sum(pupil_list) / len(pupil_list)

    # ---- save results -----------------------------------------------------------------------------------------------
    # log stuff
    log.write([trial, trialtype, pupilsize, blinks_num])


# stop the eyetracker recording and end the experiment
win.flip()
tracker.stop_recording()
log.close()
tracker.close()
disp.close()
libtime.expend()
sys.exit()

