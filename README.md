# OctoPrint-hueCommands
This Plugin was inspired by [GCODE System Commands Plugin](https://plugins.octoprint.org/plugins/gcodesystemcommands/).
Instead of executing local system commands you control your [Philips hue](https://www.meethue.com/) resources.

# Known issues: NOT WORKING with OctoPrint 1.5.1

## Version 0.2.3 

## Features
* Configure presets with colors, assigned resources (Light and/or Groups) and timing.
* Set hue resources with *GCODE* commands (e.g. Terminal window, OctoPrint **GCODE Scripts**).
![GCODE Scripts](https://raw.githubusercontent.com/LMS0815/OctoPrint-hueCommands/master/screenshots/huecommands_GCODE.png "hueCommands scripting")
* Control resources per command line or sidebar buttons.
![Sidebar](https://raw.githubusercontent.com/LMS0815/OctoPrint-hueCommands/master/screenshots/huecommands_sidebar.png "hueCommands settings")
* Discover hue bridge.
* Dialog to create hue user.


## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

[https://github.com/LMS0815/OctoPrint-hueCommands/archive/master.zip](https://github.com/LMS0815/OctoPrint-hueCommands/archive/master.zip)

### Hue Bridge Configuration

hueCommands requires 3 settings to function
1. The IP Address of you hue bridge selectable from drop down list after discovery.
2. A User for OctoPrint to use when contacting your bridge which can be created by pushing the bridge button.
3. The numeric ID of your hue resources(lights or groups) which are available from drop down list when you are connected to a hue bridge.

## Hue User for OctoPrint
If you have a user name already, enter it and use the asterisk for testing your connection.
To find or configure these can be found in [How to Develop for Hue - Getting Started](https://developers.meethue.com/develop/get-started-2/)

To create a user name, leave the field empty and enter a device name or click the asterisk button to create one.
After that  press the button of your bridge and than click the asterisk button a second time.

### Light and Group ID's

As soon you are connected to your hue bridge, the IDs are available as drop down menu.


#### To control multiple lights:

If a the lights are not yet grouped, use the Hue app (or API directly if you're feeling hardcore) to create a room or zone consisting of the intended lights.

Once done, the list of available Group ID's can be found at:
`https://<bridgeaddr>/api/<hueusername>/groups`


## Configuration

Once you have the hue IP, user name, enter these into the appropriate field in hueCommands menu in settings.
Use the Light/Group ID for settings

![Settings](https://raw.githubusercontent.com/LMS0815/OctoPrint-hueCommands/master/screenshots/huecommands_settings.png "hueCommands settings")

## Examples

Examples|Effect
-|-
```hue $RED```|Switch lamp/group on using preset *RED*
```hue off $RED```|Switch lamp/group off using preset *RED*
```hue L15 off```|Switch lamp 15 off.
```hue L15 D2.5 #000000```|Transition lamp 15 in 2.5 sec to last state.
```hue L15 M1 on```|Transition lamp 15 in 1.5 sec to last state.
```hue L15 #808080```|Switch Lamp 15 Gray (= 50% White).
```hue G8 %50 #FFFFFF```|Switch group 15 to 50% White (= Gray).
```hue G8 M1:30 %100 #C0C0C0```|Transition group 15 in 90 sec to 100% Silver (= White).


# hue Command syntax

```
   hue [$preset]
       [[Ln]/[Gn]]
       [[on]/[off]]
       [[Tnnnnn]/[Dnnnn]/[Mhh:mm:ss]]
       [[#nnnnnn]/[Knnnnnn]]
       [Bbbb]/[%ppp]
       [[Sbbb]/[Vppp]]
```

Preset|Description
-|-
**preset ID**|Preset ID from the list above. Not all values must be set; Zero (0) values are ignored.

Device|Description
-|-
**L**n|Lamp with device number n
**G**n|Group with device number n

State|Description
-|-
**on**|Switch on
**off**|Switch off

Transition time|Description
-|-
**T**nnnnn|Transitiontime n in 1/10 seconds between 0 and 65535
**D**nnnn.n|Duration-/Transitiontime n in seconds between 0 and 6553.5
**M**hh:mm:ss.h|Transitiontime in time format between 0:00:00 and 1:49:13.5

Color commands|Description
-|-
#rrggbb|RGB color Red/Green/Blue
**K**nnnnnn|color temperature n in Kelvin
**C**nnnnnn|color temperature n between 0 and 65535

Brightness commands|Description
-|-
**B**bbb|Brightness b between 1 and 254
%ppp.p|Brightness p in percent between 0.0 and 100.0

Saturation commands|Description
-|-
**S**bbb|Saturation b between 0 and 254
**V**ppp.p|Saturation value p in percent between 0.0 and 100.0

Hue commands|Description
-|-
**H**nnnnnn|Hue n between 0 and 65535
**U**ppp.p|Hue p in percent between 0.0 and 100.0


## Support My Efforts
I programmed this plugin for fun and do my best effort to support those that have issues with it, please return the favor and support me.

[![paypal](https://www.paypalobjects.com/digitalassets/c/website/marketing/emea/de/de/logo-center/M2_Logo_02.jpg)](https://paypal.me/stonehome/5 "PayPal.me")
