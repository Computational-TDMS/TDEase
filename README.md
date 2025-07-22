# 🧪 TDEase - Top-Down Proteomics Tools

## Language
[English](README.md) | [中文](README_zh.md)

## ✨ Introduction
✨ TDEase is an automated data processing and interactive visualization toolkit designed specifically for Top-Down proteomics research.

It helps laboratories quickly build the data processing and visualization components of a Top-Down proteomics workflow.

It consists of two core modules:
- 🛠️ **TDpipe**: Automated data processing pipeline
- 📊 **TDvis**: Interactive data visualization platform

## 🌟 Key Features

1. **One-Click Deployment** 🚀  
   Both modules provide ready-to-use exe packages, requiring no complex configuration.
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
Download the release package, unzip it, and double-click the corresponding exe to run:
- `TDvis.exe`: Standalone version (no user management)
- `TDvis_web.exe`: Web version with user authentication

🌐 Access:  
`http://{your_ip}:8501`

TDvis provides two parallel exe entry points:
**TDvis.exe:**  
Run the local version without user management (collaborators can view your data on the intranet, but files must be selected manually; visitors cannot choose files).

**TDvis_web.exe:**  
Provides a version with user management. After configuring the user management database, you can deploy the test platform.

Both versions map the program to port 8501. Users can access your shared data via your IP and port:


```
http://{your_ip}:8501
```

### TDpipe Workflow Configuration

### TDvis Database Configuration
If you do not need user authentication, you can skip this section.

#### PostgreSQL
The TDvis_web version uses [PostgreSQL](https://www.postgresql.org/) by default for user management.

PostgreSQL provides detailed official documentation. Simply follow the guide to create an initial database using pgAdmin, then configure it in `TDvis/DBUtils/dbconfig.toml`!

#### SQLite

If you want to use SQLite for quick testing, simply modify the parameter file as follows:

```
[database]
mode = "sqlite"
dbname = "{your_path}/TDEase/TDVis/src/DBUtils/TDvis_sqlite3.db"
```

## For Developers

*If you have unique feature requirements, we welcome your contributions!*

Recommended steps for collaborative development:

1. **Source Code Download**
```pwsh
git clone https://github.com/Elcherneske/TDEase.git && cd TDease
```

2. **Dependency Installation**

We recommend using [uv](https://docs.astral.sh/uv/) for fast deployment instead of pip.

```pwsh
uv install -r requirements.txt
```

If you are in China, use the following command:

```pwsh
uv pip install -r requirements.txt --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

Alternatively, you can use [conda](https://anaconda.org/anaconda/conda) for environment management (slower, but reusable across projects):

```pwsh
conda create -n tdvis python=3.10 -y
conda activate tdvis
pip install -r requirements.txt
```

### TDpipe
TDpipe uses PyQt for its GUI, located in the `GUI` folder.

### TDvis

1. **Run Streamlit**

Our web service is built on [Streamlit](https://docs.streamlit.io/develop/api-reference). For collaborative development and debugging, run the following command in the TDvis folder:

```pwsh
cd TDvis
python launch.py  / python launch_web.py
```

2. **Packaging**

Since Streamlit requires command-line startup, we provide a `launch.py` file for command-line execution. When running PyInstaller, this file is used as the packaging target.

First, install PyInstaller in your virtual environment (tested to work in cmd, but may not activate in PowerShell):

```pwsh
pip install pyinstaller
```

The `launch.spec` packaging configuration file is ready. If you want to change the icon or add new dependencies, you can modify it as needed. Then, run the following in the TDvis folder:

```pwsh
pyinstaller launch.spec --clean
```

## TDpipe

TDpipe is a GUI-based Top-Down proteomics data processing workflow integration tool. With a rich set of buttons, you can easily invoke each module, set workflow parameters, and run the workflow automatically.

## TDvis

TDvis provides interactive visualization of TopPic results processed by TDpipe, helping researchers quickly locate target proteins from the feature map and perform custom modification analysis.

With a simple, linear operation logic and step-by-step guidance, TDvis is accessible even to users unfamiliar with proteomics.

A detailed user manual is embedded within the program—explore it after launching the application!

## Publications
If you find our work helpful, please consider citing us in your publications.

