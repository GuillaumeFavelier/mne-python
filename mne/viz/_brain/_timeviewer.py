# Authors: Alexandre Gramfort <alexandre.gramfort@inria.fr>
#          Eric Larson <larson.eric.d@gmail.com>
#          Guillaume Favelier <guillaume.favelier@gmail.com>
#
# License: Simplified BSD

import time
import numpy as np


class IntSlider(object):
    """Class to set a integer slider."""

    def __init__(self, plotter=None, callback=None, name=None):
        self.plotter = plotter
        self.callback = callback
        self.name = name

    def __call__(self, value):
        """Round the label of the slider."""
        idx = int(round(value))
        for slider in self.plotter.slider_widgets:
            name = getattr(slider, "name", None)
            if name == self.name:
                slider_rep = slider.GetRepresentation()
                slider_rep.SetValue(idx)
                self.callback(idx)


class UpdateOrientation(object):
    """Class to update the orientation."""

    def __init__(self, plotter=None, callback=None,
                 orientation=None, label=None):
        self.plotter = plotter
        self.callback = callback
        self.orientation = orientation
        self.label = label

    def __call__(self, value):
        """Update the value of the label."""
        idx = int(round(value))
        orientation = self.orientation[idx]
        self.callback(orientation)
        self.label.SetInput(orientation)


class UpdateColorbarScale(object):
    """Class to update the values of the colorbar sliders."""

    def __init__(self, plotter=None, brain=None):
        self.plotter = plotter
        self.brain = brain

    def __call__(self, value):
        """Update the colorbar sliders."""
        self.brain.update_fscale(value)
        fmin = self.brain._data['fmin']
        fmid = self.brain._data['fmid']
        fmax = self.brain._data['fmax']
        for slider in self.plotter.slider_widgets:
            name = getattr(slider, "name", None)
            if name == "fmin":
                slider_rep = slider.GetRepresentation()
                slider_rep.SetValue(fmin)
            elif name == "fmid":
                slider_rep = slider.GetRepresentation()
                slider_rep.SetValue(fmid)
            elif name == "fmax":
                slider_rep = slider.GetRepresentation()
                slider_rep.SetValue(fmax)
            elif name == "fscale":
                slider_rep = slider.GetRepresentation()
                slider_rep.SetValue(1.0)


class BumpColorbarPoints(object):
    """Class that ensure constraints over the colorbar points."""

    def __init__(self, plotter=None, brain=None, name=None):
        self.plotter = plotter
        self.brain = brain
        self.name = name
        self.callback = {
            "fmin": brain.update_fmin,
            "fmid": brain.update_fmid,
            "fmax": brain.update_fmax
        }
        self.last_update = time.time()

    def __call__(self, value):
        """Update the colorbar sliders."""
        keys = ('fmin', 'fmid', 'fmax')
        vals = {key: self.brain._data[key] for key in keys}
        reps = {key: None for key in keys}
        for slider in self.plotter.slider_widgets:
            name = getattr(slider, "name", None)
            if name is not None:
                reps[name] = slider.GetRepresentation()
        if self.name == "fmin" and reps["fmin"] is not None:
            if vals['fmax'] < value:
                self.brain.update_fmax(value)
                reps['fmax'].SetValue(value)
            if vals['fmid'] < value:
                self.brain.update_fmid(value)
                reps['fmid'].SetValue(value)
            reps['fmin'].SetValue(value)
        elif self.name == "fmid" and reps['fmid'] is not None:
            if vals['fmin'] > value:
                self.brain.update_fmin(value)
                reps['fmin'].SetValue(value)
            if vals['fmax'] < value:
                self.brain.update_fmax(value)
                reps['fmax'].SetValue(value)
            reps['fmid'].SetValue(value)
        elif self.name == "fmax" and reps['fmax'] is not None:
            if vals['fmin'] > value:
                self.brain.update_fmin(value)
                reps['fmin'].SetValue(value)
            if vals['fmid'] > value:
                self.brain.update_fmid(value)
                reps['fmid'].SetValue(value)
            reps['fmax'].SetValue(value)
        if time.time() > self.last_update + 1. / 60.:
            self.callback[self.name](value)
            self.last_update = time.time()


