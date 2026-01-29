# ifp_organizer

The library aims to load files containing fingerprint interactions between ligands and proteins, display the data, allow users to make selections and apply filters, and visualize the results through graphical representations.

---

## Table of Contents
1. [Features](#features)
2. [Library Structure](#library-structure)
3. [Installation](#installation)
4. [License](#license)

---

## Features
- **Analyze Interaction Data:** Analyze interaction data files by categorizing interactions by protein and ligand atoms.
- **Filter Matrix:** Filter matrix data by interaction type and protein subunits for targeted analysis.
- **Visualize Data:** Plot bar or pie charts of selected matrix data and save as PNG files.
- **Select Reactive Data:** Sort and select reactive rows or columns based on interaction criteria.

---

## Library Structure

```plaintext
.
├── pickit/
│   ├── analyze_interactions.py     # Core functionalities of the library
│   └── __init__.py                 # Module initialization
├── setup.py                        # Installation and packaging script
├── LICENSE.txt                     # License file for the library
└── README.md                       # Library documentation (this file)
```

---

## Installation

### Prerequisites

- Python 3.12

### Install Library

```sh
pip install pickit-urv
```

---

## License

This library is licensed under the **[GNU AFFERO GENERAL PUBLIC LICENSE](LICENSE.txt)**. See the [LICENSE.txt](LICENSE.txt) file for complete details.
