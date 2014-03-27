#!/usr/bin/env python
#=================================================================
# main yawpi program
#=================================================================

# XXX todo:
# save config and programs on change

# standard modules:
import time
from datetime import datetime
import sys
import web
import thread
import pickle
import os
# gv - 'global vars' - an empty module, used for storing vars (as attributes),
# that need to be 'global' across threads and between functions and classes:
import gv
# yawpi hardware control (hardware abstraction layer):
from yawpi_hw_control import yawpihw


# ------------------- general functions:
def get_now_str():  # returns current date and time as string
    return time.strftime('%d. %m. %Y %H:%M, %A, %B, %Z')


def get_day_sec():  # returns seconds from midnight
    today = datetime.date.today()
    return time.time() - time.mktime(today.timetuple())


def s_to_hms(secondsofaday):  # seconds -> (hour, minute, second)
    # convert seconds of a day to hour and minute and second of a day
    hour = secondsofaday // 3600
    rest = secondsofaday - hour * 3600
    minute = rest // 60
    second = rest - minute * 60
    return (hour, minute, second)


def quit():  # performs safe quit
    hw.so_switch(0)  # set pump off
    for i in range(gv.cv['StNo']):
        hw.st_switch(i, 0)  # switch valve off
    hw.clean_up()  # cleans GPIO
    gs_save()  # save configuration
    prg_save()  # save programs
    log_add('quitting')
    log_save()  # save log
    # and this is the end of the script


def init_gs():  # initialize dictionary with general settings:
    gv.gs = {
        # Name: configurable name of the system
        'Name': u'YAWPI',
        # Version: yawpi version
        'Version': u'0.1',
        # Enabled: operation enabled
        'Enabled': 0,
        # httpPort: http port of web pages
        'httpPort': 8080,
        # Location: city name for weather retrieval from internet
        'Location': u'Brno',
        # Logging: writing to log enabled
        'Logging': 1,
        # LoggingLimit: maximal number of log records to keep, 0 = no limit
        'LoggingLimit': 40,
    }


def init_hws():  # initialize dictionary with hw settings:
    gv.hws = {
        # number of stations
        'StNo': hw.StNo,
        'StData': [],
        'RPiRevision': hw.RPiRevision,
    }
    for x in range(gv.hws['StNo']):
        gv.hws['StData'].append({
            # Station names:
            'Name': 'st' + str(x),
            # lower threshold - if sensors value is below, station is
            # considered empty:
            'LowThr': 0.1,
            # upper threshold - if sensors value is above, station is
            # considered full:
            'HighThr': 0.9,
        })


def init_cv():  # initialize dictionary with current values:
    gv.cv = {
        # NowStr: current time as string for webpage
        'TimeStr': get_now_str(),
        # SoStatus: current status of water source
        'SoStatus': 0,
        # SoWL: current water level of source
        'SoWL': 0,
        # StStatus: current status of stations
        'StStatus': [0] * gv.hws['StNo'],
        # StWL: current water level of stations
        'StWL': [0] * gv.hws['StNo'],
        # temperature sensor status
        'SeTemp': -300,
        'SeRain': -300,
        'SeHumid': -300,
        'SePress': -300,
    }


def prg_get_new():  # returns dict with new program)
    return {
        # name of the program:
        'Name': 'newprogram',
        # program is enabled:
        'Enabled': False,
        # stations affected by program:
        'Stations': [],
        # mode of operation:
        #   'waterlevel' - according water level - start if all stations empty
        #   'weekly' - according calendar - start selected days of week
        #   'interval' - according calendar - start every nth day
        'Mode': 'waterlevel',
        'Mode': 'weekly',
        'Mode': 'interval',
        # for waterlevel mode - not start sooner than (s)
        'wlMinDelay': 3600,
        # for waterlevel mode - must be empty at least (s)
        'wlEmptyDelay': 3600,
        # for weekly mode - start days in week (1 - Monday, 7 - Sunday):
        'calwDays': [1, 3, 5],
        # for interval mode - repeat interval (s):
        'caliInterval': 172800,
        # for both calendar modes - repeat during day every (s):
        'calRepeat': 18000,
        # program valid from time of day (s):
        'TimeFrom': 21600,
        # program valid to time of day (s):
        'TimeTo': 64800,
        # last run of program (s):
        'TimeLastRun': 0,
        # first found empty (usefull for waterlevel mode) (s):
        'TimeFoundEmpty': 0,
    }


