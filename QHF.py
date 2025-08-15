# ======================================
# Imports
# ======================================

import sys
import os
sys.path.append('./Habitats')
sys.path.append('./Metabolisms')
sys.path.append('./Analyses')

from collections import defaultdict
import math
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import style
import matplotlib.patches as patches
import importlib
import configparser  # For handling configuration files
import pdb           # Python debugger
import keyparams
from mcmodules import Module as Module
from layout_presets import presets, label_offsets
import importlib.util

# ======================================
# Program Flow
# ======================================
# 1) Configure/load modules
# 2) Translate connections between modules to graph
# 3) Visualize Graph
# 4) Apply topological sorting to graph
# 5) Evaluate vertices following the sorted graph
# 6) Analyze results
# 7) Visualize and save results

# ======================================
# Graph Visualization Class
# ======================================

class GraphVisualization:
    def __init__(self):
        self.visual = []

    def addEdge(self, a, b, label):
        self.visual.append([a, b])

    def visualize(self):
        G = nx.DiGraph()
        G.add_edges_from(self.visual)

        # Choose layout spacing and pull offsets for current config
        preset_name = HabitatShortName.lower()
        offset_dict = presets.get(preset_name, {})
        label_dict = label_offsets.get(preset_name, {})

        # Spread out graph layout
        pos = nx.spring_layout(G, seed=42, k=0.7, scale=3.0, iterations=150)

        for node, label in mod_labels.items():
            normalized_label = label.replace('\n', ' ').strip()
            x, y = pos[node]
            dx, dy = offset_dict.get(label, (0.00, 0.00))
            pos[node] = (x + dx, y + dy)

        # Node color logic
        node_colors = [
            prior_node_color if len(Modules[node].input_parameters) == 0
            else metabolism_node_color if 'Suitability' in Modules[node].output_parameters
            else other_node_color
            for node in G
        ]

        node_size_val = 12 * sf  # Unified box size

        # Draw background layers
        if screen:
            nx.draw_networkx(
                G, pos, arrows=False, arrowsize=3.0 * sf, with_labels=False,
                width=3 * sf, alpha=0.02, edge_color=selected_edgecolor,
                node_color="white", node_size=70 * sf
            )
            nx.draw_networkx(
                G, pos, arrows=False, arrowsize=3.0 * sf, with_labels=False,
                width=2 * sf, alpha=0.05, edge_color=selected_edgecolor,
                node_color=node_colors, node_size=50 * sf
            )

        # Main network draw
        nx.draw_networkx(
            G, pos, arrows=True, arrowsize=3.0 * sf, with_labels=False,
            width=0.5 * sf, alpha=0.7, edge_color=selected_edgecolor,
            node_color=node_colors, node_size=node_size_val
        )

        # Edge label cleanup
        for idx, varlabel_key in enumerate(edge_labels):
            if edge_labels[varlabel_key] == 'Surface Temperature':
                edge_labels[varlabel_key] = 'Temperature'
            elif edge_labels[varlabel_key] == 'Surface Pressure':
                edge_labels[varlabel_key] = 'Pressure'

        nx.draw_networkx_edge_labels(
            G, pos, edge_labels=edge_labels, label_pos=0.4, rotate=False,
            font_color=selected_edgecolor, font_size=1.6 * sf,
            font_weight='light', bbox=dict(alpha=0.2, fc=bkgcolor, ec=labelcolor, linewidth=0.1 * sf),
            clip_on=True
        )

        # Label placement
        pos_upper = {}
        for k, v in pos.items():
            label = mod_labels[int(k)]
            pos_upper[k] = (v[0], v[1] + 0.05)

        nx.draw_networkx_labels(
            G, pos_upper, mod_labels, font_size=1.8 * sf,
            font_color=labelcolor, font_weight='light',
            horizontalalignment='center', verticalalignment="bottom"
        )

        plt.title(
            'Connections between Modules', color=labelcolor, fontsize=5,
            bbox=dict(alpha=0.1, fc=bkgcolor, ec=bkgcolor, linewidth=0.)
        )

        plt.axis("off")
        ax = plt.gca()

        if screen:
            rect = patches.Rectangle(
                (0., 0.), 1., 1., linewidth=0.2, edgecolor='lightblue',
                facecolor='none', transform=ax.transAxes
            )
            ax.add_patch(rect)

        return ax


