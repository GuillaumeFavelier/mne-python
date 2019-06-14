"""
Core visualization operations based on Fury.

Actual implementation of _Renderer and _Projection classes.
"""

# Authors: Alexandre Gramfort <alexandre.gramfort@telecom-paristech.fr>
#          Eric Larson <larson.eric.d@gmail.com>
#          Guillaume Favelier <guillaume.favelier@gmail.com>
#
# License: Simplified BSD

from .base_renderer import _BaseRenderer
from ...utils import copy_base_doc_to_subclass_doc


class _Projection(object):
    """Class storing projection information.

    Attributes
    ----------
    xy : array
        Result of 2d projection of 3d data.
    pts : None
        Scene sensors handle.
    """

    def __init__(self, xy=None, pts=None):
        """Store input projection information into attributes."""
        pass

    def visible(self, state):
        """Modify visibility attribute of the sensors."""
        pass


@copy_base_doc_to_subclass_doc
class _Renderer(_BaseRenderer):
    """Class managing rendering scene.

    Attributes
    ----------
    plotter: pyvista.Plotter
        Main PyVista access point.
    off_screen: bool
        State of the offscreen.
    name: str
        Name of the window.
    """

    def __init__(self, fig=None, size=(600, 600), bgcolor=(0., 0., 0.),
                 name="Fury Scene", show=False):
        pass

    def scene(self):
        pass

    def set_interactive(self):
        pass

    def mesh(self, x, y, z, triangles, color, opacity=1.0, shading=False,
             backface_culling=False, **kwargs):
        pass

    def contour(self, surface, scalars, contours, line_width=1.0, opacity=1.0,
                vmin=None, vmax=None, colormap=None):
        pass

    def surface(self, surface, color=None, opacity=1.0,
                vmin=None, vmax=None, colormap=None, scalars=None,
                backface_culling=False):
        pass

    def sphere(self, center, color, scale, opacity=1.0,
               resolution=8, backface_culling=False):
        pass

    def quiver3d(self, x, y, z, u, v, w, color, scale, mode, resolution=8,
                 glyph_height=None, glyph_center=None, glyph_resolution=None,
                 opacity=1.0, scale_mode='none', scalars=None,
                 backface_culling=False):
        pass

    def text(self, x, y, text, width, color=(1.0, 1.0, 1.0)):
        pass

    def show(self):
        pass

    def close(self):
        pass

    def set_camera(self, azimuth=0.0, elevation=0.0, distance=1.0,
                   focalpoint=(0, 0, 0)):
        pass

    def screenshot(self):
        pass

    def project(self, xyz, ch_names):
        pass


def _close_all():
    pass
