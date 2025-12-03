import sys
from types import ModuleType
import pytest

# Insert minimal top-level `donkeycar` package and `donkeycar.parts`
# package modules to prevent importing the real package (which pulls in
# optional heavy deps like Pillow) during pytest collection.
_inserted = []
if "donkeycar" not in sys.modules:
    pkg = ModuleType("donkeycar")
    pkg.__path__ = []
    sys.modules["donkeycar"] = pkg
    _inserted.append("donkeycar")

if "donkeycar.parts" not in sys.modules:
    parts_pkg = ModuleType("donkeycar.parts")
    parts_pkg.__path__ = []
    sys.modules["donkeycar.parts"] = parts_pkg
    _inserted.append("donkeycar.parts")
    # create lightweight placeholders for commonly-imported submodules
    actuator_mod = ModuleType("donkeycar.parts.actuator")
    pins_mod = ModuleType("donkeycar.parts.pins")
    sys.modules["donkeycar.parts.actuator"] = actuator_mod
    sys.modules["donkeycar.parts.pins"] = pins_mod
    # expose as attributes on the package so `from donkeycar.parts import actuator` works
    setattr(parts_pkg, "actuator", actuator_mod)
    setattr(parts_pkg, "pins", pins_mod)
    _inserted.extend(["donkeycar.parts.actuator", "donkeycar.parts.pins"])


def pytest_unconfigure(config):
    # remove the placeholders we added at collection time
    for name in _inserted:
        try:
            del sys.modules[name]
        except KeyError:
            pass


@pytest.fixture
def inject_module():
    """Return a helper that injects a module into `sys.modules` for the
    duration of a test and restores previous state afterwards.

    Usage in tests:
        def test_x(inject_module):
            fake_mod = ModuleType('donkeycar.parts.dgym')
            inject = inject_module()
            inject('donkeycar.parts.dgym', fake_mod)
            # now import modules that expect donkeycar.parts.dgym
    """
    backups = {}

    def _inject(name, module):
        # save previous value (or None)
        backups.setdefault(name, sys.modules.get(name))
        sys.modules[name] = module

    yield _inject

    # restore previous modules
    for name, val in backups.items():
        if val is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = val
