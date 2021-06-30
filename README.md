# pymidisoundboard

A simple gstreamer-based soundboard triggered by MIDI, with a Qt configuration interface.

![screenshot](/screenshot.png)

## Status

This is the culmination of about ~~four~~ six hours of effort, so set your expectations appropriately.

Features include:

- Choosing a MIDI device
- Choosing sound clips
- Playing a note to map it to a clip
- Triggering that note again later to play the clip
- Creating multiple banks with their own note and sample mappings
- Changing banks via MIDI CC (control change) or by selecting the tab
- Configuring the number of rows, columns, and banks in the UI

And that's about it.

Config persists to a dotfile created in your home directory.
