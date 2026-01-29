"""
Entry point for running the substitution module as a script.
"""

import sys  # pragma: no cover

from .substitution import main  # pragma: no cover

if __name__ == '__main__':  # pragma: nocover
    sys.exit(main(sys.argv[1:]))
