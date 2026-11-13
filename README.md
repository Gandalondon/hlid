# Woden

Test build of the Woden app concept: the clickable prototype (app C) full screen on Android. Walks, GPS and the Google Maps hand-off are mocked.

Install: on the Pixel, open the latest release of this repo and tap `Woden.apk`.

- The page is `app/src/main/assets/index.html`: app C from ~/Woden/app/app-c.html plus a small app-mode block at the end (no frame, scaled to the phone's width).
- Every push to main builds a release (GitHub Actions, same as Rinse).
- No signing secret yet, so each build has its own key: uninstall before installing a new one. Add SIGNING_KEYSTORE_B64 and SIGNING_PASSWORD (alias woden) to fix that.
