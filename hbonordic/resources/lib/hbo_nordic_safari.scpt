-- This script depends on cliclick to perform mouseclicks
--	http://www.bluem.net/en/mac/cliclick/

on run argv
	set scriptfile to POSIX file (POSIX path of (path to me))
	set scriptfilefolder to GetParentPath(scriptfile)
	set scriptdir to POSIX path of scriptfilefolder
	set cliclickPath to scriptdir & "cliclick"
	
	set episodeUrl to item 1 of argv
	log ("Loading episode url " & episodeUrl)
	
	-- Safari hack - wait for the page to be ready before executing rest of script
	tell application "Safari"
		activate
		delay 1
		set the URL of the front document to episodeUrl
		repeat
			-- use Safari's 'do JavaScript' to check a page's status
			if (do JavaScript "document.readyState" in document 1) is "complete" then exit repeat
			delay 1 -- wait a second before checking again
		end repeat
		delay 1
		repeat
			-- Wait for play button to be available
			if (do JavaScript "typeof __hboPlayerProxy" in document 1) is not "undefined" then exit repeat
			delay 1 -- wait a second before checking again
		end repeat
		--	display dialog "Document ready"
		
		delay 3 --TODO: Figure out when the player and episode scrolls into view
		-- start playback
		do JavaScript "var e = document.createEvent('MouseEvents');e.initMouseEvent('click', true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);$('.js-play_button.play_button').get(0).dispatchEvent(e);" in document 1
		
		-- acquire playback controls coordinates (screen) and store them in menuPos
		set menuPos to do JavaScript "var menuPos = function () { var menuX = window.screenX + $('.js-play_button.play_button')[0].getBoundingClientRect().left; var menuY = window.screenY + window.screen.availTop + (window.screen.height - window.screen.availHeight) + $('.js-play_button.play_button')[0].getBoundingClientRect().top + $('.js-play_button.play_button')[0].getBoundingClientRect().height; return {x: menuX, y: menuY, width: $('.js-play_button.play_button')[0].getBoundingClientRect().width};}; menuPos();" in document 1
	end tell
	
	--TODO: To stop playback call javascript __hboPlayerProxy("complete")
	
	set menuPosX to get x of menuPos as integer
	set menuPosY to get y of menuPos as integer
	set playerWidth to get width of menuPos as integer
	
	--TODO: figure out a smarter way to wait for spinner to disappear and playback to start - javascript maybe?
	delay 5
	
	-- Magic constant TODO: Figure out a failsafe way to get playback controls coordinates
	set controlsIconWidth to 66 --Fixed size
	set controlsIconHeight to 66 --Fixed size
	set controlsVerticalDelimiter to 1 --Fixed size
	
	-- TODO: Detect what icons are available. Sometimes subtitles icon is not shown, which means the HD icon moves up a position
	set volumeIconRightOffset to ((0 * (controlsIconWidth + controlsVerticalDelimiter)) + (0.5 * controlsIconWidth)) as integer
	set fullscreenIconRightOffset to ((1 * (controlsIconWidth + controlsVerticalDelimiter)) + (0.5 * controlsIconWidth)) as integer
	set subtitlesIconRightOffset to ((2 * (controlsIconWidth + controlsVerticalDelimiter)) + (0.5 * controlsIconWidth)) as integer
	set hdIconRightOffset to ((3 * (controlsIconWidth + controlsVerticalDelimiter)) + (0.5 * controlsIconWidth)) as integer
	
	set clickPosY to menuPosY - (0.5 * controlsIconHeight)
	
	set fullscreenIconOffset to (menuPosX + playerWidth - fullscreenIconRightOffset) as integer
	log "Fullscreen icon offset: " & fullscreenIconOffset
	
	--Going fullscreen
	log "Going fullscreen"
	tell application "Safari" to activate
	do shell script quoted form of POSIX path of cliclickPath & " m:" & fullscreenIconOffset & "," & clickPosY & " w:500 c:."
	set fullscreen to true
	
	set res to GetResolution()
	set screenHorizontalRes to item 3 in res
	set screenVerticalRes to item 4 in res
	set clickPosY to screenVerticalRes - (0.5 * controlsIconHeight)
	
	delay 1
	
	log "Switching to HD stream"
	--tell application "Safari" to activate
	do shell script quoted form of POSIX path of cliclickPath & " c:" & (screenHorizontalRes - hdIconRightOffset) & "," & clickPosY --& " w:200 c:."
	
end run

on GetResolution()
	tell application "Finder" to get bounds of window of desktop
end GetResolution

on GetParentPath(theFile)
	tell application "Finder" to return container of (theFile as alias) as text
end GetParentPath
