-- copy "ofbiz quick open.scpt.applescript" into ~/Application Support/BBEdit/Scripts
-- execute following command in above path:
-- $ osacompile -o "ofbiz quick open.scpt" "ofbiz quick open.scpt.applescript"
tell application "BBEdit"
	set fwLst to {"base", "bi", "common", "datafile", "entity", "entityext", "example", "exampleext", "guiapp", "minilang", "security", "service", "webapp", "webslinger", "webtools", "widget"}
	set apLst to {"accouting", "commmonext", "content", "humanres", "manufacturing", "marketing", "order", "party", "product", "securityext", "workeffort"}
	set spLst to {"assetmaint", "cmssite", "ebay", "ecommerce", "googlebase", "googleCheckout", "hhfacility", "ldap", "myportal", "oagis", "pos", "projectmgr", "shark", "webpos", "workflow"}
	
	set sSelFnd to ""
	set sKndLen to 0
	tell text window 1
		select line (startLine of selection)
		set sSel to selection as text
		set iPage to offset of "page=\"" in sSel
		set iLocation to offset of "location=\"" in sSel
		if iPage > 0 then
			set sSelFnd to find "page=\"[^\"]+\"" options {search mode:grep, returning results:true} searching in selection
			set sKndLen to 4
		end if
		if iLocation > 0 then
			set sSelFnd to find "location=\"[^\"]+\"" options {search mode:grep, returning results:true} searching in selection
			set sKndLen to 8
		end if
	end tell
	
	if found of sSelFnd then
		set filename to file of text window 1 as text
		set AppleScript's text item delimiters to ":"
		set fn_a to get every text item of filename
		
		set sTargetFile to found text of sSelFnd
		set iComp to offset of "component://" in sTargetFile
		if iComp > 0 then
			set sTargetFile to text (sKndLen + 14) thru ((length of sTargetFile) - 1) of sTargetFile
			set AppleScript's text item delimiters to "/"
			set tf_a to get every text item of sTargetFile
			set res to "framework"
			set ian to 0
			repeat with i from 1 to (length of fn_a)
				set istr to item i of fn_a
				if istr = "framework" or istr = "applications" or istr = "specialpurpose" then
					set res to istr
					set ian to i
					exit repeat
				end if
			end repeat
			set fn_c to (items 1 thru (ian - 1) of fn_a)
			set tf_1st to item 2 of tf_a
			if fwLst contains tf_1st then
				set fn_c to fn_c & {"framework"}
			else if apLst contains tf_1st then
				set fn_c to fn_c & {"applications"}
			else if spLst contains tf_1st then
				set fn_c to fn_c & {"specialpurpose"}
			end if
			set fn_c to fn_c & (items 2 thru (length of tf_a) of tf_a)
		else
			-- todo: open not component:// ... i.e. *ftl
			set sTargetFile to text (sKndLen + 3) thru ((length of sTargetFile) - 1) of sTargetFile
		end if
		
		set AppleScript's text item delimiters to ":"
		set target_filename to fn_c as text
		set sharp_idx to offset of "#" in target_filename
		set find_text to ""
		if sharp_idx > 0 then
			set AppleScript's text item delimiters to "#"
			set tfn_a to get every text item of target_filename
			set target_filename_alias to (item 1 of tfn_a as alias)
			set find_text to "name=\"" & (item 2 of tfn_a) & "\""
		else
			set target_filename_alias to target_filename as alias
		end if
		open target_filename_alias
		-- find text below #
		find find_text options {returning results:true} searching in text window 1 with selecting match
		find_text
	end if
end tell
