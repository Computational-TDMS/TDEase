from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QLabel, QComboBox, QLineEdit, QPushButton,
                             QTextEdit, QFrame)
from PyQt5.QtGui import QFont
from .Setting import ToolsSetting



class WorkflowConfigTab(QWidget):
    def __init__(self, args):
        super().__init__()
        self.args = args
        self.ui = {}
        self.setting = ToolsSetting()
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        # style = """
        #     QGroupBox {
        #         background-color: #fafdff;
        #         border: 2px solid #b0b8c1;
        #         border-radius: 6px;
        #         margin-top: 12px;
        #         font-weight: bold;
        #     }
        #     QGroupBox::title {
        #         color: #3a506b;
        #         subcontrol-origin: margin;
        #         left: 10px;
        #         padding: 0 5px;
        #     }
        # """
        # Pipeline Mode
        mode_group = self._create_mode_group()
        # mode_group.setStyleSheet(style)
        layout.addWidget(mode_group)
        # Input Files
        file_group = self._create_file_group()
        # file_group.setStyleSheet(style)
        layout.addWidget(file_group)
        # FASTA
        fasta_group = self._create_fasta_group()
        # fasta_group.setStyleSheet(style)
        layout.addWidget(fasta_group)
        # Info
        info_group = self._create_info_group()
        # info_group.setStyleSheet(style)
        layout.addWidget(info_group)
        layout.addStretch()
        self.setLayout(layout)
    
    def _create_mode_group(self):
        group = QGroupBox("Pipeline Mode")
        layout = QHBoxLayout()
        mode_combo = QComboBox()
        mode_combo.addItems([
            "TopPIC Suite",
            "Informed Proteomics Full",
            "Informed Proteomics MS1-Only",
            "msconvert",
            "topfd",
            "toppic",
            "topmg",
            "pbfgen",
            "promex",
            "mspathfinder",
            "sum spectrum",
        ])
        self.args.set_config('workflow', None, 'TopPIC Suite')
        mode_combo.currentTextChanged.connect(
            lambda text: self._update_workflow_info(text)
        )
        self.ui['mode'] = mode_combo
        layout.addWidget(QLabel("Mode:"))
        layout.addWidget(mode_combo)
        group.setLayout(layout)
        return group
    
    def _create_file_group(self):
        group = QGroupBox("Input Files")
        layout = QHBoxLayout()
        ms_file_path_edit = QLineEdit()
        ms_file_path_edit.setPlaceholderText("Please select the path of MS files")
        ms_file_path_edit.textChanged.connect(
            lambda text: self.args.set_config('msfile', None, text.replace('\\', '/').split(';'))
        )
        self.ui['msfile'] = ms_file_path_edit
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(lambda: self._browse_ms_files(ms_file_path_edit))
        
        layout.addWidget(QLabel("MS file path:"))
        layout.addWidget(ms_file_path_edit)
        layout.addWidget(browse_btn)
        group.setLayout(layout)
        return group

    def _create_fasta_group(self):
        group = QGroupBox("FASTA Database")
        layout = QHBoxLayout()
        fasta_path_edit = QLineEdit()
        if self.setting.get_config('Fasta', 'fasta_path'):
            fasta_path_edit.setText(self.setting.get_config('Fasta', 'fasta_path'))
            self.args.set_config('fasta', None, self.setting.get_config('Fasta', 'fasta_path'))
        else:
            fasta_path_edit.setPlaceholderText("Please select the path of FASTA file")
        fasta_path_edit.textChanged.connect(lambda text: (self.args.set_config('fasta', None, text), self.setting.set_config('Fasta', 'fasta_path', text)))
        self.ui['fasta'] = fasta_path_edit
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(lambda: self._browse_fasta_file(fasta_path_edit))
        
        layout.addWidget(QLabel("FASTA file path:"))
        layout.addWidget(fasta_path_edit)
        layout.addWidget(browse_btn)
        group.setLayout(layout)
        return group

    def _create_info_group(self):
        group = QGroupBox("Workflow Information")
        layout = QVBoxLayout()
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMinimumHeight(150)
        self.ui['info'] = info_text
        # Set initial workflow info
        self._update_workflow_info("TopPIC Suite")
        
        layout.addWidget(info_text)
        group.setLayout(layout)
        return group
        
    def _update_workflow_info(self, workflow_name):
        info_text = ""
        if workflow_name == "TopPIC Suite":
            info_text = """TopPIC Suite is a complete workflow for top-down proteomics analysis:
1. MSConvert: Converts raw MS data to mzML format
2. TopFD: Performs feature detection and deconvolution
3. TopPIC: Identifies proteoforms and performs database search

Supported file formats: .raw, .mzML

This workflow is suitable for comprehensive top-down proteomics analysis."""
        elif workflow_name == "Informed Proteomics Full":
            info_text = """Informed Proteomics Full workflow includes:
1. PBFGen: Converts mzML to pbf format
2. Promex: Performs feature detection
3. MSPathFinderT: Performs database search

Supported file formats: .raw, .mzML

This workflow is optimized for high-throughput proteomics analysis."""
        elif workflow_name == "Informed Proteomics MS1-Only":
            info_text = """Informed Proteomics MS1-Only workflow includes:
1. PBFGen: Converts mzML to pbf format
2. Promex: Performs feature detection

Supported file formats: .raw, .mzML

This workflow is suitable for MS1-level analysis only."""
        elif workflow_name == "msconvert":
            info_text = """MSConvert is a tool for converting mass spectrometry data files between different formats.
It supports various input formats and can convert them to mzML, mzXML, or other formats.

Supported file formats: .raw, .mzML, .mzXML, .mzData, .mz5, .mzML.gz, .mzXML.gz, .mzData.gz, .mz5.gz
"""
        elif workflow_name == "topfd":
            info_text = """TopFD is a tool for feature detection and deconvolution in top-down proteomics.
It can detect features and deconvolute MS/MS spectra to identify proteoforms.

Supported file formats: .mzML
"""
        elif workflow_name == "toppic":
            info_text = """TopPIC is a tool for proteoform identification in top-down proteomics.
It can identify proteoforms and perform database search using MS/MS spectra.

Supported file formats: .msalign
"""
        elif workflow_name == "topmg":
            info_text = """TopMG is a tool for proteoform identification in top-down proteomics.
It can identify proteoforms and perform database search using MS/MS spectra."""
        elif workflow_name == "pbfgen":
            info_text = """PBFGen is a tool for converting mzML files to pbf format.
It is used in the Informed Proteomics workflow.

Supported file formats: .raw, .mzML
"""
        elif workflow_name == "promex":
            info_text = """Promex is a tool for feature detection in mass spectrometry data.
It can detect features in MS1 spectra and is used in the Informed Proteomics workflow.

Supported file formats: .pbf
"""
        elif workflow_name == "mspathfinder":
            info_text = """MSPathFinder is a tool for database search in mass spectrometry data.
It can identify peptides and proteins from MS/MS spectra.

Supported file formats: .ms1ft
"""
        elif workflow_name == "sum spectrum":
            info_text = """Spectrum Summing is a tool for combining multiple MS spectra.
It can sum spectra based on different methods:
1. Block Summing: Sums spectra in fixed-size blocks
2. Range Summing: Sums spectra within a specified scan range
3. Precursor Summing: Sums spectra based on precursor m/z and retention time

Supported file formats: .mzML
"""
        
        self.ui['info'].setText(info_text)
        self.args.set_config('workflow', None, workflow_name)
                
    def _browse_ms_files(self, ms_file_path_edit):
        from PyQt5.QtWidgets import QFileDialog
        filenames, _ = QFileDialog.getOpenFileNames(self, "Select MS files")
        if filenames:
            ms_file_path_edit.setText(";".join(filenames))
            self.args.clear_msfile()
            for filename in filenames:
                self.args.add_msfile(filename)
                
    def _browse_fasta_file(self, fasta_path_edit):
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(self, "Select FASTA file")
        if filename:
            fasta_path_edit.setText(filename)
            self.args.set_config('fasta', None, filename)
            self.setting.set_config('Fasta', 'fasta_path', filename)