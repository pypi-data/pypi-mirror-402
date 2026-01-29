
import os
import json
import pandas as pd
from robyn.pareto import robyn_pareto
from robyn.clusters import robyn_clusters

def robyn_outputs(input_collect, output_models, pareto_fronts="auto", 
                  calibration_constraint=0.1, plot_folder=None, 
                  plot_folder_sub=None, export=True, clusters=True, 
                  select_model="clusters", csv_out="pareto", 
                  quiet=False, ui=False, **kwargs):
    
    if not quiet:
        print(">>> Calculating Pareto Method...")
        
    output_collect = robyn_pareto(
        input_collect=input_collect,
        output_models=output_models,
        pareto_fronts=pareto_fronts,
        calibration_constraint=calibration_constraint,
        quiet=quiet
    )
    
    if clusters:
        if not quiet:
            print(">>> Calculating Clusters...")
        
        output_collect = robyn_clusters(
            output_collect=output_collect,
            dep_var_type=input_collect['dep_var_type'],
            all_media=input_collect['all_media'],
            quiet=quiet,
            **kwargs
        )
        
    if export:
        # Determine paths
        # R uses plot_folder/plot_folder_sub
        if plot_folder is None:
             plot_folder = os.getcwd()
             
        if plot_folder_sub:
             output_path = os.path.join(plot_folder, plot_folder_sub)
        else:
             output_path = plot_folder
             
        if not os.path.exists(output_path):
             os.makedirs(output_path)
             
        output_collect['plot_folder'] = output_path
        
        # Export CSVs
        if csv_out == "pareto" or csv_out == "all":
            if not quiet:
                print(f"Exporting results to {output_path}")
            
            # pareto_hyperparameters.csv
            hyp_param = output_collect.get('resultHypParam')
            if hyp_param is not None:
                hyp_param.to_csv(os.path.join(output_path, "pareto_hyperparameters.csv"), index=False)
                
            # pareto_aggregated.csv
            decomp_agg = output_collect.get('xDecompAgg')
            if decomp_agg is not None:
                decomp_agg.to_csv(os.path.join(output_path, "pareto_aggregated.csv"), index=False)
                
        # Export JSON
        # robyn_write(output_collect)
        # For now a simple json dump of scalar/list info metadata?
        # Serializing DataFrames to JSON might be heavy, often people save CSVs + dict metadata.
        # R saves Robyn.RDS.
         
    return output_collect