def prg_water(index):  # return boolean whether watering should start?
    if gv.prg[i]['Enabled']:
        now = time.time()
        nowinday = get_day_sec()
        # test for valid time of day:
        if nowinday < gv.prg[i]['TimeFrom'] or nowinday > gv.prg[i]['TimeTo']:
            return False
        if gv.prg[i]['Mode'] == 'waterlevel':
            # water level mode:
            # check time from last watering is long enough:
            if not now > gv.prg[i]['TimeLastRun'] + gv.prg[i]['wlMinDelay']:
                return False
            # check if already found all stations empty:
            if gv.prg[i]['TimeFoundEmpty'] == 0:
                # check if all stations in program are empty:
                tmp = False
                for st in gv.prg[i]['Stations']:
                    if gv.cv['StWL'][st] != 0:
                        tmp = True
                if tmp:
                    return False
                else:
                    # all stations empty, remember time
                    gv.prg[i]['TimeFoundEmpty'] = now
            # check if stations are empty long enough:
            if now > gv.prg[i]['TimeFoundEmpty'] + gv.prg[i]['wlEmptyDelay']:
                return True
            else:
                return False
        elif gv.prg[i]['Mode'] == 'weekly':
            # weekly calendar mode:
            # check if valid day of week:
            if not datetime.datetime.today().isoweekday() in gv.prg[i]['calwDays']:
                return False
            # check if valid repeated hours during a day:
            # XXX finish!
            return False
        elif gv.prg[i]['Mode'] == 'interval':
            # XXX finish!
            return False
        else:
            raise NameError('unknown program type')


def gs_load():  # load configuration file
    # general settings:
    if os.path.isfile(gv.gsfilepath):
        # if file exist load it:
        gsfile = open(gv.gsfilepath, 'r')
        gv.gs = pickle.load(gsfile)
        gsfile.close()
        log_add('general settings loaded from file')
    else:
        # if file do not exist initialize standard settings:
        init_gs()
        log_add('general settings initialized to default values')


def gs_save():  # save configuration file
    # general settings:
    if not os.path.isdir(gv.datadir):
        os.mkdir(gv.datadir)
    gsfile = open(gv.gsfilepath, 'w')
    pickle.dump(gv.gs, gsfile)
    gsfile.close()
    log_add('general settings saved to file')


def hws_load():  # load hardware settings file
    # general settings:
    if os.path.isfile(gv.hwsfilepath):
        # if file exist load it:
        hwsfile = open(gv.hwsfilepath, 'r')
        gv.hws = pickle.load(hwsfile)
        hwsfile.close()
        if gv.hws['StNo'] != hw.StNo:
            raise NameError('Number of stations in hardware settings file do \
            not match hardware configuration file. Probably hardware settings \
            file should be deleted?')
        log_add('hardware settings loaded from file')
    else:
        # if file do not exist initialize standard settings:
        init_hws()
        log_add('hardware settings initialized to default values')


def hws_save():  # save configuration file
    # hardware settings:
    if not os.path.isdir(gv.datadir):
        os.mkdir(gv.datadir)
    hwsfile = open(gv.hwsfilepath, 'w')
    pickle.dump(gv.hws, hwsfile)
    hwsfile.close()
    log_add('hardware settings saved to file')


