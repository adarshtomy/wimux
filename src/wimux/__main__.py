"""Start the WiFi Mux command when Python runs the package as a module.

Running ``python3 -m wimux`` reaches the same command-line function as the
other supported entry points.
"""

from .main import main


if __name__ == "__main__":
    main()