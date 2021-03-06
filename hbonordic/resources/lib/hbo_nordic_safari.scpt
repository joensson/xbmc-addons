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
		
		tell (window 1 where (its document is not missing value))
			if name of its document is not "Untitled" then set current tab to (make new tab)
			set index to 1
		end tell
		set URL of document 1 to episodeUrl
		
		activate
		
		--If on a slow network it can take some time before Safari resolves DNS etc and starts loading the url
		my debug("Waiting for Safari to begin loading episode URL")
		set startTime to (get current date)
		repeat
			set props to (get properties of document 1)
			if ((get URL of props is episodeUrl) and (get name of props is not "Untitled")) then exit repeat
			delay 0.5
		end repeat
		set duration to (get current date) - startTime
		my debug("Waited " & duration & " seconds for Safari to begin loading document")
		
		my debug("Waiting for Safari to finish loading episode URL")
		set startTime to (get current date)
		repeat
			if (do JavaScript "document.readyState" in document 1) is "complete" then exit repeat
			delay 0.5
		end repeat
		set duration to (get current date) - startTime
		my debug("Waited " & duration & " seconds for readyState to be 'complete'")
		
		--Login if not logged in already
		if (do JavaScript "$('.js-toggle_login_form').length" in document 1) is 1 then
			my debug("Logging in")
			do JavaScript "var doLogin = function() {$('.js-toggle_login_form')[0].click(); $('#login_email')[0].value='" & username & "'; $('#login_password')[0].value='" & userpass & "'; $('#sign_in_form').submit();}; doLogin();" in document 1
			delay 1.5
		end if
		
		my debug("Get screen coordinates of windowed playback area")
		delay 1
		-- TODO: Figure out a failsafe way to get playback controls coordinates when player is windowed
		--		set menuPos to (do JavaScript "function findPos(obj) { var curleft = curtop = 0; if (obj.offsetParent) { do { curleft += obj.offsetLeft; curtop += obj.offsetTop;} while (obj = obj.offsetParent);}curtop += window.screenY+26curleft += window.screenLeftreturn [curleft,curtop];}; var menuPos = function () { var divPos=findPos($(\"div.js-play_button.play_button.pointer.absolute.topleft.z_10.full_width.full_height.transition_fade.no_select\")[0]); return {x: divPos[0], y: divPos[1], pageYOffset: $(window).get(0).pageYOffset, width: $(\"div.js-play_button.play_button.pointer.absolute.topleft.z_10.full_width.full_height.transition_fade.no_select\")[0].getBoundingClientRect().width, height: $(\"div.js-play_button.play_button.pointer.absolute.topleft.z_10.full_width.full_height.transition_fade.no_select\")[0].getBoundingClientRect().height};}; menuPos();" in document 1)
		set menuPos to (do JavaScript "function getPosition(element) {var xPosition = 0;var yPosition = 0;while(element) {xPosition += (element.offsetLeft - element.scrollLeft + element.clientLeft);yPosition += (element.offsetTop - element.scrollTop + element.clientTop);element = element.offsetParent;}return { x: xPosition, y: yPosition };};var myPos = function () {var elem = $(\"div.js-play_button.play_button.pointer.absolute.topleft.z_10.full_width.full_height.transition_fade.no_select\")[0]; var pos = getPosition(elem); var boundingClientRect = elem.getBoundingClientRect();return {x: pos.x, y: pos.y+boundingClientRect.height+94+22, pageYOffset: $(window).get(0).pageYOffset, width: boundingClientRect.width, height: boundingClientRect.height};}; myPos();" in document 1)
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
		if pageYOffset > 0 then
			menuPosY = menuPosY - pageYOffset
			my debug("menuPosY > screenheight, adjusted menuPosY to " & menuPosY)
		end if
		if menuPosY > screenVerticalRes then
			my warn("menuPosY: " & menuPosY & " greater than screen height " & screenVerticalRes & " - pageYOffset: " & pageYOffset & ". Script cannot continue")
			error number -128
		end if
	end if
	
	my info("Click Play")
	do shell script quoted form of POSIX path of cliclickPath & " m:" & (menuPosX + 0.5 * playerWidth) & "," & (menuPosY - 0.5 * playerHeight) & " w:300 c:."
	delay 3 --TODO: figure out a smarter way to wait for flash spinner to disappear and playback to start - javascript event of xhr request completed?
	
	
	-- TODO: Detect what icons are available. Sometimes subtitles icon is not shown, which means the HD icon moves up a position
	--Play/pause icon is all to the left
	set playIconLeftOffset to 0.5 * controlsIconWidth
	set volumeIconRightOffset to ((0 * (controlsIconWidth + controlsVerticalDelimiter)) + (0.5 * controlsIconWidth)) as integer
	set fullscreenIconRightOffset to ((1 * (controlsIconWidth + controlsVerticalDelimiter)) + (0.5 * controlsIconWidth)) as integer
	set subtitlesIconRightOffset to ((2 * (controlsIconWidth + controlsVerticalDelimiter)) + (0.5 * controlsIconWidth)) as integer --sometimes not shown, how do we detect this?
	set hdIconRightOffset to ((3 * (controlsIconWidth + controlsVerticalDelimiter)) + (0.5 * controlsIconWidth)) as integer
	
	set clickPosY to menuPosY - (0.5 * controlsIconHeight) --Screen Y position measured from screen top to center of control icons (windowed mode)
	set fullscreenIconWindowedX to (menuPosX + playerWidth - fullscreenIconRightOffset) as integer -- 
	
	debug("Fullscreen-icon x,y in windowed mode: (" & fullscreenIconWindowedX & ", " & clickPosY & ")")
	
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
	
	my info("Script completed")
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