def prg_load():  # load program file
    # general settings:
    if os.path.isfile(gv.prgfilepath):
        # if file exist load it:
        prgfile = open(gv.prgfilepath, 'r')
        gv.prg = pickle.load(prgfile)
        prgfile.close()
        log_add('programs loaded from file')
    else:
        # if file do not exist initialize standard settings:
        gv.prg = []
        log_add('programs initialized to default values')


def prg_save():  # save program file
    # general settings:
    if not os.path.isdir(gv.datadir):
        os.mkdir(gv.datadir)
    prgfile = open(gv.prgfilepath, 'w')
    pickle.dump(gv.prg, prgfile)
    prgfile.close()
    log_add('programs saved to file')


def log_add(line):  # add string to a log buffer
    if gv.gs['Logging']:
        # add time to the log line:
        tmp = datetime.now().strftime('%Y.%m.%d-%H:%M:%S.%f') + \
            ': ' + line + '\n'
        # hopefully this is atomic operation so no collisions between threads
        # can occur:
        gv.logbuffer = gv.logbuffer + [tmp]


def log_save():  # saves log to a file
    # this function should be called only from main thread (not webserver
    # thread) to prevent thread collisions
    # write only if buffer is not empty:
    if gv.gs['Logging'] and len(gv.logbuffer) > 0:
            logfile = open(gv.logfilepath, 'a')
            # this is not atomic XXX! :
            tmp = gv.logbuffer
            gv.logbuffer = []
            # write buffer to a file:
            logfile.writelines(tmp)
            logfile.close()
        # XXX how to limit lines in log file?


def log_get():  # returns full log (load file and add buffer)
    tmp = ['']
    if gv.gs['Logging'] and os.path.isfile(gv.logfilepath):
        logfile = open(gv.logfilepath, 'r')
        # read file and append actual buffer:
        tmp = logfile.readlines() + gv.logbuffer
        logfile.close()
    return tmp


# ------------------- hardware related functions (cal only from main thread):
def sensors_get_all():  # measures water levels of barrel and all stations
    # barrel water level:
    gv.cv['SoWL'] = hw.so_level()
    log_add('water source is ' + str(gv.cv['SoWL'] * 100) + '% full')
    # stations water level:
    for i in range(gv.hws['StNo']):
        # XXX tady dat threshold (nebo nekam jinam)?
        gv.cv['StWL'][i] = hw.se_level(i)
        log_add('station ' + str(i) + ' is '
                + str(gv.cv['StWL'][i] * 100) + '% full')
    # weather sensors:
    gv.cv['SeTemp'] = hw.se_temp
    gv.cv['SeHumid'] = hw.se_humid
    gv.cv['SeRain'] = hw.se_rain
    gv.cv['SePress'] = hw.se_press


def cv_update():  # gets all status data from hw_control
    # generate time string:
    gv.cv['TimeStr'] = get_now_str()
    # get status of water source
    gv.cv['SoStatus'] = hw.SoStatus
    # get status of stations (station valves)
    gv.cv['StStatus'] = hw.StStatus


def station_fill(index):  # fill water into one station
    log_add('preparing to fill station ' + str(index))
    # get filling time in seconds according to station capacity:
    filltime = hw.fill_time(index)
    threshold = 0.1  # XXX finish it!
    try:
        realfilltime = hw.st_fill(index, threshold)
    except:   # XXX tohle je mozna blbost, try mozna uvnitr station fill?
        hw.so_switch(0)
        raise NameError('Error when filling station!')
    tmp = 'station ' + str(index) + ' was filled, time of filling was ' \
          + str(realfilltime) + ', time limit was ' + str(filltime) + ' s'
    if realfilltime > filltime:
        tmp = tmp + ', limit EXCEEDED!'
    log_add(tmp)


