-- This script depends on cliclick to perform mouseclicks
--	http://www.bluem.net/en/mac/cliclick/

on run argv
	set scriptfile to POSIX file (POSIX path of (path to me))
	set scriptfilefolder to GetParentPath(scriptfile)
	set scriptdir to POSIX path of scriptfilefolder
	set cliclickPath to scriptdir & "cliclick"
	
	set episodeUrl to item 1 of argv
	set username to item 2 of argv
	set userpass to item 3 of argv
	
	-- Get display resolution
	set res to GetResolution()
	set screenHorizontalRes to item 3 in res
	set screenVerticalRes to item 4 in res
	
	set controlsIconWidth to 66 --Fixed size
	set controlsIconHeight to 66 --Fixed size
	set controlsVerticalDelimiter to 1 --Fixed size
	
	
	debug("Loading episode url " & episodeUrl)
	
	-- Close existing tabs on HBO Nordic
	tell application "Safari"
		reopen
		set hboNordicTabTitle to "HBO Nordic" as string
	    close (every tab of window 1 whose name is equal to hboNordicTabTitle)
	end tell
	delay 1
	
	-- wait for the page to be ready before executing rest of script
	tell application "Safari"
		reopen
		activate
	    tell (window 1 where (its document is not missing value))
    	    if name of its document is not "Untitled" then set current tab to (make new tab)
        	set index to 1
	    end tell
    	set URL of document 1 to episodeUrl
--		set the URL of the front document to episodeUrl
		delay 2 --TODO: Is there an event we can check to see when Safari starts loading the new URL. If we check document.readyState too soon the 'old' page will return complete and the script will continue before the new page is loaded

		my debug("Waiting for Safari to finish loading episode URL")
		set startTime to (get current date)
		repeat
			if (do JavaScript "document.readyState" in document 1) is "complete" then exit repeat
			delay 1
		end repeat
		set duration to (get current date) - startTime
		my debug("Waited " & duration & " seconds for readyState to be 'complete'")
		
		--Login if not logged in already
		if (do JavaScript "$('.js-toggle_login_form').length" in document 1) is 1 then
			my debug("Logging in")
			do JavaScript "var doLogin = function() {$('.js-toggle_login_form')[0].click(); $('#login_email')[0].value='" & username & "'; $('#login_password')[0].value='" & userpass & "'; $('#sign_in_form').submit();}; doLogin();" in document 1
			delay 1
		end if
