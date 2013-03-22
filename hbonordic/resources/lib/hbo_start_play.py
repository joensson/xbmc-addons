import signal, os, subprocess as sp, sys



def PlaybackInSafariOSx(url, user, password):
	if(sys.platform != 'darwin'):
		print "Not running on darwin platform - aborting. PlaybackInSafariOSx can only be run on OSx since it depends on AppleScript ~ osascript"
		return 
	script_dir=os.path.dirname(os.path.realpath(__file__))
	print("Launching Safari using AppleScript and starting maximized playback")
	script = 'hbo_nordic_safari.scpt'

	try:
		hboProc = sp.Popen(['osascript', os.path.join(script_dir, script), url, user, password], stdout = sp.PIPE, stderr = sp.STDOUT)

		while True:
			line = hboProc.stdout.readline()
			code = hboProc.poll()

			if line == '':
				if code != None:
					break
			else:
				print("hbo_nordic_safari.scpt: {0}".format(line))
				continue

	except OSError, e:
		# Ignore, but log the error
		if (e.strerror == "No child processes"):
			print("TODO: This error happens in subprocess (and popen2) modules in Python 2.4 - upgrade Python? - Errno: {0} - {1}".format(e.errno, e.strerror))
			pass
		else:
			raise e
	
	print("Done executing hbo_nordic_safari.scpt")
	return 0

if __name__ == "__main__":
	args = sys.argv[1:]
	if (len(args) != 3):
		print "Needs 3 arguments - url, username, password"
		sys.exit(1)
	sys.exit(PlaybackInSafariOSx(args[0], args[1], args[2]))