class _TimeViewer(object):
    """Class to interact with _Brain."""

    def __init__(self, brain):
        self.brain = brain
        self.plotter = brain._renderer.plotter

        # scalar bar
        if brain._colorbar_added:
            scalar_bar = self.plotter.scalar_bar
            scalar_bar.SetOrientationToVertical()
            scalar_bar.SetHeight(0.6)
            scalar_bar.SetWidth(0.05)
            scalar_bar.SetPosition(0.02, 0.2)

        # smoothing slider
        default_smoothing_value = 7
        self.set_smoothing = IntSlider(
            plotter=self.plotter,
            callback=brain.set_data_smoothing,
            name="smoothing"
        )
        smoothing_slider = self.plotter.add_slider_widget(
            self.set_smoothing,
            value=default_smoothing_value,
            rng=[0, 15], title="smoothing",
            pointa=(0.82, 0.90),
            pointb=(0.98, 0.90)
        )
        smoothing_slider.name = 'smoothing'
        self.set_smoothing(default_smoothing_value)

        # orientation slider
        orientation = [
            'lateral',
            'medial',
            'rostral',
            'caudal',
            'dorsal',
            'ventral',
            'frontal',
            'parietal'
        ]
        self.orientation_label_actor = self.plotter.add_text(
            text=orientation[0],
            font_size=14,
            position=(0.9, 0.77),
            viewport=True,
        )
        prop = self.orientation_label_actor.GetTextProperty()
        prop.BoldOn()
        prop.SetJustificationToCentered()
        self.update_orientation = UpdateOrientation(
            plotter=self.plotter,
            callback=brain.show_view,
            orientation=orientation,
            label=self.orientation_label_actor,
        )
        orientation_slider = self.plotter.add_slider_widget(
            self.update_orientation,
            value=0,
            rng=[0, len(orientation) - 1],
            title='orientation',
            pointa=(0.82, 0.74),
            pointb=(0.98, 0.74),
            event_type='always'
        )

        # time label
        for hemi in brain._hemis:
            self.time_actor = brain._data.get(hemi + '_time_actor')
            if self.time_actor is not None:
                self.time_actor.SetPosition(0.5, 0.03)
                self.time_actor.GetTextProperty().SetJustificationToCentered()

        # time slider
        max_time = len(brain._data['time']) - 1
        time_slider = self.plotter.add_slider_widget(
            brain.set_time_point,
            value=brain._data['time_idx'],
            rng=[0, max_time],
            pointa=(0.23, 0.1),
            pointb=(0.77, 0.1),
            event_type='always'
        )
        time_slider.name = "time_slider"

        # playback speed
        default_playback_speed = 0.05
        playback_speed_slider = self.plotter.add_slider_widget(
            self.set_playback_speed,
            value=default_playback_speed,
            rng=[0.01, 1], title="playback speed",
            pointa=(0.02, 0.1),
            pointb=(0.18, 0.1)
        )

        # colormap slider
        scaling_limits = [0.2, 2.0]
        pointa = np.array((0.82, 0.26))
        pointb = np.array((0.98, 0.26))
        shift = np.array([0, 0.08])
        fmin = brain._data["fmin"]
        self.update_fmin = BumpColorbarPoints(
            plotter=self.plotter,
            brain=brain,
            name="fmin"
        )
        fmin_slider = self.plotter.add_slider_widget(
            self.update_fmin,
            value=fmin,
            rng=_get_range(brain), title="clim",
            pointa=pointa,
            pointb=pointb,
            event_type="always",
        )
        fmin_slider.name = "fmin"
        fmid = brain._data["fmid"]
        self.update_fmid = BumpColorbarPoints(
            plotter=self.plotter,
            brain=brain,
            name="fmid",
        )
        fmid_slider = self.plotter.add_slider_widget(
            self.update_fmid,
            value=fmid,
            rng=_get_range(brain), title="",
            pointa=pointa + shift,
            pointb=pointb + shift,
            event_type="always",
        )
        fmid_slider.name = "fmid"
        fmax = brain._data["fmax"]
        self.update_fmax = BumpColorbarPoints(
            plotter=self.plotter,
            brain=brain,
            name="fmax",
        )
        fmax_slider = self.plotter.add_slider_widget(
            self.update_fmax,
            value=fmax,
            rng=_get_range(brain), title="",
            pointa=pointa + 2 * shift,
            pointb=pointb + 2 * shift,
            event_type="always",
        )
        fmax_slider.name = "fmax"
        self.update_fscale = UpdateColorbarScale(
            plotter=self.plotter,
            brain=brain,
        )
        fscale_slider = self.plotter.add_slider_widget(
            self.update_fscale,
            value=1.0,
            rng=scaling_limits, title="fscale",
            pointa=(0.82, 0.10),
            pointb=(0.98, 0.10)
        )
        fscale_slider.name = "fscale"

        # add toggle to start/stop playback
        self.playback = False
        self.playback_speed = default_playback_speed
        self.refresh_rate_ms = max(int(round(1000. / 60.)), 1)
        self.plotter.add_callback(self.play, self.refresh_rate_ms)
        self.plotter.add_key_event('space', self.toggle_playback)

        # add toggle to show/hide interface
        self.visibility = True
        self.plotter.add_key_event('y', self.toggle_interface)

        # set the slider style
        _set_slider_style(smoothing_slider)
        _set_slider_style(orientation_slider, show_label=False)
        _set_slider_style(fmin_slider)
        _set_slider_style(fmid_slider)
        _set_slider_style(fmax_slider)
        _set_slider_style(fscale_slider)
        _set_slider_style(playback_speed_slider)
        _set_slider_style(time_slider, show_label=False)

        # set the text style
        _set_text_style(self.time_actor)

    def toggle_interface(self):
        self.visibility = not self.visibility
        for slider in self.plotter.slider_widgets:
            if self.visibility:
                slider.On()
            else:
                slider.Off()

    def toggle_playback(self):
        self.playback = not self.playback
        if self.playback:
            time_data = self.brain._data['time']
            max_time = np.max(time_data)
            if self.brain._current_time == max_time:  # start over
                self.brain.set_time_point(np.min(time_data))
            self._last_tick = time.time()

    def set_playback_speed(self, speed):
        self.playback_speed = speed

    def play(self):
        from scipy.interpolate import interp1d
        if self.playback:
            this_time = time.time()
            delta = this_time - self._last_tick
            self._last_tick = time.time()
            time_data = self.brain._data['time']
            times = np.arange(self.brain._n_times)
            time_shift = delta * self.playback_speed
            max_time = np.max(time_data)
            time_point = min(self.brain._current_time + time_shift, max_time)
            ifunc = interp1d(time_data, times)
            idx = ifunc(time_point)
            self.brain.set_time_point(idx)
            for slider in self.plotter.slider_widgets:
                name = getattr(slider, "name", None)
                if name == "time_slider":
                    slider_rep = slider.GetRepresentation()
                    slider_rep.SetValue(idx)
            if time_point == max_time:
                self.playback = False
            self.plotter.update()  # critical for smooth animation


def _set_slider_style(slider, show_label=True):
    if slider is not None:
        slider_rep = slider.GetRepresentation()
        slider_rep.SetSliderLength(0.02)
        slider_rep.SetSliderWidth(0.04)
        slider_rep.SetTubeWidth(0.005)
        slider_rep.SetEndCapLength(0.01)
        slider_rep.SetEndCapWidth(0.02)
        slider_rep.GetSliderProperty().SetColor((0.5, 0.5, 0.5))
        if not show_label:
            slider_rep.ShowSliderLabelOff()


def _set_text_style(text_actor):
    if text_actor is not None:
        prop = text_actor.GetTextProperty()
        prop.BoldOn()


def _get_range(brain):
    val = np.abs(brain._data['array'])
    return [np.min(val), np.max(val)]
