# pymidisoundboard

A simple gstreamer-based soundboard triggered by MIDI, with a Qt configuration interface.

## Status

This is the culmination of about four hours of effort, so set your expectations appropriately.

Right now, there's a hardcoded number of rows and columns in the UI. The UI/UX isn't great in general.

However, you can:

- Choose a MIDI device
- Choose sound clips
- Play a note to map it to a clip
- Trigger that note again layer

And that's about it.

Config persists to a dotfile created in your home directory.
