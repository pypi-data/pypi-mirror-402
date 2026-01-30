# Skyset

Skyset is a tiny, file-based contract for sharing a live visual theme between apps. One producer writes latest.yml; many consumers read it to sync their look. It keeps coupling low: no IPC, just a shared file.

This repo is a command-line based editor for the format.

## Example Uses

-   The Coppelia music player sets a system-wide theme based on the currently playing album art
-   Get the current weather conditions outside and set your terminal colors and wallpaper accordingly
-   Coordinate your apps' themes to match images on your desktop
-   Shift your whole environment gradually to match the time of day
