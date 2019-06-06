"""Core visualization operations based on ipyvolume."""

# Authors: Alexandre Gramfort <alexandre.gramfort@telecom-paristech.fr>
#          Eric Larson <larson.eric.d@gmail.com>
#          Oleh Kozynets <ok7mailbox@gmail.com>
#          Guillaume Favelier <guillaume.favelier@gmail.com>
#          Joan Massich <mailsik@gmail.com>
#
# License: Simplified BSD

import warnings
import numpy as np
from .base_renderer import _BaseRenderer
from ._utils import _get_colormap_from_array, _get_color_from_scalars
from ...utils import copy_base_doc_to_subclass_doc
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import ipyvolume as ipv
    from pythreejs import (BlendFactors, BlendingMode, Equations,
                           ShaderMaterial, Side)


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
        raise NotImplementedError('This feature is not implemented yet')

    def visible(self, state):
        """Modify visibility attribute of the sensors."""
        raise NotImplementedError('This feature is not implemented yet')


@copy_base_doc_to_subclass_doc
class _Renderer(_BaseRenderer):
    """Class managing rendering scene created with ipyvolume.

    Attributes
    ----------
    plotter: ipyvolume.widgets.Figure
        The scene handler.
    """

    def __init__(self, fig=None, size=(600, 600), bgcolor=(0., 0., 0.),
                 name="Ipyvolume Scene", show=False):
        """Set up the scene.

        Parameters
        ----------
        fig: ipyvolume.widgets.Figure
            The scene handler.
        size: tuple
            The dimensions of the context window: (width, height).
        bgcolor: tuple
            The color definition of the background: (red, green, blue).
        name: str | None
            The name of the scene.
        """
        self.off_screen = False
        self.name = name
        self.vmin = 0.0
        self.vmax = 0.0

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            if fig is None:
                fig_w, fig_h = size
                self.plotter = ipv.figure(width=fig_w, height=fig_h)
                self.plotter.animation = 0
                ipv.style.box_off()
                ipv.style.axes_off()
                bgcolor = tuple(int(c) for c in bgcolor)
                ipv.style.background_color('#%02x%02x%02x' % bgcolor)
            else:
                self.plotter = ipv.figure(key=fig)
            self.plotter.camera.up = (0.0, 0.0, 1.0)

    def update_limits(self, x, y, z):
        self.vmin = np.min([self.vmin, x.min(), y.min(), z.min()])
        self.vmax = np.max([self.vmax, x.max(), y.max(), z.max()])

    def scene(self):
        return self.plotter

    def set_interactive(self):
        pass

    def mesh(self, x, y, z, triangles, color, opacity=1.0, shading=False,
             backface_culling=False, **kwargs):
        # opacity for overlays will be provided as part of color
        color = _color2rgba(color, opacity)
        mesh = ipv.plot_trisurf(x, y, z, triangles=triangles, color=color)
        if opacity < 1.0:
            _add_transparent_material(mesh, opacity)
        self.update_limits(x, y, z)
        return mesh

    def contour(self, surface, scalars, contours, line_width=1.0, opacity=1.0,
                vmin=None, vmax=None, colormap=None,
                normalized_colormap=False):
        from ipyvolume.pylab import plot

        vertices = surface['rr']
        tris = surface['tris']

        cmap = _get_colormap_from_array(colormap, normalized_colormap)

        if isinstance(contours, int):
            levels = np.linspace(vmin, vmax, num=contours)
        else:
            levels = np.array(contours)

        if scalars is not None:
            color = _get_color_from_scalars(cmap, scalars, vmin, vmax)
        if len(color) == 3:
            color = np.append(color, opacity)

        verts, _, = _isoline(vertices=vertices, tris=tris,
                             vertex_data=scalars, levels=levels)

        x, y, z = verts.T
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            plot(x, y, z, color=color)
        self.update_limits(x, y, z)

    def surface(self, surface, color=None, opacity=1.0,
                vmin=None, vmax=None, colormap=None,
                normalized_colormap=False, scalars=None,
                backface_culling=False):
        cmap = _get_colormap_from_array(colormap, normalized_colormap)

        vertices = np.array(surface['rr'])
        x, y, z = vertices.T
        triangles = np.array(surface['tris'])

        if scalars is not None:
            color = _get_color_from_scalars(cmap, scalars, vmin, vmax)
        if len(color) == 3:
            color = np.append(color, opacity)

        mesh = ipv.plot_trisurf(x, y, z, triangles=triangles, color=color)
        if opacity < 1.0:
            _add_transparent_material(mesh, opacity)
        self.update_limits(x, y, z)

    def sphere(self, center, color, scale, opacity=1.0, resolution=8,
               backface_culling=False):
        default_sphere_radius = 0.5
        if center.ndim == 1:
            center = np.array([center])

        # fetch original data
        orig_vertices, orig_faces = \
            _create_sphere(radius=scale * default_sphere_radius,
                           cols=resolution, rows=resolution)
        n_vertices = len(orig_vertices)
        orig_vertices = np.c_[orig_vertices, np.ones(n_vertices)].T
        n_faces = len(orig_faces)
        n_center = len(center)
        voffset = 0
        foffset = 0

        # accumulate mesh data
        acc_vertices = np.empty((n_center * n_vertices, 3), dtype=np.float32)
        acc_faces = np.empty((n_center * n_faces, 3), dtype=np.uint32)
        for c in center:
            # apply index shifting and accumulate faces
            current_faces = orig_faces + voffset
            acc_faces[foffset:foffset + n_faces, :] = current_faces
            foffset += n_faces

            # apply translation and accumulate vertices
            mat = np.eye(4)
            mat[:-1, 3] = c
            current_vertices = mat.dot(orig_vertices)
            acc_vertices[voffset:voffset + n_vertices, :] = \
                current_vertices.T[:, 0:3]
            voffset += n_vertices

        x, y, z = acc_vertices.T
        color = np.append(color, opacity)

        mesh = ipv.plot_trisurf(x, y, z, triangles=acc_faces, color=color)
        if opacity < 1.0:
            _add_transparent_material(mesh, opacity)
        self.update_limits(x, y, z)

    def quiver3d(self, x, y, z, u, v, w, color, scale, mode, resolution=8,
                 glyph_height=None, glyph_center=None, glyph_resolution=None,
                 opacity=1.0, scale_mode='none', scalars=None,
                 backface_culling=False):
        # XXX: scale is not supported yet
        color = np.append(color, opacity)
        x, y, z, u, v, w = map(np.atleast_1d, [x, y, z, u, v, w])
        size = scale * 200
        tr = scale / 2.0
        x += tr * u
        y += tr * v
        z += tr * w
        scatter = ipv.quiver(x, y, z, u, v, w, marker=mode, color=color,
                             size=size)

        if opacity < 1.0:
            _add_transparent_material(scatter, opacity)
        self.update_limits(x, y, z)

    def text(self, x, y, text, width, color=(1.0, 1.0, 1.0)):
        pass

    def show(self):
        ipv.xyzlim(self.vmin, self.vmax)
        ipv.show()

    def close(self):
        ipv.clear()

    def set_camera(self, azimuth=0.0, elevation=0.0, distance=1.0,
                   focalpoint=(0, 0, 0)):
        ipv.view(azimuth=azimuth,
                 elevation=elevation,
                 distance=distance * 2.0)

    def screenshot(self):
        pass

    def project(self):
        pass