# ------------------- web pages definitions:
class WebHome:  # home page with status informations
    def GET(self):
        return render.home(gv)

    def POST(self):
        response = web.input()  # get user response
        if 'reload' in response:
            raise web.seeother('/')
        elif 'runnow' in response:
            if not 'askforRun' in gv.flags:
                gv.flags = gv.flags + ['askforRun']
            # wait for refresh maximally 5 seconds:
            waittill = time.time() + 5
            while time.time() < waittill:
                if not 'askforRun' in gv.flags:
                    break
                time.sleep(0.1)
            raise web.seeother('/')
        elif 'options' in response:
            raise web.seeother('/options')
        elif 'stations' in response:
            raise web.seeother('/stations')
        elif 'programs' in response:
            raise web.seeother('/programs')
        elif 'log' in response:
            raise web.seeother('/log')
        elif 'start' in response:
            gv.gs['Enabled'] = 1
            raise web.seeother('/')
        elif 'stop' in response:
            gv.gs['Enabled'] = 0
            raise web.seeother('/')
        elif 'reboot' in response:
            raise web.seeother('/reboot')
        else:
            raise NameError('Error - unknown button on home page')


class WebOptions:  # options page to change settings
    def __init__(self):
        self.frm = web.form.Form(  # definitions of all input fields
            web.form.Textbox(
                'Name',
                web.form.regexp('.+', 'At least one character'),
                description='System name:'
            ),
            web.form.Textbox(
                'httpPort',
                web.form.regexp('^\d\d\d\d$', 'Must be four digits'),
                description='http port of web pages:'
            ),
            web.form.Textbox(
                'Location',
                description='City location of the system (for weather service):'
            ),
            web.form.Checkbox(
                'Logging',
                description='Logging:'
            ),
            web.form.Textbox(
                'LoggingLimit',
                web.form.regexp('^\d+$', 'Must be at least one digit'),
                description='Limit logs to number of lines:'
            ),
        )

    def GET(self):
        frm = self.frm()
        # set default values of forms to current global values:
        frm.Name.value = gv.gs['Name']
        frm.httpPort.value = gv.gs['httpPort']
        frm.Location.value = gv.gs['Location']
        frm.Logging.checked = gv.gs['Logging']
        frm.LoggingLimit.value = gv.gs['LoggingLimit']
        return render.options(gv, frm)

    def POST(self):
        frm = self.frm()
        response = web.input()  # get user response
        if 'cancel' in response:  # if cancel pressed, go to home page
            raise web.seeother('/')
        elif 'submit' in response:
            if not frm.validates():  # if not validated
                # set default values of forms to user response (so input of all
                # fields is not lost if one field is not validated)
                frm.Name.value = response['Name']
                frm.httpPort.value = response['httpPort']
                frm.Location.value = response['Location']
                frm.Logging.checked = 'Logging' in response
                frm.LoggingLimit.value = response['LoggingLimit']
                return render.options(gv, frm)
            else:
                # write new values to global variables:
                gv.gs['Name'] = response['Name']
                gv.gs['httpPort'] = response['httpPort']
                gv.gs['Location'] = response['Location']
                gv.gs['Logging'] = 'Logging' in response
                gv.gs['LoggingLimit'] = response['LoggingLimit']
                log_add('options changed by user')
                raise web.seeother('/')
        else:
            raise NameError('Error - unknown response in options page')


class WebReboot:  # show reboot question
    def GET(self):
        return render.reboot()

    def POST(self):
        response = web.input()  # get user response
        if 'cancel' in response:  # if cancel pressed, go to home page
            raise web.seeother('/')
        elif 'reboot' in response:
            # send keyboard interrupt to main thread:
            thread.interrupt_main()
            # quit this thread with webserver:
            sys.exit(0)
        else:
            raise NameError('Error - unknown response in reboot page')


