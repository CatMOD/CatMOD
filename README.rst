CatMOD
=====

.. class:: no-web no-pdf

    .. image:: https://github.com/CatMOD/CatMOD/blob/main/img/catmod.logo.svg

.. class:: no-web no-pdf

    |language| |version| |update|

.. contents::

.. section-numbering::

Description
-----------

**CatMOD** is a .

.. class:: no-web no-pdf

    .. image:: https://github.com/CatMOD/CatMOD/blob/main/img/catmod.model.png

Getting Started
---------------

Requirements
~~~~~~~~~~~~

CatMOD Project is a python3 package. To use CatMOD, python version 3.9 or higher is required.

Installation
~~~~~~~~~~~~

.. code-block:: shell

    git clone https://github.com/CatMOD/CatMOD.git
    cd CatMOD
    conda create -n catmod -y python=3.9
    python setup.py install

or

.. code-block:: shell

    git clone https://github.com/CatMOD/CatMOD.git
    cd CatMOD
    conda env create -f catmod.yml

or

.. code-block:: shell

    git clone https://github.com/CatMOD/CatMOD.git
    conda create -n catmod -y python=3.9 catboost h5py numpy pysam rich scipy
    conda activate catmod

Running the tests
~~~~~~~~~~~~~~~~~

Usage
-----

Preprocess
~~~~~~~~~~

Using Guppy and Tombo processes ONT fast5 files.

.. code-block:: shell

    guppy_basecaller --input_path $fast5_folder --recursive --fast5_out --save_path $guppy_folder --flowcell $FLOWCELL --kit $KIT --num_callers $THREADS
    multi_to_single_fast5 --input_path $guppy_folder --save_path $single_folder --threads $THREADS --recursive
    tombo resquiggle --rna --processes $threads --overwrite --fit-global-scale --include-event-stdev $single_folder $REFERENCE

Data processing
~~~~~~~~~~~~~~~

.. code-block:: shell

    catmod data_process

Extracting features
~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

    catmod extract_features --bed $sample_bed --ref $REFERENCE --align $ont_bam --current $ont_current --threads $THREADS --output $datasets_folder

Predicting
~~~~~~~~~~

.. code-block:: shell

    catmod predict --bed $sample_bed --datasets $datasets_folder --model /path/to/CatMOD/models/wheat_pretrained.cbc.cbm --threads $THREADS --output $datasets_folder

Support
-------

Contributing
------------

Citation
--------

License
-------

Changelog
---------

.. |language| image:: https://img.shields.io/badge/language-python-blue.svg

.. |version| image:: https://img.shields.io/badge/version-v0.0.1a-green.svg

.. |update| image:: https://img.shields.io/badge/last%20updated-10%20May%202022-orange.svg