def _create_sphere(rows, cols, radius, offset=True):
    verts = np.empty((rows + 1, cols, 3), dtype=np.float32)

    # compute vertices
    phi = (np.arange(rows + 1) * np.pi / rows).reshape(rows + 1, 1)
    s = radius * np.sin(phi)
    verts[..., 2] = radius * np.cos(phi)
    th = ((np.arange(cols) * 2 * np.pi / cols).reshape(1, cols))
    if offset:
        # rotate each row by 1/2 column
        th = th + ((np.pi / cols) * np.arange(rows + 1).reshape(rows + 1, 1))
    verts[..., 0] = s * np.cos(th)
    verts[..., 1] = s * np.sin(th)
    # remove redundant vertices from top and bottom
    verts = verts.reshape((rows + 1) * cols, 3)[cols - 1:-(cols - 1)]

    # compute faces
    faces = np.empty((rows * cols * 2, 3), dtype=np.uint32)
    rowtemplate1 = (((np.arange(cols).reshape(cols, 1) +
                      np.array([[1, 0, 0]])) % cols) +
                    np.array([[0, 0, cols]]))
    rowtemplate2 = (((np.arange(cols).reshape(cols, 1) +
                      np.array([[1, 0, 1]])) % cols) +
                    np.array([[0, cols, cols]]))
    for row in range(rows):
        start = row * cols * 2
        faces[start:start + cols] = rowtemplate1 + row * cols
        faces[start + cols:start + (cols * 2)] = rowtemplate2 + row * cols
    # cut off zero-area triangles at top and bottom
    faces = faces[cols:-cols]

    # adjust for redundant vertices that were removed from top and bottom
    vmin = cols - 1
    faces[faces < vmin] = vmin
    faces -= vmin
    vmax = verts.shape[0] - 1
    faces[faces > vmax] = vmax
    return verts, faces


