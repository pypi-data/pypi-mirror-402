guirecognizer
=============

**guirecognizer** is a Python library for recognizing on-screen patterns and driving GUI interactions.

The main goal of *guirecognizer* is to recognize on-screen patterns, such as retrieving a pixel color, computing an image hash over a screenshot area, or finding a specific image.
It can also perform basic GUI interactions, such as clicking on screen elements.

The companion application **guirecognizerapp** helps you create and preview actions and preprocessing operations through a visual interface,
before using them in a Python bot with guirecognizer.

See documentation with tutorials and examples: `https://guirecognizer.readthedocs.io <https://guirecognizer.readthedocs.io>`_.

Quick overview
--------------

*guirecognizer* relies on a configuration file that defines the actions.

Let's install the companion application *guirecognizerapp* to generate a configuration file. This will also install *guirecognizer*.

.. code-block:: console

  (venv) $ pip install guirecognizerapp

Launch the application:

.. code-block:: console

  (venv) $ python -m guirecognizerapp

From the application, take a screenshot using *Capture -> Take Screenshot* or use the keyboard shortcut *Ctrl+Alt+T*.

The first step is to define the borders.
The borders represent the absolute coordinates of the screen region that serve as a reference for all actions.
All action selections are defined relative to these borders.
This greatly improves the reusability of the configuration file across different screen resolutions or setups.

.. figure:: https://raw.githubusercontent.com/fab5code/guirecognizer/main/docs/_static/overview/defineBorders1.webp
   :alt: Click on the Make Selection button to define the borders.
   :width: 100%
   :align: center

   Click on the *Make Selection* button to define the borders.

Select an area of the screenshot using the mouse or the controls at the bottom of the interface.

.. figure:: https://raw.githubusercontent.com/fab5code/guirecognizer/main/docs/_static/overview/defineBorders2.webp
   :alt: Select the borders on the screenshot.
   :width: 100%
   :align: center

   Select the borders on the screenshot.

For the sake of this tutorial, let's retrieve the color of a single pixel.
Create a new *Get Pixel Color* action: *Manage Actions -> Add Action Get Pixel Color*. Name your action *getColor* and select a pixel.

.. figure:: https://raw.githubusercontent.com/fab5code/guirecognizer/main/docs/_static/overview/defineAction.webp
   :alt: Select a point within the borders on the screenshot.
   :width: 100%
   :align: center

   Select a point within the borders on the screenshot.

You can preview the action by clicking on the eye icon.

.. figure:: https://raw.githubusercontent.com/fab5code/guirecognizer/main/docs/_static/overview/preview1.webp
   :alt: Preview the action getColor by clicking on the eye icon.
   :width: 100%
   :align: center

   Preview the action *getColor* by clicking on the eye icon.

.. figure:: https://raw.githubusercontent.com/fab5code/guirecognizer/main/docs/_static/overview/preview2.webp
   :alt: Preview of the action getColor.
   :width: 100%
   :align: center

   Preview of the action *getColor*.

The preview shows the pixel color retrieved by the *getColor* action.

Save the configuration file as *guirecognizerConfig.json* in your project folder: *File -> Save* or *Ctrl+S*.
Now the configuration file can be used with *guirecognizer*.

In your Python script:

.. code-block:: python

  from guirecognizer import Recognizer

  recognizer = Recognizer('guirecognizerConfig.json')
  color = recognizer.executePixelColor('getColor')
  print(color)

This produces the following output:

.. code-block::

  (243, 207, 85)

Development
-----------

Install the dependencies
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

  (venv) $ pip install -e ".[dev]"


Create wheel
^^^^^^^^^^^^

.. code-block:: console

  (venv) $ python -m build

OCR
^^^

Two optical character recognition libraries are supported: `EasyOCR <https://github.com/JaidedAI/EasyOCR>`_ and `tesseract <https://github.com/tesseract-ocr/tesseract>`_.

Install EasyOCR (already in the dev dependencies).

.. code-block:: console

  (venv) $ python install easyocr

Install pytesseract (already in the dev dependencies).

.. code-block:: console

  (venv) $ python install easyocr

Install tesseract: follow installation instruction in `https://github.com/tesseract-ocr/tesseract <https://github.com/tesseract-ocr/tesseract>`_.

Generate full coverage report
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

  (venv) $ coverage run
  (venv) $ coverage html

Then open *htmlcov/index.html*

Documentation
^^^^^^^^^^^^^

Generate doc

.. code-block:: console

  (venv) $ make html

Then open *docsBuild/index.html*

Use the script *scripts/optimizeImages.sh* in a bash console to reduce the size of images before pushing them in git.
Image files are converted to webp files.

For instance:

.. code-block:: console

  $ ./scripts/optimizeImages.sh docs/_static/app

Coding style
^^^^^^^^^^^^

Some visual studio code settings of visualStudioCodeSettings.json should be used to ensure some homogeneity in the coding style.

In Visual Studio Code, install extensions

- isort to sort Python automatically
- Pylance for type checking

Improvements
------------

**Improve logger usage**: in code and tests.
