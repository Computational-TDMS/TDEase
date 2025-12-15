# 🧪 TDEase - an Open-Source Data Visualization Software Framework for Targeted Proteoform Characterization by Top-Down Proteomics

## Language
[English](README.md) | [中文](README_zh.md)

## ✨ Introduction
✨ TDEase is an automated data processing and interactive visualization toolkit designed specifically for top-down proteomics research.

It helps laboratories quickly build the data processing and visualization components of a top-down proteomics workflow.

It consists of two core modules:
- 🛠️ **TDPipe**: Automated data processing engine
- 📊 **TDVis**: Interactive data visualization platform

The demo data for TDVis is available at [Zenodo](https://zenodo.org/records/15527298).

## 🌟 Key Features

1. **One-Click Deployment** 🚀  
   Both modules provide ready-to-use exe packages, requiring no complex configuration, see [releases](https://github.com/Elcherneske/TDEase/releases).
2. **Thoughtful UI Design**:
    - TDpipe uses PyQt to create a sophisticated workflow control interface, allowing platform administrators high flexibility.
    - TDvis uses Streamlit to provide a minimalist, almost parameter-free interface, making it easy for users to quickly get started with data viewing.
3. **Intranet Web Deployment**:
    - The visualization module can be deployed on an intranet using Python's [http.server](https://docs.python.org/3.13/library/http.server.html), allowing collaborators to access results remotely without transferring large mass spectrometry files.
    - ⚠️ Note: Due to HTTP's plaintext nature, public internet deployment is not recommended.
    - For external collaborators, you can simply send the result files, and users can view them locally with TDvis.

---

## Quick Start

### 📥 Installation
Download the released setup package, double-click the corresponding exe to run:
- `TDPipe.exe`: automated data processing engine
- `TDVis.exe`: standalone data visualization platform
- `TDVisWeb.exe`: web data visualization platform

🌐 to access the web data visualization platform:  
1. click the visualization button in TDPipe
2. run TDVisWeb.exe/TDVis.exe and enter the url `http://{your_ip}:8501` in explorer

### TDPipe Workflow Configuration

TDPipe is a GUI-based top-down proteomics data processing workflow integration tool. With a rich set of buttons, you can easily invoke each module, set workflow parameters, and run the workflow automatically.

### TDVis Database Configuration
If you do not need user authentication, you can skip this section.

#### PostgreSQL
The TDVisWeb version uses [PostgreSQL](https://www.postgresql.org/) by default for user management.

PostgreSQL provides detailed official documentation. Simply follow the guide to create an initial database using pgAdmin, then configure it in `TDVis/DBUtils/dbconfig.toml`!

#### SQLite

If you want to use SQLite for quick testing, simply modify the parameter file as follows:

```
[database]
mode = "sqlite"
dbname = "{your_path}/TDEase/TDVis/src/DBUtils/TDVis_sqlite3.db"
```

---

## For Developers

*If you have unique feature requirements, we welcome your contributions!*

Recommended steps for collaborative development:

1. **Source Code Download**
```pwsh
git clone https://github.com/Elcherneske/TDEase.git && cd TDEase
```

2. **Dependency Installation**

We recommend using [uv](https://docs.astral.sh/uv/) for fast deployment instead of pip.

```pwsh
uv install -r requirements.txt
```

or 

```pwsh
uv pip install -r requirements.txt --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

Alternatively, you can use [conda](https://anaconda.org/anaconda/conda) for environment management (slower, but reusable across projects):

```pwsh
conda create -n tdease python=3.12 -y
conda activate tdease
pip install -r requirements.txt
```

### TDpipe

To run TDPipe:

```pwsh
cd TDEase/TDPipe
python src/TDPipe.py
```

### TDvis

Our web service is built on [Streamlit](https://docs.streamlit.io/develop/api-reference). For collaborative development and debugging, run the following command in the TDVis folder:

```pwsh
cd TDEase/TDVis
streamlit run MainPage.py
```


## Publications && Citation
If you find our work helpful, please consider citing us in your publications.

Liao Y, Qian R, Zhang M, et al. TDEase: An Open‐Source Data Visualization Software Framework for Targeted Proteoform Characterization by Top‐Down Proteomics[J]. Proteomics, 2025: e70031.