class WebLog:  # show log
    def GET(self):
        tmp = log_get()
        #reverse list and serialize it:
        # XXX zkusit pres [8:0:-1]
        tmp.reverse()
        tmp = ''.join(tmp)
        return render.log(tmp)

    def POST(self):
        response = web.input()  # get user response
        if 'reload' in response:  # if reload pressed, reload page
            raise web.seeother('/log')
        elif 'cancel' in response:
            raise web.seeother('/')
        else:
            raise NameError('Error - unknown response in reboot page')


class WebStations:  # shows list of stations
    def GET(self):
        return render.stations(gv)

    def POST(self):
        response = web.input()  # get user response
        if 'cancel' in response:  # if back pressed, go to home page
            raise web.seeother('/')
        else:
            for i in range(gv.cv['StNo']):
                if str(i) in response:
                    return web.seeother('changestation' + str(i))
            else:
                raise NameError('Error - unknown response in stations page')


class WebChangeStation():  # change station settings
    def __init__(self):
        self.frm = web.form.Form(  # definitions of all input fields
            web.form.Textbox(
                'Name',
                web.form.regexp('.+', 'At least one character'),
                description='Station name:'
            ),
        )

    def GET(self, indexstr):
        frm = self.frm()
        try:
            self.index = int(indexstr)
        except ValueError:
            self.index = -1
        if self.index >= 0 and self.index < gv.cv['StNo']:
            # set default values of forms to current global values:
            frm.Name.value = gv.hw['StName'][self.index]
        else:
            self.index = -1
            frm.Name.value = 'X'
        return render.changestation(gv, frm, self.index, indexstr)

    def POST(self, indexstr):
        frm = self.frm()
        response = web.input()  # get user response
        # XXX if else by vzdy melo skoncit na back, pro pripad podivnych
        # navratovych hodnot, a to same u jinych POST ostatnich class
        if 'cancel' in response:  # if back pressed, go to stations page
            raise web.seeother('/stations')
        elif 'submit' in response:
            try:
                self.index = int(indexstr)
            except ValueError:
                self.index = -1
            if self.index >= 0 and self.index < gv.cv['StNo']:
                if not frm.validates():  # if not validated
                    # set default values of forms to user response (so input of
                    # all fields is not lost if one field is not validated)
                    frm.Name.value = response['Name']
                    return render.changestation(gv, frm, self.index, '')
                else:
                    # write new values to global variables:
                    gv.hw['StName'][self.index] = response['Name']
                    log_add('settings of station ' + str(self.index)
                            + ' (' + gv.hw['StName'][self.index]
                            + ' was changed by user')
                    raise web.seeother('/stations')
            else:
                return render.changestation(gv, frm, -1, indexstr)
        else:
            raise NameError('Error - unknown response in changestation page')


class WebPrograms:  # shows list of programs
    def GET(self):
        return render.programs(gv)

    def POST(self):
        response = web.input()  # get user response
        if 'cancel' in response:  # if back pressed, go to home page
            raise web.seeother('/')
        elif 'add' in response:
            gv.prg.append(prg_get_new())
            return web.seeother('programs')
        else:
            for i in range(len(gv.prg)):
                if 'c' + str(i) in response:
                    # change program
                    return web.seeother('changeprogram' + str(i))
                if 'r' + str(i) in response:
                    # remove program
                    gv.prg.pop(i)
                    return web.seeother('programs')
            else:
                raise NameError('Error - unknown response in program page')