# ======================================
# Load Configuration File
# ======================================

cl_args = sys.argv
config_file_path = str(cl_args[1])
config = configparser.ConfigParser()
config.read(config_file_path)

ConfigID = config['Configuration']['ConfigID']
HabitatFile = config['Habitat']['HabitatFile']
HabitatModule = config['Habitat']['HabitatModule']
HabitatLogo = os.path.join(os.path.dirname(__file__), config['Habitat']['HabitatLogo'])
HabitatShortName = config['Habitat']['HabitatShortname']

MetabolismFile = os.path.splitext(config['Metabolism']['MetabolismFile'])[0]
MetabolismModule = config['Metabolism']['MetabolismModule']

VisualizationFile = os.path.splitext(config['Visualization']['VisualizationFile'])[0]
VisualizationModule = config['Visualization']['VisualizationModule']

NumProbes = config['Sampling']['NumProbes']
if float(NumProbes) > 1e8:
    print('### Warning: Number of Probes limited -- change QHF code if you need more probes.')
NumProbes = np.clip(float(NumProbes), 1, 1e8)

print(' [ Configuration file: ]', ConfigID)
print(' [ Habitat Module: ]', HabitatModule)
print(' [ Metabolism Module: ]', MetabolismModule)
print(' [ Visualization Module: ]', VisualizationModule)


# ======================================
# Dynamic Import Function
# ======================================

