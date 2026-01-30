from .plot_function_umap import plot_umap 
from .plot_function_umap import def_plot_umap
from .plot_function_umap import ACTION_SCHEMA_UMAP
from .plot_function_umap import UMAPEmbedConfig, UMAPPlotConfig

from .plot_function_stackedbar import plot_celltype_population
from .plot_function_stackedbar import def_plot_celltype_population
from .plot_function_stackedbar import ACTION_SCHEMA_POPULATION
from .plot_function_stackedbar import PopulationComputeConfig, PopulationPlotConfig

from .plot_function_deg import plot_degs
from .plot_function_deg import def_plot_degs
from .plot_function_deg import ACTION_SCHEMA_DEG
from .plot_function_deg import DEGComputeConfig, DEGPlotConfig

from .plot_function_gsea import plot_gsea_go
from .plot_function_gsea import def_plot_gsea_go
from .plot_function_gsea import ACTION_SCHEMA_GSA
from .plot_function_gsea import GSAComputeConfig, GSABarPlotConfig, GSADotPlotConfig

from .plot_function_ccidot import plot_cci_dots
from .plot_function_ccidot import def_plot_cci_dots
from .plot_function_ccidot import ACTION_SCHEMA_CCI
from .plot_function_ccidot import CCIComputeConfig, CCIDotPlotConfig

from .plot_function_cnv_heatmap import plot_cnv_heatmap
from .plot_function_cnv_heatmap import def_plot_cnv_heatmap
from .plot_function_cnv_heatmap import ACTION_SCHEMA_CNV
from .plot_function_cnv_heatmap import CNVComputeConfig, CNVHeatmapStyle, CNVDataKeys

from .plot_function_marker import plot_markers_and_expression_dot
from .plot_function_marker import def_plot_markers_and_expression_dot
from .plot_function_marker import ACTION_SCHEMA_MARKER
from .plot_function_marker import MarkerFindConfig, MarkerPlotConfig

from .plot_function_violin import plot_violin_for_gene_expression_with_signif_difference
from .plot_function_violin import def_plot_violin_for_gene_expression_with_signif_difference
from .plot_function_violin import ACTION_SCHEMA_VIOLIN
from .plot_function_violin import SignifTestConfig, GeneSelectConfig, ViolinPlotStyle

from .plot_function_box import plot_box_for_celltype_population_with_signif_difference
from .plot_function_box import plot_box_for_cci_with_signif_difference
from .plot_function_box import plot_box_for_gene_expression_with_signif_difference
from .plot_function_box import def_plot_box
from .plot_function_box import ACTION_SCHEMA_BOX_GENE
from .plot_function_box import ACTION_SCHEMA_BOX_CCI
from .plot_function_box import ACTION_SCHEMA_BOX_POPULATION
from .plot_function_box import ObsFilter, SignifTestConfig, FeatureSelectConfig, BoxPlotStyle


Config_Name_to_Class_map = {
    'plot_umap': {
        'UMAPEmbedConfig': UMAPEmbedConfig, 
        'UMAPPlotConfig': UMAPPlotConfig
    },
    'plot_celltype_population': {
        'PopulationComputeConfig': PopulationComputeConfig,
        'PopulationPlotConfig': PopulationPlotConfig
    },
    'plot_degs': {
        'DEGComputeConfig': DEGComputeConfig, 
        'DEGPlotConfig': DEGPlotConfig
    },
    'plot_gsea_go': {
        'GSAComputeConfig': GSAComputeConfig,
        'GSABarPlotConfig': GSABarPlotConfig,
        'GSADotPlotConfig': GSADotPlotConfig
    },
    'plot_cci_dots': {
        'CCIComputeConfig': CCIComputeConfig,
        'CCIDotPlotConfig': CCIDotPlotConfig
    },
    'plot_cnv_heatmap': {
        'CNVComputeConfig': CNVComputeConfig,
        'CNVHeatmapStyle': CNVHeatmapStyle,
        'CNVDataKeys': CNVDataKeys
    },
    'plot_markers_and_expression_dot': {
        'MarkerFindConfig': MarkerFindConfig,
        'MarkerPlotConfig': MarkerPlotConfig
    },
    'plot_violin_for_gene_expression_with_signif_difference': {
        'SignifTestConfig': SignifTestConfig,
        'GeneSelectConfig': GeneSelectConfig,
        'ViolinPlotStyle': ViolinPlotStyle
    },
    'plot_box_for_gene_expression_with_signif_difference': {
        'SignifTestConfig': SignifTestConfig,
        'FeatureSelectConfig': FeatureSelectConfig,
        'BoxPlotStyle': BoxPlotStyle
    },
    'plot_box_for_cci_with_signif_difference': {
        'SignifTestConfig': SignifTestConfig,
        'FeatureSelectConfig': FeatureSelectConfig,
        'BoxPlotStyle': BoxPlotStyle
    },
    'plot_box_for_celltype_population_with_signif_difference': {
        'SignifTestConfig': SignifTestConfig,
        'FeatureSelectConfig': FeatureSelectConfig,
        'BoxPlotStyle': BoxPlotStyle
    }
}

