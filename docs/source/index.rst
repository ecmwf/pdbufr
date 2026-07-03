
Pdbufr's documentation
====================================

*pdbufr* is a Python package implementing a `Pandas <https://pandas.pydata.org>`_ reader for the BUFR format using :xref:`eccodes`. It features the :func:`read_bufr` function to extract data from a BUFR file as a Pandas DataFrame using a rich filtering engine.

*pdbufr* supports BUFR 3 and 4 files with uncompressed and compressed subsets. It works on Linux, macOS and Windows; the ecCodes C-library is the only binary dependency.


.. grid:: 1
   :gutter: 2

   .. grid-item-card:: Why pdbufr?
      :img-top: _static/bulb.svg
      :link: why
      :link-type: doc
      :class-card: sd-shadow-sm

      The motivation and key features of pdbufr.


.. grid:: 1 1 2 2
   :gutter: 2

   .. grid-item-card:: Installation
      :img-top: _static/rocket.svg
      :link: install
      :link-type: doc
      :class-card: sd-shadow-sm

      New to pdbufr? Start here with installation and a quick overview.

   .. grid-item-card:: How-tos
      :img-top: _static/tool.svg
      :link: how-tos/index
      :link-type: doc
      :class-card: sd-shadow-sm

      Practical notebook examples for common tasks.

   .. grid-item-card:: Tutorials
      :img-top: _static/book.svg
      :link: tutorials/index
      :link-type: doc
      :class-card: sd-shadow-sm

      Step-by-step guides to learn pdbufr.

   .. grid-item-card:: Frequently Asked Questions
      :img-top: _static/message-question.svg
      :link: faq
      :link-type: doc
      :class-card: sd-shadow-sm

      Common questions, answered.

   .. grid-item-card:: Concepts
      :img-top: _static/bulb.svg
      :link: concepts/index
      :link-type: doc
      :class-card: sd-shadow-sm

      Understand the readers, filters and BUFR key model.

   .. grid-item-card:: API Reference
      :img-top: _static/brackets-contain.svg
      :link: concepts/read_bufr
      :link-type: doc
      :class-card: sd-shadow-sm

      Detailed documentation of :func:`read_bufr` and all its parameters.


**Support**

Have a feature request or found a bug? Feel free to open an
`issue <https://github.com/ecmwf/pdbufr/issues/new/choose>`_.


.. toctree::
   :maxdepth: 1
   :hidden:

   why

.. toctree::
   :maxdepth: 1
   :caption: User guide
   :hidden:

   install
   tutorials/index
   faq
   how-tos/index
   concepts/index

.. toctree::
   :maxdepth: 1
   :caption: Developer guide
   :hidden:

   development

.. toctree::
   :maxdepth: 1
   :caption: Extras
   :hidden:

   release-notes/index
   licence
   genindex
