"""
Core visualization operations based on Dash.

Actual implementation of _Renderer and _Projection classes.
"""
from .base_renderer import _BaseRenderer
import numpy as np


class _Projection(object):
    def __init__(self, xy=None, pts=None):
        pass


class _Renderer(_BaseRenderer):
    def __init__(self, fig=None, size=(600, 600), bgcolor=(0., 0., 0.),
                 name=None, show=False):
        import plotly.graph_objects as go
        self.data = []

    def scene(self):
        pass

    def set_interactive(self):
        pass

    def mesh(self, x, y, z, triangles, color, opacity=1.0, shading=False,
             backface_culling=False, **kwargs):
        pass


    def contour(self, surface, scalars, contours, line_width=1.0, opacity=1.0,
                vmin=None, vmax=None, colormap=None,
                normalized_colormap=False):
        pass

    def surface(self, surface, color=None, opacity=1.0,
                vmin=None, vmax=None, colormap=None,
                normalized_colormap=False, scalars=None,
                backface_culling=False):
        import plotly.graph_objects as go
        vertices = np.array(surface['rr'])
        triangles = np.array(surface['tris'])
        x, y, z = vertices.T
        i, j, k = triangles.T
        mesh = go.Mesh3d(
            x=x,
            y=y,
            z=z,
            i=i,
            j=j,
            k=k,
            opacity=opacity,
            showscale=True
        )
        self.data.append(mesh)

    def sphere(self, center, color, scale, opacity=1.0,
               resolution=8, backface_culling=False):
        import plotly.graph_objects as go
        x, y, z = center.T
        scatter = go.Scatter3d(x=x, y=y, z=z, mode='markers')
        self.data.append(scatter)

    def tube(self, origin, destination, radius=1.0, color=(1.0, 1.0, 1.0),
             scalars=None, vmin=None, vmax=None, colormap='RdBu',
             normalized_colormap=False, reverse_lut=False):
        pass

    def quiver3d(self, x, y, z, u, v, w, color, scale, mode, resolution=8,
                 glyph_height=None, glyph_center=None, glyph_resolution=None,
                 opacity=1.0, scale_mode='none', scalars=None,
                 backface_culling=False):
        pass

    def text2d(self, x, y, text, width, color=(1.0, 1.0, 1.0)):
        pass

    def text3d(self, x, y, z, text, scale, color=(1.0, 1.0, 1.0)):
        pass

    def scalarbar(self, source, title=None, n_labels=4):
        pass

    def show(self):
        import plotly.graph_objects as go
        fig = go.Figure(data=self.data)
        fig.show()

    def close(self):
        pass

    def set_camera(self, azimuth=None, elevation=None, distance=None,
                   focalpoint=None):
        pass

    def screenshot(self):
        pass

    def project(self, xyz, ch_names):
        pass


def _set_3d_title(figure, title, size=40):
    pass


def _set_3d_view(figure, azimuth, elevation, focalpoint, distance):
    pass


def _close_all():
    pass
