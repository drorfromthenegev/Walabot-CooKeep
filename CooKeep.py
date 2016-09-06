from __future__ import print_function # python2-python3 compatibillity
try: input = raw_input # python2-python3 compatibillity
except NameError: pass # python2-python3 compatibillity
from sys import platform
from os.path import join
from imp import load_source # used to load the walabot library
from datetime import datetime, timedelta # used to the current time
from math import sin, cos, radians, sqrt # used to calculate MAX_Y_VALUE
import simpleaudio
WAVPATH=r'alarm.wav' #The path to the alarm sound
R_MIN, R_MAX, R_RES = 10, 60, 2 # walabot SetArenaR parameters
THETA_MIN, THETA_MAX, THETA_RES = -10, 10, 10 # walabot SetArenaTheta parameters
PHI_MIN, PHI_MAX, PHI_RES = -10, 10, 2 # walabot SetArenaPhi parametes
THRESHOLD = 15 # walabot SetThreshold parametes
MAX_Y_VALUE = R_MAX * cos(radians(THETA_MAX)) * sin(radians(PHI_MAX))
SENSITIVITY = 0 # amount of seconds to wait after a move has been detected
TENDENCY_LOWER_BOUND = 0.1 # tendency below that won't count as entrance/exit
IGNORED_LENGTH = 3 # len in cm to ignore targets in center of arena (each side)
APPROVEDDISTANCE=200 #the minimal distance from the cookies that people could be in
def initWalabot():
    """ Load and initialize the Walabot SDK. A cross platform function.
        Returns:
            wlbt:           The WalabotAPI module
    """
    if platform == 'win32': # for windows
        path = join('C:/', 'Program Files', 'Walabot', 'WalabotSDK', 'python')
    else: # for linux, raspberry pi, etc.
        path = join('/usr', 'share', 'walabot', 'python')
    wlbt = load_source('WalabotAPI', join(path, 'WalabotAPI.py'))
    wlbt.Init()
    wlbt.SetSettingsFolder()
    return wlbt
wlbt = initWalabot()


def verifyWalabotIsConnected():
    """ Check for Walabot connectivity. loop until detect a Walabot.
    """
    while True:
        try:
            wlbt.ConnectAny()
        except wlbt.WalabotError as err:
            if err.code == 19: # 'WALABOT_INSTRUMENT_NOT_FOUND'
                input("- Connect Walabot and press 'Enter'.")
        else:
            print('- Connection to Walabot established.')
            return

def setWalabotSettings():
    """ Configure Walabot's profile, arena (r, theta, phi), threshold and
        the image filter.
    """
    wlbt.SetProfile(wlbt.PROF_SENSOR)
    wlbt.SetArenaR(R_MIN, R_MAX, R_RES)
    wlbt.SetArenaTheta(THETA_MIN, THETA_MAX, THETA_RES)
    wlbt.SetArenaPhi(PHI_MIN, PHI_MAX, PHI_RES)
    wlbt.SetThreshold(THRESHOLD)
    wlbt.SetDynamicImageFilter(wlbt.FILTER_TYPE_NONE)
    print('- Walabot Configurated.')

def startAndCalibrateWalabot():
    """ Start the Walabot and calibrate it.
    """
    wlbt.Start()
    wlbt.StartCalibration()
    print('- Calibrating...')
    while wlbt.GetStatus()[0] == wlbt.STATUS_CALIBRATING:
        wlbt.Trigger()
    print('- Calibration ended.\n- Ready!')

def getDataList():
    """ Detect and record a list of Walabot sensor targets. Stop recording
        and return the data when enough triggers has occured (according to the
        SENSITIVITY) with no detection of targets.
        Returns:
            dataList:      A list of the yPosCm attribute of the detected
                            sensor targets
    """
    while True:
        wlbt.Trigger()
        targets = wlbt.GetSensorTargets()
        distance = lambda t: sqrt(t.xPosCm**2 + t.yPosCm**2 + t.zPosCm**2)
        if targets:
            targets = [max(targets, key=distance)]
            numOfFalseTriggers = 0
            triggersToStop = wlbt.GetAdvancedParameter('FrameRate')*SENSITIVITY
            while numOfFalseTriggers < triggersToStop:
                wlbt.Trigger()
                newTargets = wlbt.GetSensorTargets()
                if newTargets:
                    targets.append(max(newTargets, key=distance))
                    numOfFalseTriggers = 0
                else:
                    numOfFalseTriggers += 1
            yList = [t.yPosCm for t in targets if abs(t.yPosCm)>IGNORED_LENGTH]
            if yList:
                return yList




def stopAndDisconnectWalabot():
    """ Stops Walabot and disconnect the device.
    """
    wlbt.Stop()
    wlbt.Disconnect()

def CooKeep():
    """ Main function. init and configure the Walabot, get the current number
        of people from the user, start the main loop of the app.
        Walabot scan constantly and record sets of data (when peoples are
        near the door header). For each data set, the app calculates the type
        of movement recorded and acts accordingly.
    """
    verifyWalabotIsConnected()
    setWalabotSettings()
    startAndCalibrateWalabot()
    try:
        while True:
            dataList = getDataList()
            if min(dataList)<APPROVEDDISTANCE:
                print("Do not touch the cookies!!!!!!!")
                alarm=simpleaudio.WaveObject.from_wave_file(r'c:\Users\user\Desktop\Loud-alarm-clock-sound.wav')
                playobj=alarm.play()
                playobj.wait_done()
    except KeyboardInterrupt: pass
    finally:
        stopAndDisconnectWalabot()

if __name__ == '__main__':
    CooKeep()