(*
		my debug("Wait for browser to scroll to play icon")
		set startTime to (get current date)
		repeat
			if (do JavaScript "var isScrolledIntoView = function(elem) { var docViewTop = $(window).get(0).pageYOffset; var docViewBottom = docViewTop + $(window).height(); var elemTop = $(elem).offset().top; var elemBottom = elemTop + $(elem).height(); return ((elemBottom <= docViewBottom) && (elemTop >= docViewTop));}; isScrolledIntoView($('.js-play_button.play_button').get(0))" in document 1) is "false" then
				my debug("Calling scrollIntoView directly on play button element")
				delay 1
			else
				set duration to (get current date) - startTime
				my debug("Play icon is visible - waited for " & duration & " seconds")
				exit repeat
			end if
		end repeat
*)	
	
		my debug("Get screen coordinates of windowed playback area")
		delay 0.5
		do JavaScript "$('.js-play_button.play_button').get(0).scrollIntoView()" in document 1
		delay 0.5
		-- TODO: Figure out a failsafe way to get playback controls coordinates when player is windowed
		set menuPos to (do JavaScript "var menuPos = function () { var menuX = window.screenX + $('.js-play_button.play_button')[0].getBoundingClientRect().left; var menuY = window.screenY + window.screen.availTop + (window.screen.height - window.screen.availHeight) + $('.js-play_button.play_button')[0].getBoundingClientRect().top + $('.js-play_button.play_button')[0].getBoundingClientRect().height; return {x: menuX, y: menuY, pageYOffset: $(window).get(0).pageYOffset, width: $('.js-play_button.play_button')[0].getBoundingClientRect().width, height: $('.js-play_button.play_button')[0].getBoundingClientRect().height};}; menuPos();" in document 1)
		my debug("Playback element - X: " & (get x of menuPos) & ", Y: " & (get y of menuPos) & " (playerWidth: " & (get width of menuPos) & ", playerHeight: " & (get height of menuPos) & ", pageYOffset (scroll distance from page top): " & (get pageYOffset of menuPos) & ")")

	end tell

	set menuPosX to get x of menuPos as integer
	set menuPosY to get y of menuPos as integer
	set playerWidth to get width of menuPos as integer
	set playerHeight to get height of menuPos as integer
	set pageYOffset to get pageYOffset of menuPos as integer
	
	if menuPosX > screenHorizontalRes then
		my warn("menuPosX greater than screen width. Script cannot continue")
		error number -128
	end if
	if menuPosY > screenVerticalRes then
		my warn("menuPosY: " & menuPosY & " greater than screen height " & screenVerticalRes & " - pageYOffset: " & pageYOffset & ". Script cannot continue")
		error number -128
	end if
	
	my info("Click Play")
	do shell script quoted form of POSIX path of cliclickPath & " m:" & (menuPosX + 0.5 * playerWidth) & "," & (menuPosY - 0.5 * playerHeight) & " w:300 c:."
	delay 3 --TODO: figure out a smarter way to wait for flash spinner to disappear and playback to start - javascript event of xhr request completed?
	
	
	-- TODO: Detect what icons are available. Sometimes subtitles icon is not shown, which means the HD icon moves up a position
	--Play/pause icon is all to the left
	set playIconLeftOffset to 0.5*controlsIconWidth
	set volumeIconRightOffset to ((0 * (controlsIconWidth + controlsVerticalDelimiter)) + (0.5 * controlsIconWidth)) as integer
	set fullscreenIconRightOffset to ((1 * (controlsIconWidth + controlsVerticalDelimiter)) + (0.5 * controlsIconWidth)) as integer
	set subtitlesIconRightOffset to ((2 * (controlsIconWidth + controlsVerticalDelimiter)) + (0.5 * controlsIconWidth)) as integer --sometimes not shown, how do we detect this?
	set hdIconRightOffset to ((3 * (controlsIconWidth + controlsVerticalDelimiter)) + (0.5 * controlsIconWidth)) as integer
	
	set clickPosY to menuPosY - (0.5 * controlsIconHeight) --Screen Y position measured from screen top to center of control icons (windowed mode)
	
	set fullscreenIconWindowedX to (menuPosX + playerWidth - fullscreenIconRightOffset) as integer -- 
	debug("Fullscreen icon X in windowed mode: " & fullscreenIconWindowedX)
	
	--Going fullscreen
	set fullscreen to false
	tell application "Safari"
		my info("Going fullscreen")
		activate
		delay 2.5
		--clickPosY uses windowed coordinates at this point
		do shell script quoted form of POSIX path of cliclickPath & " m:" & fullscreenIconWindowedX & "," & clickPosY & " w:500 c:."
		set fullscreen to true --TODO: How to verify that fullscreen happened
	end tell
	
	--update clickPosY to accomodate for fullscreen coordinates
	set clickPosY to screenVerticalRes - (0.5 * controlsIconHeight)
	delay 1.5
	
	tell application "Safari"
		activate
		my info("Switching to HD stream")
		-- Workaround: Some series does not have a subtitles icon - so the HD icon is offset 1 to the right - attempt click in both positions
		do shell script quoted form of POSIX path of cliclickPath & " m:" & (screenHorizontalRes - subtitlesIconRightOffset) & "," & clickPosY & " w:100 c:."
		delay 0.5
		do shell script quoted form of POSIX path of cliclickPath & " m:" & (screenHorizontalRes - hdIconRightOffset) & "," & clickPosY & " w:100 c:."
	end tell
	
end run

on GetResolution()
	tell application "Finder" to get bounds of window of desktop
end GetResolution

on GetParentPath(theFile)
	tell application "Finder" to return container of (theFile as alias) as text
end GetParentPath

on debug(msg)
	log ("[DEBUG] " & msg)
end debug

on info(msg)
	log ("[INFO] " & msg)
end info

on warn(msg)
	log ("[WARN] " & msg)
end warn