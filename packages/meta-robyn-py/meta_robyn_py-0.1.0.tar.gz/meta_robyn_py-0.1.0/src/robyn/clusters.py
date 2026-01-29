
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
from robyn.utils import errors_scores

def robyn_clusters(output_collect, dep_var_type, cluster_by="hyperparameters", 
                   all_media=None, k="auto", wss_var=0.06, max_clusters=10, 
                   limit=1, weights=[1, 1, 1], seed=123, quiet=False, **kwargs):
    
    if all_media is None:
        # Assuming input_collect is part of output_collect?
        # R: if is.null(all_media) aux <- colnames(input$mediaVecCollect) ...
        # We can pass all_media explicitly or try to find it.
        pass
        
    # Prepare data for clustering
    # x: input$resultHypParam or xDecompAgg
    result_hyp_param = output_collect.get('resultHypParam')
    x_decomp_agg = output_collect.get('xDecompAgg')
    
    if cluster_by == "hyperparameters":
        data_source = result_hyp_param
        # Select hyperparameter columns
        # Filter columns that contain "thetas", "shapes", "scales", "alphas", "gammas"
        hyp_cols = [c for c in data_source.columns if any(x in c for x in ["thetas", "shapes", "scales", "alphas", "gammas"])]
        df_cluster = data_source[['solID'] + hyp_cols].copy()
    else:
        # Performance clustering
        # Pivot xDecompAgg?
        # ROI or CPA
        pass # Implement if needed
        
    # Normalize data for K-Means?
    # R usually does scale() or the `clusterKmeans` does it.
    # We should normalize.
    
    scaler = MinMaxScaler()
    df_numeric = df_cluster.drop('solID', axis=1)
    df_normalized = pd.DataFrame(scaler.fit_transform(df_numeric), columns=df_numeric.columns)
    
    # Auto K selection - Elbow method
    if k == "auto":
        wss = []
        possible_k = range(1, min(len(df_normalized), 30) + 1)
        
        for i in possible_k:
            kmeans = KMeans(n_clusters=i, random_state=seed, n_init=10)
            kmeans.fit(df_normalized)
            wss.append(kmeans.inertia_)
            
        # Analyze WSS to find Elbow
        # R logic: pareto = wss / wss[1], dif = lag(pareto) - pareto
        # filter(dif > wss_var) -> max n
        
        wss = np.array(wss)
        pareto = wss / wss[0]
        dif = -np.diff(pareto) # diff(pareto) is x[i+1] - x[i]. We want prev - curr.
        # lag(pareto) - pareto => pareto[i] - pareto[i+1]
        
        # indices where dif > wss_var
        valid_k_indices = np.where(dif > wss_var)[0]
        if len(valid_k_indices) > 0:
            best_k = valid_k_indices[-1] + 2 # +1 for index, +1 because diff reduces length
            # Wait, index 0 in dif corresponds to k=1 vs k=2.
            # If dif[0] > wss_var, it means moving from 1 to 2 is significant.
            # Python index 0 -> k=2.
            best_k = valid_k_indices[-1] + 1 + 1 
        else:
            best_k = 1 # or min_clusters
            
        # min_clusters check
        min_clusters = 3
        if best_k < min_clusters:
            best_k = min_clusters
        if best_k > max_clusters:
            best_k = max_clusters
            
        k = best_k
        if not quiet:
            print(f">> Auto selected k = {k} (clusters)")
            
    # Final KMeans
    kmeans = KMeans(n_clusters=k, random_state=seed, n_init=10)
    labels = kmeans.fit_predict(df_normalized)
    
    df_cluster['cluster'] = labels + 1 # 1-based index
    
    # Merge back
    result_hyp_param = pd.merge(result_hyp_param, df_cluster[['solID', 'cluster']], on='solID', how='left')
    
    # Top solutions per cluster
    # Calculate error scores
    # .clusters_df
    
    result_hyp_param['error_score'] = errors_scores(result_hyp_param, balance=weights)
    
    top_sols = result_hyp_param.sort_values('error_score').groupby('cluster').head(limit)
    
    output_collect['resultHypParam'] = result_hyp_param
    output_collect['clusters'] = {
        'data': df_cluster,
        'n_clusters': k,
        'models': top_sols
    }
    
    return output_collect