def _add_transparent_material(mesh, opacity):
    """Change the mesh material so it will support transparency."""
    mat = ShaderMaterial()
    mat.alphaTest = opacity
    mat.blending = BlendingMode.CustomBlending
    mat.blendDst = BlendFactors.OneMinusSrcAlphaFactor
    mat.blendEquation = Equations.AddEquation
    mat.blendSrc = BlendFactors.SrcAlphaFactor
    mat.transparent = True
    mat.side = Side.DoubleSide

    mesh.material = mat


def _isoline(vertices, tris, vertex_data, levels):
    """Generate an isocurve from vertex data in a surface mesh.

    Parameters
    ----------
    vertices : ndarray, shape (Nv, 3)
        Vertex coordinates.
    tris : ndarray, shape (Nf, 3)
        Indices of triangular element into the vertices array.
    vertex_data : ndarray, shape (Nv,)
        data at vertex.
    levels : ndarray, shape (Nl,)
        Levels at which to generate an isocurve

    Returns
    -------
    lines : ndarray, shape (Nvout, 3)
        Vertex coordinates for lines points
    connects : ndarray, shape (Ne, 2)
        Indices of line element into the vertex array.

    Notes
    -----
    Uses a marching squares algorithm to generate the isolines.
    """
    lines, connects = (None, None)
    if not all([isinstance(x, np.ndarray) for x in (vertices, tris,
                vertex_data, levels)]):
        raise ValueError('all inputs must be numpy arrays')
    verts = _check_vertices_shape(vertices)
    if (verts is not None and tris.shape[1] == 3 and
            vertex_data.shape[0] == verts.shape[0]):
        edges = np.vstack((tris.reshape((-1)),
                           np.roll(tris, -1, axis=1).reshape((-1)))).T
        edge_datas = vertex_data[edges]
        edge_coors = verts[edges].reshape(tris.shape[0] * 3, 2, 3)
        for lev in levels:
            # index for select edges with vertices have only False - True
            # or True - False at extremity
            index = (edge_datas >= lev)
            index = index[:, 0] ^ index[:, 1]  # xor calculation
            # Selectect edge
            edge_datas_Ok = edge_datas[index, :]
            xyz = edge_coors[index]
            # Linear interpolation
            ratio = np.array([(lev - edge_datas_Ok[:, 0]) /
                              (edge_datas_Ok[:, 1] - edge_datas_Ok[:, 0])])
            point = xyz[:, 0, :] + ratio.T * (xyz[:, 1, :] - xyz[:, 0, :])
            nbr = point.shape[0] // 2
            if connects is None:
                lines = point
                connects = np.arange(0, nbr * 2).reshape((nbr, 2))
            else:
                connect = np.arange(0, nbr * 2).reshape((nbr, 2)) + \
                    len(lines)
                connects = np.append(connects, connect, axis=0)
                lines = np.append(lines, point, axis=0)

    return lines, connects


def _color2rgba(color, opacity):
    """Update color opacity values."""
    if opacity is None:
        # no need to update colors
        return color

    color = np.array(color)
    if color.ndim == 1:
        color = np.expand_dims(color, axis=0)
    _, n_components = color.shape
    if n_components == 4:
        color[:, -1] = opacity
    elif n_components == 3:
        # add new axis
        rgba_color = np.zeros((len(color), 4))
        rgba_color[:, :-1] = color
        rgba_color[:, -1] = opacity
        color = rgba_color

    return color


def _check_vertices_shape(vertices):
    """Check vertices shape."""
    if vertices.shape[1] <= 3:
        verts = vertices
    elif vertices.shape[1] == 4:
        verts = vertices[:, :-1]
    else:
        verts = None
    return verts


def _close_all():
    # XXX This is not implemented yet
    pass
