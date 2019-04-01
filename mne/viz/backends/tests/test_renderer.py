# Authors: Alexandre Gramfort <alexandre.gramfort@telecom-paristech.fr>
#          Eric Larson <larson.eric.d@gmail.com>
#          Joan Massich <mailsik@gmail.com>
#          Guillaume Favelier <guillaume.favelier@gmail.com>
#
# License: Simplified BSD

import os
import pytest
import importlib
import warnings
import numpy as np
from mne.viz.backends.renderer import get_3d_backend, use_test_3d_backend
from mne.utils import skips_if_not_vispy

# from .._utils import DEFAULT_3D_BACKEND
DEFAULT_3D_BACKEND = 'mayavi'  # This should be done with the import

print(DEFAULT_3D_BACKEND)

# def test_no_env_variable():
#     print(get_config().keys())
#     assert 'MNE_3D_BACKEND' not in get_config(use_env=True)


@pytest.fixture
def backend_mocker():
    """Help to test set up 3d backend."""
    from mne.viz.backends import renderer
    assert renderer.MNE_3D_BACKEND == DEFAULT_3D_BACKEND  # just double-check
    del renderer.MNE_3D_BACKEND
    yield
    renderer.MNE_3D_BACKEND = DEFAULT_3D_BACKEND


def has_not_mayavi():
    """Check that mayavi is not installed."""
    try:
        with warnings.catch_warnings(record=True):  # traits
            from mayavi import mlab # noqa F401
        return False
    except ImportError:
        return True


requires_mayavi = pytest.mark.skipif(has_not_mayavi(),
                                     reason='requires mayavi')


@pytest.mark.parametrize('backend', [
    pytest.param('mayavi', marks=requires_mayavi),
    pytest.param('vispy', marks=skips_if_not_vispy),
    pytest.param('foo', marks=pytest.mark.xfail(raises=ValueError)),
])
def test_backend_enviroment_setup(backend, backend_mocker, monkeypatch):
    """Test set up 3d backend based on env."""
    monkeypatch.setenv("MNE_3D_BACKEND", backend)
    assert os.environ['MNE_3D_BACKEND'] == backend  # just double-check

    from mne.viz.backends import renderer
    importlib.reload(renderer)
    assert renderer.MNE_3D_BACKEND == backend
    assert get_3d_backend() == backend


@requires_mayavi
def test_backend_setup():
    """Test 3d backend degenerate scenarios."""
    from mne.viz.backends.renderer import (set_3d_backend,
                                           get_3d_backend)
    pytest.raises(ValueError, set_3d_backend, "unknown_backend")
    pytest.raises(ValueError, set_3d_backend, 1)

    # smoke test
    set_3d_backend('mayavi')
    set_3d_backend('mayavi')

    assert get_3d_backend() == "mayavi"


@requires_mayavi
@pytest.mark.parametrize('backend_name', [
    pytest.param('mayavi'),
    pytest.param('vispy', marks=skips_if_not_vispy),
])
def test_3d_backend(backend_name):
    """Test default plot."""
    with use_test_3d_backend(backend_name):
        from mne.viz.backends.renderer import _Renderer

        # set data
        win_size = (600, 600)
        win_color = (0, 0, 0)

        tet_size = 1.0
        tet_x = np.array([0, tet_size, 0, 0])
        tet_y = np.array([0, 0, tet_size, 0])
        tet_z = np.array([0, 0, 0, tet_size])
        tet_indices = np.array([[0, 1, 2],
                                [0, 1, 3],
                                [0, 2, 3],
                                [1, 2, 3]])
        tet_color = (1, 1, 1)

        sph_center = np.column_stack((tet_x, tet_y, tet_z))
        sph_color = (1, 0, 0)
        sph_scale = tet_size / 3.0

        ct_scalars = np.array([0.0, 0.0, 0.0, 1.0])
        ct_levels = [0.2, 0.4, 0.6, 0.8]
        ct_surface = {
            "rr": sph_center,
            "tris": tet_indices
        }

        qv_mode = "arrow"
        qv_color = (0, 0, 1)
        qv_scale = tet_size / 2.0
        qv_center = np.array([np.mean((sph_center[va, :],
                                       sph_center[vb, :],
                                       sph_center[vc, :]), axis=0)
                             for (va, vb, vc) in tet_indices])
        center = np.mean(qv_center, axis=0)
        qv_dir = qv_center - center
        qv_scale_mode = 'scalar'
        qv_scalars = np.linspace(1.0, 2.0, 4)

        txt_x = 0.0
        txt_y = 0.0
        txt_text = "renderer"
        txt_width = 1.0

        cam_distance = 5 * tet_size

        # init scene
        renderer = _Renderer(size=win_size, bgcolor=win_color)
        renderer.set_interactive()

        # use mesh
        renderer.mesh(x=tet_x, y=tet_y, z=tet_z,
                      triangles=tet_indices,
                      color=tet_color)

        # use contour
        renderer.contour(surface=ct_surface, scalars=ct_scalars,
                         contours=ct_levels)

        # use sphere
        renderer.sphere(center=sph_center, color=sph_color,
                        scale=sph_scale)

        # use quiver3d
        renderer.quiver3d(x=qv_center[:, 0],
                          y=qv_center[:, 1],
                          z=qv_center[:, 2],
                          u=qv_dir[:, 0],
                          v=qv_dir[:, 1],
                          w=qv_dir[:, 2],
                          color=qv_color,
                          scale=qv_scale,
                          scale_mode=qv_scale_mode,
                          scalars=qv_scalars,
                          mode=qv_mode)

        # use text
        renderer.text(x=txt_x, y=txt_y, text=txt_text, width=txt_width)
        renderer.set_camera(azimuth=180.0, elevation=90.0,
                            distance=cam_distance,
                            focalpoint=center)
        renderer.show()