def dynamic_import(module_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ======================================
# Import Modules Dynamically
# ======================================

# Habitat module
habitat_path = os.path.join(os.path.dirname(__file__), "Habitats", HabitatFile + ".py")
habitat_module = dynamic_import(habitat_path, HabitatModule)
Modules = getattr(habitat_module, HabitatModule)()

# Metabolism module
metabolism_path = os.path.join(os.path.dirname(__file__), "Metabolisms", MetabolismFile + ".py")
metabolism_module = dynamic_import(metabolism_path, MetabolismModule)
ModuleHabitability = getattr(metabolism_module, MetabolismModule)()
Modules.append(ModuleHabitability)

nmods = len(Modules)

# Visualization module
visual_path = os.path.join(os.path.dirname(__file__), "Analyses", VisualizationFile + ".py")
visual_module = dynamic_import(visual_path, VisualizationModule)
VisualizationModule = getattr(visual_module, VisualizationModule)

print('[Modules Loaded]')
for mi in np.arange(nmods):
    print(mi, ' : ', Modules[mi].name)


# ======================================
# Plotting Mode Configuration
# ======================================

screen = False  # True for dark theme, False for light theme

if screen:
    sf = 1.0
    bkgcolor = '#030810'
    selected_edgecolor = 'white'
    prior_node_color = 'blue'
    other_node_color = 'lightblue'
    metabolism_node_color = 'green'
    labelcolor = 'lightblue'
    labeloffset = 0.0
else:
    sf = 1.3
    bkgcolor = 'white'
    selected_edgecolor = 'darkblue'
    prior_node_color = 'red'
    other_node_color = 'blue'
    metabolism_node_color = 'green'
    labelcolor = 'black'
    labeloffset = -0.05


# ======================================
# Build Graph from Modules
# ======================================

G = GraphVisualization()
edge_labels = {}
mod_labels = {}

for jj in np.arange(nmods):
    mod_labels[int(jj)] = Modules[jj].name
    print('--------------------------------------------------------------------------------')
    print('Identifying input connections for module ', Modules[jj].name)

    for ip in Modules[jj].input_parameters:
        print('......................................................................')
        print('Scanning for output parameters matching the input parameter:', ip)

        for module_scanned in np.arange(nmods):
            if any(x == ip for x in Modules[module_scanned].output_parameters):
                print(' + Input/output Match found in module: ', Modules[module_scanned].name)
                G.addEdge(module_scanned, jj, label=ip.replace('_', ' '))
                edge_labels[(module_scanned, jj)] = ip.replace('_', ' ')


# ======================================
# Topological Sorting
# ======================================

print("The Topological Sort Of The Graph Is: ")
DG = nx.DiGraph()
DG.add_edges_from(G.visual)
topsorted = list(nx.topological_sort(DG))
print(topsorted)


# ======================================
# Monte Carlo Simulation
# ======================================

N_iter = int(config['Sampling']['Niterations'])

Suitability_Distribution = []
Temperature_Distribution = []
Pressure_Distribution = []
BondAlbedo_Distribution = []
GreenHouse_Distribution = []
Depth_Distribution = []
SavedParameters = []

N_probes = 100
Suitability_Plot = []
Variable = []

for keyparams.ProbeIndex in np.arange(float(NumProbes)):
    print('Probing location ', keyparams.ProbeIndex)

    for ii in np.arange(N_iter):
        keyparams.runid = ''
        for mi in np.arange(len(topsorted)):
            print('Executing ', Modules[topsorted[mi]].name)
            Modules[topsorted[mi]].execute()

        def _as_float(x, fallback=np.nan):
            try:
                if x is None:
                    return fallback
                xf = float(x)
                return xf
            except Exception:
                return fallback

        # If Suitability wasn’t set by the metabolism, create a very simple proxy
        _suit = keyparams.Suitability
        if _suit is None or (isinstance(_suit, float) and not np.isfinite(_suit)):
            T = _as_float(keyparams.Temperature, np.nan)
            # toy proxy: favor temps near 273 K
            _suit = 1.0 - min(1.0, abs(T - 273.15) / 200.0) if np.isfinite(T) else np.nan

        Suitability_Distribution.append(_as_float(_suit, np.nan))
        Temperature_Distribution.append(_as_float(keyparams.Temperature, np.nan))
        BondAlbedo_Distribution.append(_as_float(keyparams.Bond_Albedo, np.nan))
        GreenHouse_Distribution.append(_as_float(keyparams.GreenhouseWarming, np.nan))
        Pressure_Distribution.append(_as_float(keyparams.Pressure, np.nan))
        Depth_Distribution.append(_as_float(keyparams.Depth, np.nan))


        runid = keyparams.runid

    print('Monte Carlo loop completed')
    print('Runid: ' + keyparams.runid)

    This_Suitability = np.mean(Suitability_Distribution)
    print('Average Suitability %.2f' % This_Suitability)

    Suitability_Plot.append(This_Suitability)
    Variable.append(keyparams.Depth)
    SavedParameters.append(keyparams)


# ======================================
# Visualize Graph
# ======================================

fig = plt.figure(figsize=(12.00, 8.00), dpi=300)
fig.set_facecolor(bkgcolor)
fig.set_edgecolor(selected_edgecolor)

ax = G.visualize()

# Add habitat logo
logo_path = os.path.join(os.path.dirname(__file__), HabitatLogo)
im = plt.imread(logo_path)
newax = fig.add_axes([0.75, 0.75, 0.10, 0.10], anchor='NE')
newax.set_axis_off()
newax.imshow(im)

figures_dir = os.path.join(os.path.dirname(__file__), "Figures")
os.makedirs("Figures", exist_ok=True)

fig.savefig(os.path.join(figures_dir, HabitatShortName + '_Connections.png'))
fig.savefig(os.path.join(figures_dir, HabitatShortName + '_Connections.svg'))
plt.show()

# ======================================
# Visualization of Results
# ======================================

VisualizationModule(
    screen, sf, Suitability_Distribution, Temperature_Distribution,
    BondAlbedo_Distribution, GreenHouse_Distribution, Pressure_Distribution,
    Depth_Distribution, keyparams.runid, Suitability_Plot, Variable, HabitatLogo
)
