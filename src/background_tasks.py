# -*- coding: utf-8 -*-
"""
Background tasks (1.5.000).

Long network jobs (lyrics / cover art downloads, radio station searches and
database updates, song identification / submission) run in daemon threads so the
user interface never waits for them. This module

  * runs a job in a thread and delivers its result to a callback IN THE GUI
    THREAD (a 200 ms eTimer polls for finished jobs; Enigma2 widgets must only be
    touched from the GUI thread),
  * lets a newer job replace an older one with the same key (the old result is
    dropped),
  * lets a screen cancel jobs that only matter to it (cancelOwner) and the plugin
    cancel everything on exit (cancelAll); jobs without an owner (downloads) go on when
    the screen that started them is closed -- jobs get a threading.Event they
    should check between steps,
  * keeps the list of running tasks that every screen shows in its header row
    (attachBanner -> bannerText).
"""

import threading
from typing import Any, Callable, List, Optional

from .localization import _
from .logger import logger

POLL_MS = 200
BANNER_MS = 1000


class _Job:

    def __init__(self, key, label, func, callback, owner) -> None:
        self.key = key
        self.label = label
        self.func = func
        self.callback = callback
        self.owner = owner
        self.stop = threading.Event()
        self.cancelled = False
        self.finished = False
        self.result: Any = None
        self.error: Optional[BaseException] = None
        self.thread: Optional[threading.Thread] = None

    def run(self) -> None:
        try:
            self.result = self.func(self.stop)
        except BaseException as error:  # noqa: BLE001 - delivered to the callback
            self.error = error
            logger.info("[Background] job '%s' failed: %s", self.label, error)
        finally:
            self.finished = True


_lock = threading.Lock()
_jobs: List[_Job] = []
_providers: List[Callable[[], str]] = []
_timer = None


def _poll() -> None:
    """GUI thread: deliver finished jobs, stop polling when idle."""

    global _timer

    done: List[_Job] = []

    with _lock:
        for job in list(_jobs):
            if job.finished:
                _jobs.remove(job)
                done.append(job)

    for job in done:
        if job.cancelled or job.callback is None:
            continue
        try:
            job.callback(job.result, job.error)
        except Exception as error:
            logger.info("[Background] callback of '%s' failed: %s", job.label, error)

    # decided AFTER the callbacks: a callback may have started a new job (e.g. filters -> search)
    with _lock:
        idle = not _jobs

    if idle and _timer is not None:
        try:
            _timer.stop()
        except Exception:
            pass


def _ensureTimer() -> None:

    global _timer

    if _timer is None:
        from enigma import eTimer

        _timer = eTimer()
        _timer.callback.append(_poll)

    _timer.start(POLL_MS, False)


def start(label: str, func: Callable[[threading.Event], Any], callback: Optional[Callable[[Any, Optional[BaseException]], None]] = None, owner: Any = None, key: str = "") -> _Job:
    """
    Run `func(stop_event)` in a thread. `callback(result, error)` is called in the GUI
    thread when it ends (not when it was cancelled). A running job with the same `key` is
    cancelled first. Call from the GUI thread.
    """

    job = _Job(key, label, func, callback, owner)

    with _lock:
        if key:
            for old in _jobs:
                if old.key == key:
                    old.cancelled = True
                    old.stop.set()
        _jobs.append(job)

    job.thread = threading.Thread(target=job.run, name="MP3Bg-" + (key or "job"), daemon=True)
    job.thread.start()

    _ensureTimer()

    return job


def cancelOwner(owner: Any) -> None:
    """Cancel the jobs of a screen that is closing (their callbacks will not run)."""

    with _lock:
        for job in _jobs:
            if job.owner is owner:
                job.cancelled = True
                job.stop.set()


def cancelAll() -> None:
    """Plugin exit: stop everything."""

    with _lock:
        for job in _jobs:
            job.cancelled = True
            job.stop.set()

    if _timer is not None:
        try:
            _timer.stop()
        except Exception:
            pass


def registerProvider(provider: Callable[[], str]) -> None:
    """A function returning the label of a task that runs elsewhere ('' when idle)."""

    _providers.append(provider)


def activeLabels() -> List[str]:

    labels: List[str] = []

    with _lock:
        # a job with an empty label is "silent" (not shown in the header row)
        labels += [job.label for job in _jobs if job.label and not job.cancelled and not job.finished]

    for provider in _providers:
        try:
            text = provider()
        except Exception:
            text = ""
        if text:
            labels.append(text)

    return labels


def bannerText() -> str:

    labels = activeLabels()

    if not labels:
        return ""

    return labels[-1] if len(labels) == 1 else f"{labels[-1]} (+{len(labels) - 1})"


def attachBanner(screen: Any, name: str = "task_banner") -> None:
    """
    Give `screen` a label widget `name` (the skin must contain it) that shows bannerText()
    while the screen is visible. Call in __init__ after Screen.__init__.
    """

    from enigma import eTimer
    from Components.Label import Label

    screen[name] = Label("")

    state = {"text": None}

    def update() -> None:
        text = bannerText()
        if text == state["text"]:
            return
        state["text"] = text
        try:
            screen[name].setText(text)
        except Exception:
            pass

    timer = eTimer()
    timer.callback.append(update)

    # keep a reference on the screen (otherwise the timer is garbage collected)
    screen._task_banner_timer = timer

    def shown() -> None:
        state["text"] = None
        update()
        timer.start(BANNER_MS, False)

    def closed() -> None:
        try:
            timer.stop()
        except Exception:
            pass

    screen.onShown.append(shown)
    screen.onClose.append(closed)


def _headerLabelClass():
    """Built lazily so this module imports without Enigma2 (tests)."""

    from Components.Label import Label

    class HeaderLabel(Label):
        """
        A screen's header/status label that appends the running background task to its text
        ("Music Library - Downloading lyrics...") so the indicator is centred with the title.
        setText() keeps working as before: it sets the base text.
        """

        def __init__(self, text=""):
            self._base = text
            self._suffix = ""
            Label.__init__(self, text)

        def setText(self, text):
            self._base = text
            self._render()

        def setSuffix(self, suffix):
            if suffix != self._suffix:
                self._suffix = suffix
                self._render()

        def _render(self):
            shown = f"{self._base}  -  {self._suffix}" if self._suffix and self._base else (self._suffix or self._base)
            Label.setText(self, shown)

    return HeaderLabel


def makeHeaderLabel(text=""):
    return _headerLabelClass()(text)


def watchHeader(screen: Any, name: str = "status") -> None:
    """Keep the task text in screen[name] (made with makeHeaderLabel) up to date while the screen is shown."""

    from enigma import eTimer

    def update() -> None:
        try:
            screen[name].setSuffix(bannerText())
        except Exception:
            pass

    timer = eTimer()
    timer.callback.append(update)
    screen._header_banner_timer = timer

    def shown() -> None:
        update()
        timer.start(BANNER_MS, False)

    def closed() -> None:
        try:
            timer.stop()
        except Exception:
            pass

    screen.onShown.append(shown)
    screen.onClose.append(closed)
