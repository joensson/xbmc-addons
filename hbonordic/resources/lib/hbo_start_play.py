import signal, os, subprocess as sp, sys



def PlaybackInSafariOSx(url, user, password):
	"""
	Depends on osascript (AppleScript) and the free cliclick binary (http://www.bluem.net/en/mac/cliclick/)
	osascript must be able to load the script hbo_nordic_safari.scpt.
	
	The AppleScript is written specifically for Safari - but most of the interesting bits is javascript that Safari
	is asked to execute in order to calculate screen coordinates for buttons etc.
	
	The script is located in resources/lib along with the cliclick binary
	"""
	if(sys.platform != 'darwin'):
		print("Not running on darwin platform - aborting. PlaybackInSafariOSx can only be run on OSx since it depends on AppleScript ~ osascript")
		return 
	lib = os.path.dirname(os.path.realpath(__file__)) #os.path.join(ROOT_FOLDER,"resources","lib")
	
	print("Launching Safari using AppleScript and starting maximized playback")
	script = 'hbo_nordic_safari.scpt'
	
	#cliclick binary is expected to be executable, and for some reason XBMC removes the executable permission for the binary when installing from zip
	cliclick_binary = os.path.join(lib, 'cliclick')
	try:
		os.chmod(cliclick_binary, 0755)
	except Exception, e:
		print("Failed changing permissions on {0} {1}".format(cliclick_binary, e.strerror))
	
	try:
		hboProc = sp.Popen(['osascript', os.path.join(lib, script), url, user, password], stdout = sp.PIPE, stderr = sp.STDOUT)

		while True:
			line = hboProc.stdout.readline()
			code = hboProc.poll()
			
			if line == '':
				if code != None:
					break
			else:
				print("hbo_nordic_safari.scpt: {0}".format(line))
				continue
		if hboProc.returncode != 0:
			print("Script failed, see previous log statements for troubleshooting")
		else:
			print("Done executing hbo_nordic_safari.scpt")

	except OSError, e:
		# Ignore, but log the error
		if (e.strerror == "No child processes"):
			#print("TODO: 'No child processes' happens in subprocess (and popen2) modules in Python 2.4 - patch or upgrade Python to get rid of it - [Errno: {0} - {1}]".format(e.errno, e.strerror))
			pass
		else:
			raise e

if __name__ == "__main__":
	args = sys.argv[1:]
	if (len(args) != 3):
		print "Needs 3 arguments - url, username, password"
		sys.exit(1)
	sys.exit(PlaybackInSafariOSx(args[0], args[1], args[2]))