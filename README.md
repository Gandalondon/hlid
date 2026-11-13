# Woden

Test build of the Woden app concept: the clickable prototype (app C) full screen on Android. Walks, GPS and the Google Maps hand-off are mocked.

Install: on the Pixel, open the latest release of this repo and tap `Woden.apk`.

- The page is `app/src/main/assets/index.html`: app C from ~/Woden/app/app-c.html (with its build 4 fixes and test walk blocks) plus the app-mode block (no frame, laid out between the status and gesture bars).
- Every push to main builds a release (GitHub Actions, same as Rinse).
- No signing secret yet, so each build has its own key: uninstall before installing a new one. Add SIGNING_KEYSTORE_B64 and SIGNING_PASSWORD (alias woden) to fix that.

## Test walk (build 4)

The app opens on a test walk: Cannon Hill Common, no drive. Walk there shows the way to the start with live GPS; it says You're here when you are within 30 m. Start walk turns the map heading-up with the compass, shows km to go along the route and records a GPS trace; End walk saves it as GPX to Downloads/Woden. Another walk goes to the prototype's four walks (and back to the test after the fourth).

- Loop: the footpaths round Cannon Hill Common from OpenStreetMap (1.9 km), shading from OS Terrain 50 (TQ26, TQ27). Data built by tools/testwalk/ (loop.py, relief.py, testdata.py).
- Native: TrackService (GPS as a foreground service, so it keeps going with the screen off), compass from the rotation vector sensor (true north), pictures to Pictures/Woden.
