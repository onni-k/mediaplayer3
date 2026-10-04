@@
     def __init__(self, session, playback_controller=None):
@@
         self._focus = "stations"
+
+        # Device test round 2026-10-04 -- long CH+/CH- press events can
+        # repeat while the first page-scroll is still settling; without a
+        # short guard, the box can start treating the continued key repeat as
+        # a normal DOWN/UP event for another panel. This single guard keeps
+        # the page-jump on the currently focused panel until the repeat burst
+        # has drained, instead of letting it fall through to the Stations
+        # column after a single region/language page-scroll.
+        self._page_scroll_in_progress = False
+        self._page_scroll_guard_timer = eTimer()
+        self._page_scroll_guard_timer.callback.append(self._clearPageScrollGuard)
@@
     def pageUp(self) -> None:
         """
         CH+ -- jump PAGE_STEP entries up in the focused panel
         (requested after real device testing). Clamped so it stops at
         the top of the list instead of wrapping around when fewer
         than PAGE_STEP entries remain (round 80, per direct request).
         """
+
+        if self._page_scroll_in_progress:
+
+            return
+
+        self._page_scroll_in_progress = True
+        self._page_scroll_guard_timer.start(120, True)
 
         logger.verbose("[RadioBrowser] CH+ pressed. focus=%s", self._focus)
@@
     def pageDown(self) -> None:
+
+        if self._page_scroll_in_progress:
+
+            return
+
+        self._page_scroll_in_progress = True
+        self._page_scroll_guard_timer.start(120, True)
 
         logger.verbose("[RadioBrowser] CH- pressed. focus=%s", self._focus)
@@
         self._onSelectionChanged()
+
+    # ------------------------------------------------------------------
+
+    def _clearPageScrollGuard(self) -> None:
+
+        self._page_scroll_in_progress = False
 
     # ------------------------------------------------------------------