class WebChangeProgram():  # change program settings
    def __init__(self):
        self.frm = web.form.Form(  # definitions of all input fields
            web.form.Textbox(
                'Name',
                web.form.regexp('.+', 'At least one character'),
            ),
            web.form.Textbox(
                'wlMinDelay',
                web.form.Validator('(real number greater than 0)',
                                   lambda x: float(x) > 0),
                size="1",
            ),
            web.form.Textbox(
                'wlEmptyDelay',
                web.form.Validator('(real number greater than 0)',
                                   lambda x: float(x) > 0),
                size="1",
            ),
            web.form.Checkbox(
                'calwDays1',
            ),
            web.form.Checkbox(
                'calwDays2',
            ),
            web.form.Checkbox(
                'calwDays3',
            ),
            web.form.Checkbox(
                'calwDays4',
            ),
            web.form.Checkbox(
                'calwDays5',
            ),
            web.form.Checkbox(
                'calwDays6',
            ),
            web.form.Checkbox(
                'calwDays7',
            ),
            web.form.Textbox(
                'caliInterval',
                web.form.Validator('(real number greater than 0)',
                                   lambda x: float(x) > 0),
                size="1",
            ),
            web.form.Textbox(
                'calRepeatW',
                web.form.Validator('(real number from 0 to 23.99)',
                                   lambda x: float(x) >= 0),
                web.form.Validator('(real number from 0 to 23.99)',
                                   lambda x: float(x) < 24),
                size="1",
            ),
            web.form.Textbox(
                'calRepeatI',
                web.form.Validator('(real number from 0 to 23.99)',
                                   lambda x: float(x) >= 0),
                web.form.Validator('(real number from 0 to 23.99)',
                                   lambda x: float(x) < 24),
                size="1",
            ),
            web.form.Textbox(
                'TimeFromH',
                web.form.Validator('(integer number from 0 to 23)',
                                   lambda x: int(x) >= 0),
                web.form.Validator('(integer number from 0 to 23)',
                                   lambda x: int(x) <= 23),
                size="1",
            ),
            web.form.Textbox(
                'TimeFromM',
                web.form.Validator('(integer number from 0 to 23)',
                                   lambda x: int(x) >= 0),
                web.form.Validator('(integer number from 0 to 59)',
                                   lambda x: int(x) <= 59),
                size="1",
            ),
            web.form.Textbox(
                'TimeToH',
                web.form.Validator('(integer number from 0 to 23)',
                                   lambda x: int(x) >= 0),
                web.form.Validator('(integer number from 0 to 23)',
                                   lambda x: int(x) <= 23),
                size="1",
            ),
            web.form.Textbox(
                'TimeToM',
                web.form.Validator('(integer number from 0 to 23)',
                                   lambda x: int(x) >= 0),
                web.form.Validator('(integer number from 0 to 59)',
                                   lambda x: int(x) <= 59),
                size="1",
            ),
        )

    def GET(self, indexstr):
        frm = self.frm()
        try:
            self.index = int(indexstr)
        except ValueError:
            self.index = -1
        if self.index >= 0 and self.index < len(gv.prg):
            # set default values of forms to current global values:
            frm.Name.value = gv.prg[self.index]['Name']
            # convert wlMinDelay to hours:
            frm.wlMinDelay.value = gv.prg[self.index]['wlMinDelay'] / 3600
            # convert wlEmptyDelay to hours:
            frm.wlEmptyDelay.value = gv.prg[self.index]['wlEmptyDelay'] / 3600
            frm.calwDays1.checked = 1 in gv.prg[self.index]['calwDays']
            frm.calwDays2.checked = 2 in gv.prg[self.index]['calwDays']
            frm.calwDays3.checked = 3 in gv.prg[self.index]['calwDays']
            frm.calwDays4.checked = 4 in gv.prg[self.index]['calwDays']
            frm.calwDays5.checked = 5 in gv.prg[self.index]['calwDays']
            frm.calwDays6.checked = 6 in gv.prg[self.index]['calwDays']
            frm.calwDays7.checked = 7 in gv.prg[self.index]['calwDays']
            # convert caliInterval to days:
            frm.caliInterval.value = gv.prg[self.index]['caliInterval'] / 86400
            # convert calRepeat to hours:
            frm.calRepeatW.value = gv.prg[self.index]['calRepeat'] / 3600
            frm.calRepeatI.value = gv.prg[self.index]['calRepeat'] / 3600
            # convert TimeFrom to hour and minute:
            frm.TimeFromH.value = s_to_hms(gv.prg[self.index]['TimeFrom'])[0]
            frm.TimeFromM.value = s_to_hms(gv.prg[self.index]['TimeFrom'])[1]
            # convert TimeTo to hour and minute:
            frm.TimeToH.value = s_to_hms(gv.prg[self.index]['TimeTo'])[0]
            frm.TimeToM.value = s_to_hms(gv.prg[self.index]['TimeTo'])[1]
        else:
            self.index = -1
            frm.Name.value = 'X'
        return render.changeprogram(gv, frm, self.index, indexstr,
                                    gv.prg[self.index]['Enabled'],
                                    gv.prg[self.index]['Mode'])

    def POST(self, indexstr):
        frm = self.frm()
        response = web.input()  # get user response
        # XXX if else by vzdy melo skoncit na back, pro pripad podivnych
        # navratovych hodnot, a to same u jinych POST ostatnich class
        if 'cancel' in response:  # if back pressed, go to stations page
            raise web.seeother('/programs')
        elif 'submit' in response:
            try:
                self.index = int(indexstr)
            except ValueError:
                self.index = -1
            if self.index >= 0 and self.index < len(gv.prg):
                if not frm.validates():  # if not validated
                    # set default values of forms to user response (so input of
                    # all fields is not lost if one field is not validated)
                    frm.Name.value = response['Name']
                    frm.wlMinDelay.value = response['wlMinDelay']
                    frm.wlEmptyDelay.value = response['wlEmptyDelay']
                    frm.calwDays1.checked = 'calwDays1' in response
                    frm.calwDays2.checked = 'calwDays2' in response
                    frm.calwDays3.checked = 'calwDays3' in response
                    frm.calwDays4.checked = 'calwDays4' in response
                    frm.calwDays5.checked = 'calwDays5' in response
                    frm.calwDays6.checked = 'calwDays6' in response
                    frm.calwDays7.checked = 'calwDays7' in response
                    frm.caliInterval.value = response['caliInterval']
                    frm.calRepeatW.value = response['calRepeatW']
                    frm.calRepeatI.value = response['calRepeatI']
                    frm.TimeFromH.value = response['TimeFromH']
                    frm.TimeFromM.value = response['TimeFromM']
                    frm.TimeToH.value = response['TimeToH']
                    frm.TimeToM.value = response['TimeToM']
                    return render.changeprogram(gv, frm, self.index, 'On' in response, 0, response['Mode'])
                else:
                # write new values to global variables:
                    gv.prg[self.index]['Name'] = response['Name']
                    if response['Enabled'] == 'On':
                        gv.prg[self.index]['Enabled'] = True
                    else:
                        gv.prg[self.index]['Enabled'] = False
                    print response['Mode']
                    gv.prg[self.index]['Mode'] = response['Mode']
                    if not (gv.prg[self.index]['Mode'] == 'waterlevel'
                            or gv.prg[self.index]['Mode'] == 'waterlevel'
                            or gv.prg[self.index]['Mode'] == 'waterlevel'):
                        gv.prg[self.index]['Mode'] == 'waterlevel'
                    gv.prg[self.index]['wlMinDelay'] = float(response['wlMinDelay']) * 3600
                    gv.prg[self.index]['wlEmptyDelay'] = float(response['wlEmptyDelay']) * 3600
                    # parse weekdays, sort, remove duplicates and save:
                    tmp = []
                    for i in range(1, 8):
                        if 'calwDays' + str(i) in response:
                            tmp.append(i)
                    # sort and remove duplicates:
                    gv.prg[self.index]['calwDays'] = list(set(sorted(tmp)))
                    gv.prg[self.index]['caliInterval'] = int(response['caliInterval']) * 86400
                    if response['Mode'] == 'weekly':
                        gv.prg[self.index]['calRepeat'] = float(response['calRepeatW']) * 3600
                    else:
                        gv.prg[self.index]['calRepeat'] = float(response['calRepeatI']) * 3600
                    # parse valid from and valid to times:
                    gv.prg[self.index]['TimeFrom'] = int(response['TimeFromH']) * 3600 + int(response['TimeFromM']) * 60
                    gv.prg[self.index]['TimeTo'] = int(response['TimeToH']) * 3600 + int(response['TimeToM']) * 60
                    # parse selected stations
                    tmp = []
                    for i in response:
                        if i[0] == 's':
                            try:
                                num = int(i[1:])
                                tmp.append(num)
                            except ValueError:
                                pass
                    # sort and remove duplicates:
                    gv.prg[self.index]['Stations'] = list(set(sorted(tmp)))
                    # log change:
                    log_add('settings of program ' + str(self.index)
                            + ' (' + gv.prg[self.index]['Name'] + ')'
                            + ' was changed by user')
                    raise web.seeother('/programs')
            else:
                return render.changeprogram(gv, frm, -1, indexstr, 'waterlevel')
        else:
            raise NameError('Error - unknown response in changeprogram page')


