# <img alt="ACBICI" src="branding/ACBICI_Logo.svg" height="80">

[![License](https://img.shields.io/gitlab/license/schenkch/ACBICI?cacheSeconds=300)](https://gitlab.com/schenkch/ACBICI/-/blob/master/LICENSE)
[![Last Commit](https://img.shields.io/gitlab/last-commit/schenkch/ACBICI)](https://gitlab.com/schenkch/ACBICI/)
[![Documentation Status](https://readthedocs.org/projects/acbici/badge/?version=latest)](https://acbici.readthedocs.io/en/latest/py-modindex.html)

ACBICI (A Configurable BayesIan Calibration and Inference package) is a Python package designed to calibrate models including uncertainty estimates.

- **Documentation:** - https://acbici.readthedocs.io / Alternatively can be compiled following the instructions in docs/ReadmeDoc.txt file.  
- **Examples and Tutorials** - https://gitlab.com/schenkch/acbici/tree/master/examples
- **Source code:** - https://gitlab.com/schenkch/acbici/tree/master/src/ACBICI
- **Bug reports:** - https://gitlab.com/schenkch/acbici/issues


It has the following functionality:
 - Bayesian calibration
 - provide distribution for the model parameters
 - estimate aleatoric and epistemic uncertainty
 - Gaussian process surrogate models for faster predictions
 - visualization of results

<br>



## Installation
    Before installing ACBICI, you need to install make, git and one of the tested Python versions (3.9, 3.12, 3.13, 3.14).

    Then, if using Python for other purposes than ACBICI, it is recommended to use a virtual environment, you can create one for example via:
    - python3 -m venv acbici_env
    or:
    - virtualenv acbici_env
    Then activate the virtual environment by:
    - source acbici_env/bin/activate

    Upgrade packaging tools (recommended):
    pip install --upgrade pip setuptools wheel

    or with Anaconda (Windows) in the Anaconda prompt to create a virtual environment:
    - conda create -n myenv python=3.14
    Then to activate it:
    - conda activate myenv

    Next you can install ACBICI in this virtual environment:
    Either:
    Go to the folder where you want to install it via: cd "installation_directory"
    Clone and install the repo into that folder in the following way:
    - git clone https://gitlab.com/schenkch/ACBICI.git
    - cd ACBICI
    - pip install -e .
    Or:
    Install as an already built pip package via:
    pip install ACBICI (pending)




### Examples and Tutorials

The example problems are in the examples subfolder at https://gitlab.com/schenkch/acbici/tree/master/examples.

    To run all the examples and test their correctness, open a terminal and change into the `examples` directory of the downloaded repository:
    cd examples

    Execute the following command:
    make

This will trigger the build process defined in the Makefile and run all the example problems within the folder.
This may take some time but if everything is set up correctly and all dependencies are satisfied, you should see output indicating whether each example has passed or failed.
In addition, each example subfolder contains a make file for automatic clean up of old results.



## License

BSD-3



## Authors

    - Christina Schenk - IMDEA Materials Institute
    - Ignacio Romero - UPM, IMDEA Materials Institute


## Acknowledgements

    - Yufei Liu - IMDEA Materials Institute



## Please cite
<br>

    - https://gitlab.com/schenkch/ACBICI.git
    - C. Schenk, I. Romero (2026): A Framework for the Bayesian Calibration of Complex and Data-Scarce Models in Applied Sciences
