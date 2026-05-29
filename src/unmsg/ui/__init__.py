"""The desktop GUI (PySide6).

Importing this package does not import the conversion core's heavy parser at
module load; widgets pull in only what they need. The core never imports from
here — enforced in CI.
"""
