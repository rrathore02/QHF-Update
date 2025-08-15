# qhf_config_gui.py

import os
import sys
import subprocess
import configparser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# to discover modules safely
import importlib.util

# to ensure relative paths resolve from repo root
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIGS_DIR = os.path.join(REPO_ROOT, "Configs")
HABITATS_DIR = os.path.join(REPO_ROOT, "Habitats")
METABOLISMS_DIR = os.path.join(REPO_ROOT, "Metabolisms")
ANALYSES_DIR = os.path.join(REPO_ROOT, "Analyses")
QHF_SCRIPT = os.path.join(REPO_ROOT, "QHF.py")
LAST_CFG_PATH = os.path.join(REPO_ROOT, ".last_saved_cfg.txt")


# to make sure expected folders exist
for _d in [CONFIGS_DIR, HABITATS_DIR, METABOLISMS_DIR, ANALYSES_DIR]:
    os.makedirs(_d, exist_ok=True)

# to list python files without __init__.py
def _list_py_modules(folder):
    # to list all .py files except __init__.py
    files = []
    for f in os.listdir(folder):
        if f.endswith(".py") and f != "__init__.py":
            files.append(os.path.splitext(f)[0])
    files.sort()
    return files

# to build default template values
def default_template():
    # to provide a sensible starter config
    cfg = configparser.ConfigParser()
    cfg["Configuration"] = {
        "ConfigID": "New configuration"
    }
    cfg["Habitat"] = {
        "HabitatFile": "",
        "HabitatModule": "",
        "HabitatLogo": "Assets/habitat_logo.png",
        "HabitatShortname": "custom"
    }
    cfg["Metabolism"] = {
        "MetabolismFile": "",
        "MetabolismModule": ""
    }
    cfg["Visualization"] = {
        "VisualizationFile": "",
        "VisualizationModule": ""
    }
    cfg["Sampling"] = {
        "NumProbes": "100",
        "Niterations": "50"
    }
    return cfg

class QHFConfigGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QHF Config Editor")
        self.geometry("900x600")

        # to track current file path
        self.current_cfg_path = None

        # to cache dropdown data
        self.habitat_files = _list_py_modules(HABITATS_DIR)
        self.metabolism_files = _list_py_modules(METABOLISMS_DIR)
        self.analysis_files = _list_py_modules(ANALYSES_DIR)

        # to create UI
        self._build_menu()
        self._build_main()
        self._build_footer()

        # to load an empty template initially
        self.config_obj = default_template()
        self.populate_form_from_config(self.config_obj)

    # to build the menu bar
    def _build_menu(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=False)
        filemenu.add_command(label="New", command=self.new_config)
        filemenu.add_command(label="Open .cfg", command=self.open_config)
        filemenu.add_separator()
        filemenu.add_command(label="Save", command=self.save_config)
        filemenu.add_command(label="Save As…", command=self.save_as_config)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=filemenu)

        runmenu = tk.Menu(menubar, tearoff=False)
        runmenu.add_command(label="Run QHF", command=self.run_qhf)
        menubar.add_cascade(label="Run", menu=runmenu)

        self.config(menu=menubar)

    # to build main tabs and fields
    def _build_main(self):
        # to hold everything
        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        # to create tabs
        self.tabs = ttk.Notebook(container)
        self.tabs.pack(fill="both", expand=True)

        # to create frames for each section
        self.tab_cfg = ttk.Frame(self.tabs)
        self.tab_hab = ttk.Frame(self.tabs)
        self.tab_met = ttk.Frame(self.tabs)
        self.tab_vis = ttk.Frame(self.tabs)
        self.tab_sam = ttk.Frame(self.tabs)

        self.tabs.add(self.tab_cfg, text="Configuration")
        self.tabs.add(self.tab_hab, text="Habitat")
        self.tabs.add(self.tab_met, text="Metabolism")
        self.tabs.add(self.tab_vis, text="Visualization")
        self.tabs.add(self.tab_sam, text="Sampling")

        # to add fields to each tab
        self._build_config_tab()
        self._build_habitat_tab()
        self._build_metabolism_tab()
        self._build_visualization_tab()
        self._build_sampling_tab()

    # to build bottom buttons
    def _build_footer(self):
        footer = ttk.Frame(self, padding=(10,5))
        footer.pack(fill="x")

        self.lbl_status = ttk.Label(footer, text="Ready")
        self.lbl_status.pack(side="left")

        btn_run = ttk.Button(footer, text="Run QHF", command=self.run_qhf)
        btn_run.pack(side="right", padx=5)

        btn_save = ttk.Button(footer, text="Save", command=self.save_config)
        btn_save.pack(side="right", padx=5)

        btn_saveas = ttk.Button(footer, text="Save As…", command=self.save_as_config)
        btn_saveas.pack(side="right")

    # to quickly place labeled entry
    def _add_labeled_entry(self, parent, label, var, row, col=0, width=60, entry_type="entry"):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", padx=4, pady=4)
        if entry_type == "entry":
            e = ttk.Entry(parent, textvariable=var, width=width)
        elif entry_type == "combo":
            e = ttk.Combobox(parent, textvariable=var, width=width, state="readonly")
        else:
            e = ttk.Entry(parent, textvariable=var, width=width)

        e.grid(row=row, column=col+1, sticky="we", padx=4, pady=4)
        return e

    # to clear and rebuild all widgets on a tab (helps avoid stale state)
    def clear_form(self):
        # to clear all field variables
        self.var_ConfigID.set("")
        self.var_HabitatFile.set("")
        self.var_HabitatModule.set("")
        self.var_HabitatLogo.set("")
        self.var_HabitatShortname.set("")
        self.var_MetabolismFile.set("")
        self.var_MetabolismModule.set("")
        self.var_VisualizationFile.set("")
        self.var_VisualizationModule.set("")
        self.var_NumProbes.set("")
        self.var_Niterations.set("")

    # to build "Configuration" tab
    def _build_config_tab(self):
        self.tab_cfg.columnconfigure(1, weight=1)
        self.var_ConfigID = tk.StringVar()

        self._add_labeled_entry(self.tab_cfg, "ConfigID", self.var_ConfigID, row=0)

    # to build "Habitat" tab
    def _build_habitat_tab(self):
        self.tab_hab.columnconfigure(1, weight=1)
        self.var_HabitatFile = tk.StringVar()
        self.var_HabitatModule = tk.StringVar()
        self.var_HabitatLogo = tk.StringVar()
        self.var_HabitatShortname = tk.StringVar()

        # to choose from discovered habitat files
        e_file = self._add_labeled_entry(self.tab_hab, "HabitatFile (.py without .py)", self.var_HabitatFile, row=0, entry_type="combo")
        e_file["values"] = self.habitat_files

        self._add_labeled_entry(self.tab_hab, "HabitatModule (class name)", self.var_HabitatModule, row=1)
        self._add_labeled_entry(self.tab_hab, "HabitatLogo (path)", self.var_HabitatLogo, row=2)
        self._add_labeled_entry(self.tab_hab, "HabitatShortname", self.var_HabitatShortname, row=3)

        # to browse logo path
        def browse_logo():
            p = filedialog.askopenfilename(initialdir=REPO_ROOT, title="Select Habitat Logo")
            if p:
                rel = os.path.relpath(p, REPO_ROOT)
                self.var_HabitatLogo.set(rel)
        btn_browse = ttk.Button(self.tab_hab, text="Browse Logo…", command=browse_logo)
        btn_browse.grid(row=2, column=2, padx=4, pady=4, sticky="w")

    # to build "Metabolism" tab
    def _build_metabolism_tab(self):
        self.tab_met.columnconfigure(1, weight=1)
        self.var_MetabolismFile = tk.StringVar()
        self.var_MetabolismModule = tk.StringVar()

        e_file = self._add_labeled_entry(self.tab_met, "MetabolismFile (.py without .py)", self.var_MetabolismFile, row=0, entry_type="combo")
        e_file["values"] = self.metabolism_files

        self._add_labeled_entry(self.tab_met, "MetabolismModule (class name)", self.var_MetabolismModule, row=1)

    # to build "Visualization" tab
    def _build_visualization_tab(self):
        self.tab_vis.columnconfigure(1, weight=1)
        self.var_VisualizationFile = tk.StringVar()
        self.var_VisualizationModule = tk.StringVar()

        e_file = self._add_labeled_entry(self.tab_vis, "VisualizationFile (.py without .py)", self.var_VisualizationFile, row=0, entry_type="combo")
        e_file["values"] = self.analysis_files

        self._add_labeled_entry(self.tab_vis, "VisualizationModule (callable/class)", self.var_VisualizationModule, row=1)

    # to build "Sampling" tab
    def _build_sampling_tab(self):
        self.tab_sam.columnconfigure(1, weight=1)
        self.var_NumProbes = tk.StringVar()
        self.var_Niterations = tk.StringVar()

        self._add_labeled_entry(self.tab_sam, "NumProbes", self.var_NumProbes, row=0)
        self._add_labeled_entry(self.tab_sam, "Niterations", self.var_Niterations, row=1)

    # to populate GUI from config object
    def populate_form_from_config(self, cfg):
        # to reset all fields first
        self.clear_form()

        # to set values from config
        self.var_ConfigID.set(cfg.get("Configuration", "ConfigID", fallback=""))

        self.var_HabitatFile.set(cfg.get("Habitat", "HabitatFile", fallback=""))
        self.var_HabitatModule.set(cfg.get("Habitat", "HabitatModule", fallback=""))
        self.var_HabitatLogo.set(cfg.get("Habitat", "HabitatLogo", fallback="Assets/habitat_logo.png"))
        self.var_HabitatShortname.set(cfg.get("Habitat", "HabitatShortname", fallback="custom"))

        self.var_MetabolismFile.set(cfg.get("Metabolism", "MetabolismFile", fallback=""))
        self.var_MetabolismModule.set(cfg.get("Metabolism", "MetabolismModule", fallback=""))

        self.var_VisualizationFile.set(cfg.get("Visualization", "VisualizationFile", fallback=""))
        self.var_VisualizationModule.set(cfg.get("Visualization", "VisualizationModule", fallback=""))

        self.var_NumProbes.set(cfg.get("Sampling", "NumProbes", fallback="100"))
        self.var_Niterations.set(cfg.get("Sampling", "Niterations", fallback="50"))

        # to update window title/status
        name = os.path.basename(self.current_cfg_path) if self.current_cfg_path else "(unsaved)"
        self.lbl_status.config(text=f"Loaded: {name}")

    # to build a config object from GUI fields
    def build_config_from_form(self):
        cfg = configparser.ConfigParser()

        # to write sections and keys
        cfg["Configuration"] = {
            "ConfigID": self.var_ConfigID.get().strip()
        }
        cfg["Habitat"] = {
            "HabitatFile": self.var_HabitatFile.get().strip(),
            "HabitatModule": self.var_HabitatModule.get().strip(),
            "HabitatLogo": self.var_HabitatLogo.get().strip(),
            "HabitatShortname": self.var_HabitatShortname.get().strip()
        }
        cfg["Metabolism"] = {
            "MetabolismFile": self.var_MetabolismFile.get().strip(),
            "MetabolismModule": self.var_MetabolismModule.get().strip()
        }
        cfg["Visualization"] = {
            "VisualizationFile": self.var_VisualizationFile.get().strip(),
            "VisualizationModule": self.var_VisualizationModule.get().strip()
        }
        cfg["Sampling"] = {
            "NumProbes": self.var_NumProbes.get().strip(),
            "Niterations": self.var_Niterations.get().strip()
        }
        return cfg

    # to validate core fields before saving/running
    def validate(self, cfg):
        # to ensure required fields exist
        required = [
            ("Configuration", "ConfigID"),
            ("Habitat", "HabitatFile"),
            ("Habitat", "HabitatModule"),
            ("Habitat", "HabitatShortname"),
            ("Metabolism", "MetabolismFile"),
            ("Metabolism", "MetabolismModule"),
            ("Visualization", "VisualizationFile"),
            ("Visualization", "VisualizationModule"),
            ("Sampling", "NumProbes"),
            ("Sampling", "Niterations"),
        ]
        for sec, key in required:
            if not cfg.get(sec, key, fallback="").strip():
                messagebox.showerror("Validation Error", f"Missing value: [{sec}] {key}")
                return False

        # to check files exist
        hab_py = os.path.join(HABITATS_DIR, cfg["Habitat"]["HabitatFile"] + ".py")
        met_py = os.path.join(METABOLISMS_DIR, cfg["Metabolism"]["MetabolismFile"] + ".py")
        vis_py = os.path.join(ANALYSES_DIR, cfg["Visualization"]["VisualizationFile"] + ".py")

        if not os.path.isfile(hab_py):
            messagebox.showerror("Validation Error", f"Habitat file not found:\n{hab_py}")
            return False
        if not os.path.isfile(met_py):
            messagebox.showerror("Validation Error", f"Metabolism file not found:\n{met_py}")
            return False
        if not os.path.isfile(vis_py):
            messagebox.showerror("Validation Error", f"Visualization file not found:\n{vis_py}")
            return False

        # to basic-type check sampling
        try:
            _ = float(cfg["Sampling"]["NumProbes"])
            _ = int(cfg["Sampling"]["Niterations"])
        except Exception:
            messagebox.showerror("Validation Error", "NumProbes must be a number and Niterations must be an integer.")
            return False

        # to optionally check module/class loadability (best effort)
        def _can_load(py_path, class_name):
            try:
                spec = importlib.util.spec_from_file_location("modtmp", py_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # to import it
                getattr(mod, class_name)      # to ensure class/function exists
                return True
            except Exception:
                return False

        if not _can_load(hab_py, cfg["Habitat"]["HabitatModule"]):
            messagebox.showwarning("Module Check", "Could not load HabitatModule from file. Make sure class name matches.")
        if not _can_load(met_py, cfg["Metabolism"]["MetabolismModule"]):
            messagebox.showwarning("Module Check", "Could not load MetabolismModule from file. Make sure class name matches.")
        # Visualization can be class or callable; we skip strict check here

        return True

    # to update window title
    def _update_title(self):
        name = os.path.basename(self.current_cfg_path) if self.current_cfg_path else "(unsaved)"
        self.title(f"QHF Config Editor — {name}")

    # to file → New
    def new_config(self):
        self.current_cfg_path = None
        self.config_obj = default_template()
        self.populate_form_from_config(self.config_obj)
        self._update_title()

    # to file → Open
    def open_config(self):
        path = filedialog.askopenfilename(
            title="Open QHF .cfg",
            initialdir=CONFIGS_DIR,
            filetypes=[("Config files", "*.cfg"), ("All files", "*.*")]
        )
        if not path:
            return
        cfg = configparser.ConfigParser()
        try:
            cfg.read(path)
            if not cfg.sections():
                messagebox.showerror("Open Error", "Selected file is not a valid .cfg.")
                return
            self.current_cfg_path = path
            self.config_obj = cfg
            self.populate_form_from_config(cfg)
            self._update_title()
        except Exception as e:
            messagebox.showerror("Open Error", str(e))

    # to file → Save
    def save_config(self):
        cfg = self.build_config_from_form()
        if not self.validate(cfg):
            return
        if not self.current_cfg_path:
            return self.save_as_config()
        try:
            with open(self.current_cfg_path, "w") as f:
                cfg.write(f)
            # NEW: save handoff path for launcher auto-run
            try:
                with open(LAST_CFG_PATH, "w") as h:
                    h.write(self.current_cfg_path)
            except Exception:
                pass
            self.lbl_status.config(text=f"Saved: {os.path.basename(self.current_cfg_path)}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))


    # to file → Save As
    def save_as_config(self):
        cfg = self.build_config_from_form()
        if not self.validate(cfg):
            return
        path = filedialog.asksaveasfilename(
            title="Save QHF .cfg As",
            initialdir=CONFIGS_DIR,
            defaultextension=".cfg",
            filetypes=[("Config files", "*.cfg")]
        )
        if not path:
            return
        try:
            with open(path, "w") as f:
                cfg.write(f)
            self.current_cfg_path = path
            # NEW: save handoff path for launcher auto-run
            try:
                with open(LAST_CFG_PATH, "w") as h:
                    h.write(self.current_cfg_path)
            except Exception:
                pass
            self._update_title()
            self.lbl_status.config(text=f"Saved: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Save As Error", str(e))


    # to run QHF.py with current/selected config
    def run_qhf(self):
        # to ensure we have a saved file path
        if not self.current_cfg_path:
            if not messagebox.askyesno("Run QHF", "Config is not saved. Save As now?"):
                return
            self.save_as_config()
            if not self.current_cfg_path:
                return
        if not os.path.isfile(QHF_SCRIPT):
            messagebox.showerror("Run Error", f"QHF.py not found at:\n{QHF_SCRIPT}")
            return

        # to call python QHF.py "<config>"
        try:
            cmd = [sys.executable, QHF_SCRIPT, self.current_cfg_path]
            # to show a small terminal-like popup with output would be nice; keep it simple here
            subprocess.Popen(cmd, cwd=REPO_ROOT)
            messagebox.showinfo("QHF", "Started QHF in a separate process.")
        except Exception as e:
            messagebox.showerror("Run Error", str(e))

if __name__ == "__main__":
    app = QHFConfigGUI()
    app.mainloop()