Tool_config_map = {
    'plot_umap': {
        'embed_cfg': UMAPEmbedConfig, 
        'plot_cfg': UMAPPlotConfig
    },
    'plot_celltype_population': {
        'compute_cfg': PopulationComputeConfig,
        'plot_cfg': PopulationPlotConfig
    },
    'plot_degs': {
        'compute_cfg': DEGComputeConfig, 
        'plot_cfg': DEGPlotConfig
    },
    'plot_gsea_go': {
        'compute_cfg': GSAComputeConfig,
        'bar_cfg': GSABarPlotConfig,
        'dot_cfg': GSADotPlotConfig
    },
    'plot_cci_dots': {
        'compute_cfg': CCIComputeConfig,
        'dot_cfg': CCIDotPlotConfig
    },
    'plot_cnv_heatmap': {
        'compute_cfg': CNVComputeConfig,
        'style': CNVHeatmapStyle,
        'keys': CNVDataKeys
    },
    'plot_markers_and_expression_dot': {
        'find_cfg': MarkerFindConfig,
        'plot_cfg': MarkerPlotConfig
    },
    'plot_violin_for_gene_expression_with_signif_difference': {
        'test_cfg': SignifTestConfig,
        'select_cfg': GeneSelectConfig,
        'style': ViolinPlotStyle
    },
    'plot_box_for_gene_expression_with_signif_difference': {
        'test_cfg': SignifTestConfig,
        'select_cfg': FeatureSelectConfig,
        'style': BoxPlotStyle
    },
    'plot_box_for_cci_with_signif_difference': {
        'test_cfg': SignifTestConfig,
        'select_cfg': FeatureSelectConfig,
        'style': BoxPlotStyle
    },
    'plot_box_for_celltype_population_with_signif_difference': {
        'test_cfg': SignifTestConfig,
        'select_cfg': FeatureSelectConfig,
        'style': BoxPlotStyle
    }
}


TOOL_FUNCS = {
    "plot_umap": plot_umap,
    "plot_celltype_population": plot_celltype_population,
    "plot_degs": plot_degs,
    "plot_gsea_go": plot_gsea_go,
    "plot_cci_dots": plot_cci_dots,
    "plot_cnv_heatmap": plot_cnv_heatmap,
    "plot_markers_and_expression_dot": plot_markers_and_expression_dot,
    "plot_violin_for_gene_expression_with_signif_difference": plot_violin_for_gene_expression_with_signif_difference,
    "plot_box_for_gene_expression_with_signif_difference": plot_box_for_gene_expression_with_signif_difference,
    "plot_box_for_cci_with_signif_difference": plot_box_for_cci_with_signif_difference,
    "plot_box_for_celltype_population_with_signif_difference": plot_box_for_celltype_population_with_signif_difference
}

