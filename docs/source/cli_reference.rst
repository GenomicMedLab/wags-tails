.. _cli-reference:

Command-line interface
----------------------

Some ``wags-tails`` functions are executable via a provided command-line interface,
enabling usage from non-Python environments or for general data management purposes.

.. note::

   Currently, the CLI routes data requests through the explicitly defined source modules within ``wags-tails``. This means that the CLI cannot be used to manage custom sources.

.. click:: wags_tails.cli:cli
   :prog: wags-tails
   :nested: full
