"""
Core visualization operations based on Fury.

Actual implementation of _Renderer and _Projection classes.
"""

# Authors: Alexandre Gramfort <alexandre.gramfort@telecom-paristech.fr>
#          Eric Larson <larson.eric.d@gmail.com>
#          Guillaume Favelier <guillaume.favelier@gmail.com>
#
# License: Simplified BSD

import numpy as np
import vtk
from fury import window, utils, actor
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
        from mne.viz.backends.renderer import MNE_3D_BACKEND_TEST_DATA
        self.off_screen = MNE_3D_BACKEND_TEST_DATA
        self.kwargs = {
            'size': size,
            'title': name,
        }
        self.fig = window.Scene() if fig is None else fig
        self.fig.background(bgcolor)
        self.kwargs['scene'] = self.fig
        self.plotter = window.ShowManager(**self.kwargs)
        self.plotter.initialize()

    def scene(self):
        return self.fig

    def set_interactive(self):
        self.style = vtk.vtkInteractorStyleTerrain()

    def mesh(self, x, y, z, triangles, color, opacity=1.0, shading=False,
             backface_culling=False, **kwargs):
        mesh = vtk.vtkPolyData()
        vertices = np.c_[x, y, z]
        utils.set_polydata_vertices(mesh, vertices)
        utils.set_polydata_triangles(mesh, triangles)
        colors = np.tile(color, len(vertices)) * 255.0
        utils.set_polydata_colors(mesh, colors)
        mesh_actor = utils.get_actor_from_polydata(mesh)
        mesh_actor.GetProperty().SetOpacity(opacity)
        mesh_actor.GetProperty().SetBackfaceCulling(backface_culling)
        self.fig.add(mesh_actor)

    def contour(self, surface, scalars, contours, line_width=1.0, opacity=1.0,
                vmin=None, vmax=None, colormap=None):
        # XXX Not supported yet
        pass

    def surface(self, surface, color=None, opacity=1.0,
                vmin=None, vmax=None, colormap=None, scalars=None,
                backface_culling=False):
        # XXX add support for colormap/scalars
        normalized_colormap = False
        cmap = _get_colormap_from_array(colormap, normalized_colormap)

        vertices = np.array(surface['rr'])
        x, y, z = vertices.T
        triangles = np.array(surface['tris'])

        mesh = vtk.vtkPolyData()
        vertices = np.array(surface['rr'])
        triangles = np.array(surface['tris'])
        utils.set_polydata_vertices(mesh, vertices)
        utils.set_polydata_triangles(mesh, triangles)
        if scalars is None:
            colors = np.tile(color, len(vertices)) * 255.0
            utils.set_polydata_colors(mesh, colors)
        else:
            colors = _get_color_from_scalars(cmap, scalars, vmin, vmax)
            utils.set_polydata_colors(mesh, colors[:, 3] * 255.0)
        mesh_actor = utils.get_actor_from_polydata(mesh)
        mesh_actor.GetProperty().SetOpacity(opacity)
        mesh_actor.GetProperty().SetBackfaceCulling(backface_culling)
        self.fig.add(mesh_actor)

    def sphere(self, center, color, scale, opacity=1.0,
               resolution=8, backface_culling=False):
        sphere_actor = actor.sphere(centers=center,
                                    colors=color,
                                    radii=scale / 2.0)
        sphere_actor.GetProperty().SetOpacity(opacity)
        sphere_actor.GetProperty().SetBackfaceCulling(backface_culling)
        self.fig.add(sphere_actor)

    def quiver3d(self, x, y, z, u, v, w, color, scale, mode, resolution=8,
                 glyph_height=None, glyph_center=None, glyph_resolution=None,
                 opacity=1.0, scale_mode='none', scalars=None,
                 backface_culling=False):
        # XXX Not supported yet
        pass

    def text(self, x, y, text, width, color=(1.0, 1.0, 1.0)):
        # XXX Not supported yet
        pass

    def show(self):
        if self.off_screen:
            window.record(self.fig, size=self.kwargs['size'],
                          reset_camera=False)
        else:
            self.plotter.scene = self.fig
            self.plotter.render()
            self.plotter.start()

    def close(self):
        self.plotter.exit()

    def set_camera(self, azimuth=0.0, elevation=0.0, distance=1.0,
                   focalpoint=(0, 0, 0)):
        phi = _deg2rad(azimuth)
        theta = _deg2rad(elevation)
        position = [
            distance * np.cos(phi) * np.sin(theta),
            distance * np.sin(phi) * np.sin(theta),
            distance * np.cos(theta)]
        self.fig.set_camera(position, focal_point=focalpoint,
                            view_up=[0, 0, 1])

    def screenshot(self):
        return window.snapshot(self.fig, size=self.kwargs['size'],
                               reset_camera=False)

    def project(self, xyz, ch_names):
        # XXX Not supported yet
        pass


def _close_all():
    pass


def _deg2rad(deg):
    from numpy import pi
    return deg * pi / 180.


def _get_colormap_from_array(colormap=None, normalized_colormap=False,
                             default_colormap='coolwarm'):
    from matplotlib import cm
    from matplotlib.colors import ListedColormap
    if colormap is None:
        cmap = cm.get_cmap(default_colormap)
    elif normalized_colormap:
        cmap = ListedColormap(colormap)
    else:
        cmap = ListedColormap(colormap / 255.0)
    return cmap


def _get_color_from_scalars(cmap, scalars=None, vmin=None, vmax=None):
    color = None
    if scalars is not None:
        if vmin is None:
            vmin = min(scalars)
        if vmax is None:
            vmax = max(scalars)
        nscalars = (scalars - vmin) / (vmax - vmin)
        color = cmap(nscalars)
    return color
