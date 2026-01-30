.. e2x-exam-sheets documentation master file, created by
   sphinx-quickstart on Thu Apr  4 16:00:01 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

e2x-exam-sheets Documentation
=============================

Welcome to the e2x-exam-sheets documentation. This package is used for generating exam supervision sheets for JupyterHub-based exams.
Each exam sheet can be generated as a PDF or HTML file.
The generated exam sheets consist of a cover page with a list of students and a sheet for each student.
Each student sheet contains the student's name, student ID, room number, seat number, username and password.
Additionally, the student sheet contains space for a hashcode and signature to verify the exam's integrity.

Look at an example of a generated exam sheet in `PDF Format <_static/example_sheet.pdf>`_ or `HTML Format <_static/example_sheet.html>`_.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started:

   getting_started/index

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   user_guide/index

Example Sheet
-------------

.. raw:: html

   <div style="text-align: center;">
   <embed src="_static/example_sheet.pdf" type="application/pdf" width="100%" height="800px" style="border: 1px solid gray;"></iframe>   
   </div>




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
