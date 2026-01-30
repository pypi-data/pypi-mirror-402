# tests/test_log.py

import sys
sys.path.insert(0, "/data/tianzhen/my_packages/cobra-log/src")

from cobra_log import (warning, info)


def test_cobra_log():
    try:
        try:
            raise KeyError("This is the first exception")
        except Exception as e1:
            try:
                raise KeyError("This is the second exception")
            except Exception as e2:
                raise RuntimeError("This is the main exception", e2, e1)

    except Exception as e:
        warning("An error occurred during the test.", e)
        info("Continuing execution after warning.")


if __name__ == "__main__":
    test_cobra_log()
