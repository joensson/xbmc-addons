import signal, os, subprocess as sp, sys



def PlaybackInSafariOSx(url):
    if(sys.platform != 'darwin'):
        print "Not running on darwin platform - aborting. PlaybackInSafariOSx can only be run on OSx since it depends on AppleScript ~ osascript"
        return 
    script_dir=os.path.dirname(os.path.realpath(__file__))
    print("Launching Safari using AppleScript and starting maximized playback")
    script = 'hbo_nordic_safari.scpt'
    ##TODO run signal on main thread to handle (ignore) child zombies
    #signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    try:
        hboProc = sp.Popen(['osascript', os.path.join(script_dir, script), url], stdout = sp.PIPE, stderr = sp.STDOUT)

        while True:
            line = hboProc.stdout.readline()
            code = hboProc.poll()
            print("hbo_nordic_safari.scpt: {0}".format(line))
            if line == '':
                if code != None:
                    break
            else:
                continue

    except OSError, e:
        # Ignore, but log the error
        if (e.strerror == "No child processes"):
            print("TODO: This error happens in subprocess (and popen2) modules in Python 2.4 - upgrade Python? - Errno: {0} - {1}".format(e.errno, e.strerror))
            pass
        else:
            raise e
    
    print("Done executing hbo_nordic_safari.scpt")

if __name__ == "__main__":
    sys.exit(PlaybackInSafariOSx('http://hbonordic.com/series/-/-/a-day-in-the-life/seasons/1/1-richard-branson'))