# 1. 모든 스키마를 딕셔너리로 관리
SCHEMA_REGISTRY = {
    "plot_umap": ACTION_SCHEMA_UMAP,
    "plot_celltype_population": ACTION_SCHEMA_POPULATION,
    "plot_degs": ACTION_SCHEMA_DEG,
    "plot_gsea_go": ACTION_SCHEMA_GSA,
    "plot_cci_dots": ACTION_SCHEMA_CCI,
    "plot_cnv_heatmap": ACTION_SCHEMA_CNV,
    "plot_markers_and_expression_dot": ACTION_SCHEMA_MARKER,
    "plot_violin_for_gene_expression_with_signif_difference": ACTION_SCHEMA_VIOLIN,
    "plot_box_for_gene_expression_with_signif_difference": ACTION_SCHEMA_BOX_GENE,
    "plot_box_for_cci_with_signif_difference": ACTION_SCHEMA_BOX_CCI,
    "plot_box_for_celltype_population_with_signif_difference": ACTION_SCHEMA_BOX_POPULATION
}

# 1. 모든 스키마를 딕셔너리로 관리
FUNCTION_DEF_REGISTRY = {
    "plot_umap": def_plot_umap,
    "plot_celltype_population": def_plot_celltype_population,
    "plot_degs": def_plot_degs,
    "plot_gsea_go": def_plot_gsea_go,
    "plot_cci_dots": def_plot_cci_dots,
    "plot_cnv_heatmap": def_plot_cnv_heatmap,
    "plot_markers_and_expression_dot": def_plot_markers_and_expression_dot,
    "plot_violin_for_gene_expression_with_signif_difference": def_plot_violin_for_gene_expression_with_signif_difference,
    "plot_box_for_gene_expression_with_signif_difference": def_plot_box,
    "plot_box_for_cci_with_signif_difference": def_plot_box,
    "plot_box_for_celltype_population_with_signif_difference": def_plot_box
}


def get_def_strings_from_global_variables():
    ss = ''
    ss = ss + '### UMAP visualization: \n' + def_plot_umap + '\n\n'
    ss = ss + '### Barplot for cell population: \n' + def_plot_celltype_population + '\n\n'
    ss = ss + '### Barplot for DEG: \n' + def_plot_degs + '\n\n'
    ss = ss + '### Dotplot or Barplot for GSEA/GSA(GO): \n' + def_plot_gsea_go + '\n\n'
    ss = ss + '### Dotplot for CCI: \n' + def_plot_cci_dots + '\n\n'
    ss = ss + '### CNV heatmap: \n' + def_plot_cnv_heatmap + '\n\n'
    ss = ss + '### Dotplot for marker/gene expression: \n' + def_plot_markers_and_expression_dot + '\n\n'
    ss = ss + '### Violinplots: \n' + def_plot_violin_for_gene_expression_with_signif_difference + '\n\n'
    ss = ss + '### Boxplots (3 types): \n' + def_plot_box
    # print(ss)
    return ss

def get_config_names_used( ss ):
    
    flag = False
    ss_sel = []
    for line in ss.split('\n'):
        if flag == True:
            ss_sel.append(line.split(' ')[-1][:-1])
            flag = False
        if line.startswith('@dataclass'):
            flag = True
    
    ss_sel = list(set(ss_sel))
    return ss_sel

def get_config_tool_map(ss, verbose = False):
    
    flag = False
    ss_sel = []
    for line in ss.split('\n'):
        if flag == True:
            ss_sel.append(line.split(' ')[-1][:-1])
            flag = False
        if line.startswith('@dataclass'):
            flag = True
    
    ss_sel = list(set(ss_sel))
    if verbose: display(ss_sel)
    
    flag = False
    # mapping = dict( zip( ss_sel, [None]*len(ss_sel)) )
    # covered = dict( zip( ss_sel, [[]]*len(ss_sel)) )
    current_tool = None
    Tool_config_map = {}
    
    for line in ss.split('\n'):
        if line.startswith('def plot_'):
            current_tool = line.split(' ')[1].split('(')[0]
            if verbose: print( current_tool )
            Tool_config_map[current_tool] = {}
            
        for s in ss_sel:
            if f': Optional[{s}] = None' in line:
                vname = line.split(':')[0].strip()
                # covered[s].append(vname)
                # mapping[s] = vname
                if verbose: print(f'{line} -> {s}, {vname}')
                Tool_config_map[current_tool][vname] = Config_Name_to_Class_map[current_tool][s]
                break
                
    return Tool_config_map

### Run example
ss = get_def_strings_from_global_variables()
# Tool_config_map = get_config_tool_map(ss, verbose = False )
# display(Tool_config_map)

