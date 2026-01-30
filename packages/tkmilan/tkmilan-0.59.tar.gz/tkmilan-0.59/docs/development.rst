Development Process
===================

.. todo:: Document the development process

Useful Links
------------

- reStructuredText: https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html
- Docstring sections: https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html#docstring-sections
- Python Domain Roles: https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#python-roles

TODO List
---------

See a list of documentation TODO:

.. todolist::

Debug Environment Variables
---------------------------

If you run your program in `__debug__` mode, the following environment variables can be used:

.. envvar:: TKMILAN_DEBUG

   Produce more debug output for a specific section. The list of sections is:

   - ``grid``: On the `fn.debugWidget` function, for container widgets,
      debug the grid configuration (all rows and columns).
   - ``grid:debug``: Produce an enormous amount of logs for every grid
      manipulation.
   - ``layout:debug``: Produce an enormous amount of logs for every single
      autolayout execution.
   - ``validation:debug``: Produce an enormous amount of logs for every
      single widget validation.
   - ``canvas:render``: Produce an enormous amount of logs for the canvas
      rendering process.
   - ``secondarywindow``: Debug `SecondaryWindow` mapping and unmappings.

   Include the sections you want separated by ``,``.

   For example::

      TKMILAN_DEBUG=grid tkmilan-showcase