# ------------------- code run in both threads:
# list of web pages:
urls = (
    '/', 'WebHome',
    '/options', 'WebOptions',
    '/reboot', 'WebReboot',
    '/log', 'WebLog',
    '/stations', 'WebStations',
    '/changestation(.*)', 'WebChangeStation',
    '/programs', 'WebPrograms',
    '/changeprogram(.*)', 'WebChangeProgram',
)

if __name__ == "__main__":
    # ------------------- code run only in main thread:
    # initialize basic global values:
    gv.datadir = "data"
    gv.gsfilepath = gv.datadir + "/sd.pkl"
    gv.hwsfilepath = gv.datadir + "/hws.pkl"
    gv.prgfilepath = gv.datadir + "/prg.pkl"
    gv.logfilepath = gv.datadir + "/log.txt"
    gv.logbuffer = []
    gv.flags = []

    # load system configuration:
    gs_load()
    # initialize hw:
    hw = yawpihw()
    if hw.WithHW != 1:
            # not running on RPi, simulaition mode set
            tmp = 'no GPIO module was loaded, running in no-hardware mode'
            print tmp
            log_add(tmp)
    # load hardware settings:
    hws_load()
    # load programs:
    prg_load()

    # initialize dictionary with current values:
    init_cv()

    # web server initialization:
    # XXX debug mode
    web.config.debug = 1
    app = web.application(urls, globals())
    # run web server in separate thread:
    thread.start_new_thread(app.run, ())

    # -------------------------------- main program loop
    try:
        while True:
            # generate values for web:
            # measure water levels:
            sensors_get_all()
            # get status data:
            cv_update()
            # if web thread asked for refresh, remove flag:
            if 'askforRun' in gv.flags:
                gv.flags.remove('askforRun')

            # watering
            if gv.gs['Enabled']:
                ## XXX testing code for hw:
                if hw.se_status(0) == 0:
                    station_fill(0)
                # check progs if watering should start:
                for prog in gv.prg:
                    if prg_water(prog):
                        # if should water now
                        # write down last run:
                        # XXX
                        # fill stations:
                        for i in gv.prg['Stations']:
                            station_fill(i)

                # XXX generate next runs - only if watering

            # dump log buffer into a file
            log_save()

            # wait for next loop iteration
            # (time.sleep(60) is not good because catching KeyboardInterrupt
            # exception (end from web thread) would take up to 60 seconds)
            endtime = time.time() + 60
            while time.time() < endtime:
                # if web thread asked for refresh, break loop:
                if 'askforRun' in gv.flags:
                    break
                time.sleep(0.1)
    except KeyboardInterrupt:
        # keyboard interrupt or reboot pressed in webserver
        quit()  # perform safe quit
else:
    # ------------------- code run only in web thread:
    # render of templates:
    render = web.template.render('templates/')
