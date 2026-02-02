"""#!/usr/bin/env python3
"""

"""email-sorter-exe: application entrypoint (stub)
"""

from .version import __version__
from .logutil import configure_logging

import sys


def main(argv=None):
    argv = argv or sys.argv[1:]
    configure_logging()
    print(f"Email Sorter v{__version__} starting...")
    # TODO: wire up GUI, CLI, or pipeline here


if __name__ == "__main__":
    main()