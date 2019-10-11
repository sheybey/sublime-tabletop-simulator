# Tabletop Simulator for Sublime Text 3
This plugin implements the [external editor API][api] provided by Tabletop
Simulator to allow use of Sublime Text 3 as the Lua editor.

## Installation
Create the appropriate folder and put the contents of the repository in it.

 -  Windows: `%APPDATA%\Sublime Text 3\Packages\Tabletop Simulator\`
 -  Linux: `~/.config/sublime-text-3/Packages/Tabletop Simulator/`
 -  OS X: `~/Library/Application Support/Sublime Text 3/Packages/Tabletop
    Simulator/`

You can quickly locate the Packages folder by opening Sublime and clicking
`Preferences -> Browse Packages...`

## Usage
 1. Launch Tabletop Simulator and load a save
 2. Either open all existing scripts (`Tools -> Tabletop Simulator -> Get
    Scripts`) or open a particular object's script by right-clicking it in
    Tabletop Simulator and choosing `Scripting -> Lua editor`
 3. Send the edited scripts back to Tabletop Simulator: `Tools -> Tabletop
    Simulator -> Send Scripts`

## Notes
 -  UI XML editing is currently unsupported. This means that **any existing UI
    XML will be lost if you use this plugin.**
 -  The only way to send scripts back is to send all of them by using the
    "Send Scripts" command. Individual editing of objects is not possible.

[api]: https://api.tabletopsimulator.com/externaleditorapi/
