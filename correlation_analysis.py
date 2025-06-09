import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
import numpy as np
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
ANALYSIS_COLUMNS = [
    "Total Score",
    "population",
    "median_income",
    "aggregate_income",
    "high_school_grads",
    "bachelors_grads",
    "Assessed Valuation",
    "Employees",
    "Expenditures",
    "Revenues",
    "Indebtedness",
    "per_capita_income"
]

def convert_to_numeric(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Convert specified columns to numeric type, handling any conversion errors.
    
    Args:
        df (pd.DataFrame): Input dataframe
        columns (list): List of columns to convert
        
    Returns:
        pd.DataFrame: DataFrame with converted columns
    """
    df = df.copy()
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def setup_analysis_directories(base_folder: str) -> tuple:
    """
    Create necessary directories for analysis results.
    
    Args:
        base_folder (str): Base folder path for analysis
        
    Returns:
        tuple: Paths to analysis and clustering directories
    """
    analysis_dir = Path(base_folder) / "analysis"
    clustering_dir = analysis_dir / "clustering_analysis"
    
    # Create directories if they don't exist
    analysis_dir.mkdir(parents=True, exist_ok=True)
    clustering_dir.mkdir(parents=True, exist_ok=True)
    
    return analysis_dir, clustering_dir

def cluster_and_plot_boxplot(df: pd.DataFrame, id_col: str, num_cols: list, n_clusters: int, 
                           output_dir: Path) -> pd.DataFrame:
    """
    Perform clustering analysis and create boxplots for specified numeric columns.
    
    Args:
        df (pd.DataFrame): Input dataframe
        id_col (str): Identifier column name
        num_cols (list): List of numeric columns to analyze
        n_clusters (int): Number of clusters for KMeans
        output_dir (Path): Directory to save plots
        
    Returns:
        pd.DataFrame: DataFrame with added cluster columns
    """
    df = df.copy()
    
    # Convert all numeric columns at once
    df = convert_to_numeric(df, num_cols)
    
    for col in num_cols:
        try:
            # Drop NaNs for the current column
            valid_df = df.dropna(subset=[col])
            
            # Reshape and cluster
            X = valid_df[[col]].values
            kmeans = KMeans(n_clusters=n_clusters, random_state=0)
            cluster_labels = kmeans.fit_predict(X)
            
            # Map clusters to ordered labels and convert to integers
            cluster_means = pd.Series(X.flatten()).groupby(cluster_labels).mean()
            ordered_labels = cluster_means.sort_values().index
            label_mapping = {old: int(new) for new, old in enumerate(ordered_labels)}
            ordered_cluster_labels = np.array([label_mapping[label] for label in cluster_labels], dtype=int)
            
            # Assign cluster column
            cluster_col = f"{col}_cluster"
            df.loc[valid_df.index, cluster_col] = ordered_cluster_labels
            
            # Create plot dataframe with explicit type conversion
            plot_df = pd.DataFrame({
                'cluster': ordered_cluster_labels,
                'value': valid_df[col].values
            })
            
            # Plot and save boxplot
            plt.figure(figsize=(8, 6))
            sns.boxplot(x='cluster', y='value', data=plot_df)
            plt.title(f'Boxplot of {col} by {cluster_col}')
            plt.xlabel('Cluster (Ordered by Scale)')
            plt.ylabel(col)
            
            # Save plot
            plot_path = output_dir / f"{col}_cluster_boxplot.png"
            plt.savefig(plot_path)
            plt.close()
            
            logging.info(f"Created cluster analysis for {col}")
            
        except Exception as e:
            logging.error(f"Error processing column {col}: {str(e)}")
            continue
    
    return df

def create_normalized_boxplot(df: pd.DataFrame, num_cols: list, output_dir: Path, 
                            plot_size: tuple = (10, 6)) -> None:
    """
    Create normalized boxplots for selected columns.
    
    Args:
        df (pd.DataFrame): Input dataframe
        num_cols (list): List of numeric columns to analyze
        output_dir (Path): Directory to save plots
        plot_size (tuple): Figure size for the plot
    """
    try:
        # Ensure all columns are numeric
        df = convert_to_numeric(df, num_cols)
        df = df.dropna(subset=num_cols)
        
        # Normalize columns to range [0, 1]
        df_normalized = (df[num_cols] - df[num_cols].min()) / (df[num_cols].max() - df[num_cols].min())
        
        # Plot
        plt.figure(figsize=plot_size)
        df_normalized.boxplot()
        plt.title('Normalized Boxplots of Selected Columns')
        plt.xlabel('Columns')
        plt.ylabel('Normalized Values (0 to 1)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save plot
        plot_path = output_dir / "normalized_boxplots.png"
        plt.savefig(plot_path)
        plt.close()
        
        logging.info("Created normalized boxplots")
        
    except Exception as e:
        logging.error(f"Error creating normalized boxplots: {str(e)}")

def analyze_cluster_score_distribution(df: pd.DataFrame, output_dir: Path) -> None:
    """
    Analyze and visualize Total Score distribution across different clusters.
    
    Args:
        df (pd.DataFrame): Input dataframe with cluster columns
        output_dir (Path): Directory to save plots
    """
    try:
        # Get cluster columns
        cluster_columns = [col for col in df.columns if col.endswith('_cluster') and col != 'Total Score_cluster']
        
        # Create subplots for each cluster
        plt.figure(figsize=(20, 20))
        for i, cluster_col in enumerate(cluster_columns):
            plt.subplot(6, 2, i + 1)
            
            # Clean data for this cluster
            valid_data = df[[cluster_col, 'Total Score']].copy()
            valid_data = valid_data.dropna()
            
            # Convert to proper types and handle any remaining invalid values
            valid_data[cluster_col] = pd.to_numeric(valid_data[cluster_col], errors='coerce')
            valid_data['Total Score'] = pd.to_numeric(valid_data['Total Score'], errors='coerce')
            
            # Remove any infinite values
            valid_data = valid_data.replace([np.inf, -np.inf], np.nan).dropna()
            
            # Create plot dataframe with explicit type conversion
            plot_df = pd.DataFrame({
                'cluster': valid_data[cluster_col].astype(int),
                'score': valid_data['Total Score'].astype(float)
            })
            
            # Only plot if we have valid data
            if len(plot_df) > 0:
                sns.boxplot(x='cluster', y='score', data=plot_df)
                plt.title(f'Total Score by {cluster_col.replace("_cluster", "")} Cluster')
                plt.xlabel('Cluster')
                plt.ylabel('Total Score')
            else:
                plt.text(0.5, 0.5, 'No valid data for this cluster', 
                        horizontalalignment='center', verticalalignment='center')
                plt.title(f'No Data Available for {cluster_col.replace("_cluster", "")}')
        
        plt.tight_layout()
        
        # Save plot
        plot_path = output_dir / "total_score_variation_across_clusters.png"
        plt.savefig(plot_path)
        plt.close()
        
        logging.info("Created cluster score distribution analysis")
        
    except Exception as e:
        logging.error(f"Error analyzing cluster score distribution: {str(e)}")
        # Create an error plot to indicate the failure
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, f'Error creating cluster analysis: {str(e)}', 
                horizontalalignment='center', verticalalignment='center')
        plt.title('Error in Cluster Analysis')
        error_plot_path = output_dir / "cluster_analysis_error.png"
        plt.savefig(error_plot_path)
        plt.close()

def analyze_cluster_components(df: pd.DataFrame, cluster_column: str, output_dir: Path) -> None:
    """
    Create detailed analysis of sustainability components for each cluster of a given column.
    
    Args:
        df (pd.DataFrame): Input dataframe with cluster columns
        cluster_column (str): Column name to analyze clusters for
        output_dir (Path): Base directory for output
    """
    try:
        # Define max scores for normalization
        max_scores = {
            'Stakeholder & Community Engagement': 6,
            'GHG Emissions Inventory': 3,
            'Climate Change Risk Assessment (CCRA)': 7,
            'City Needs Assessment': 2,
            'Strategy Identification': 9,
            'Action Prioritization & Detailing': 5,
            'Equity & Inclusivity': 6,
            'Monitoring, Evaluation & Reporting (MER)': 6
        }
        
        # Create specific directory for this analysis
        analysis_dir = output_dir / f"{cluster_column}_analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # Get unique cluster numbers
        cluster_col = f"{cluster_column}_cluster"
        if cluster_col not in df.columns:
            logging.error(f"Cluster column {cluster_col} not found in dataframe")
            return
            
        unique_clusters = sorted(df[cluster_col].unique())
        
        # Format currency function
        def format_currency(val):
            if val >= 1_000_000:
                return f"${val/1_000_000:.1f}M"
            elif val >= 1_000:
                return f"${val/1_000:.1f}K"
            return f"${val}"
        
        # Process each cluster
        for cluster_num in unique_clusters:
            try:
                # Filter for current cluster
                df_cluster = df[df[cluster_col] == cluster_num].copy()
                
                # Get range for this cluster
                val_min = df_cluster[cluster_column].min()
                val_max = df_cluster[cluster_column].max()
                range_str = f"{cluster_column} Cluster {cluster_num} Range: {format_currency(val_min)} – {format_currency(val_max)}"
                
                # Normalize the scores
                component_cols = list(max_scores.keys())
                for col in component_cols:
                    if col in df_cluster.columns:
                        df_cluster[col] = df_cluster[col] / max_scores[col]
                
                # Sort by Total Score
                df_cluster = df_cluster.sort_values(by='Total Score', ascending=False)
                
                # Prepare data for plotting
                communities = df_cluster[['city', 'Total Score', 'Total Score_cluster', cluster_column] + component_cols]
                
                # Calculate subplot layout
                n = len(communities)
                cols = 3
                rows = (n + cols - 1) // cols
                
                # Create figure
                fig, axes = plt.subplots(rows, cols, figsize=(25, 6 * rows))
                axes = axes.flatten()
                
                # Plot each community
                for i, (_, row) in enumerate(communities.iterrows()):
                    ax = axes[i]
                    ax.bar(component_cols, row[component_cols])
                    ax.set_ylim(0, 1)
                    
                    # Format value for display
                    val = row[cluster_column]
                    val_str = f"{val:,.0f}"
                    
                    # Set title with community info
                    ax.set_title(
                        f"{row['city']}\nScore: {int(row['Total Score'])}, "
                        f"Cluster: {int(row['Total Score_cluster'])}, "
                        f"{cluster_column}: {val_str}",
                        fontsize=14
                    )
                    ax.tick_params(axis='x', rotation=75, labelsize=14)
                    ax.tick_params(axis='y', labelsize=14)
                    ax.set_ylabel('Normalized Score')
                
                # Hide unused subplots
                for j in range(i + 1, len(axes)):
                    axes[j].axis('off')
                
                plt.tight_layout()
                plt.suptitle(
                    f"Normalized Sustainability Component Scores ({cluster_column} Cluster {cluster_num})\n{range_str}",
                    fontsize=16, y=1.05
                )
                
                # Save plot
                plot_path = analysis_dir / f"normalized_scores_cluster_{cluster_num}.png"
                plt.savefig(plot_path, bbox_inches='tight')
                plt.close()
                
                logging.info(f"Created detailed analysis for {cluster_column} cluster {cluster_num}")
                
            except Exception as e:
                logging.error(f"Error processing cluster {cluster_num} for {cluster_column}: {str(e)}")
                continue
                
    except Exception as e:
        logging.error(f"Error in cluster component analysis: {str(e)}")

def main(input_file: str, base_folder: str, n_clusters: int = 3):
    """
    Main function to orchestrate the analysis.
    
    Args:
        input_file (str): Path to input CSV file
        base_folder (str): Base folder for analysis results
        n_clusters (int): Number of clusters for KMeans analysis
    """
    try:
        # Setup directories
        analysis_dir, clustering_dir = setup_analysis_directories(base_folder)
        logging.info(f"Analysis directories created at {analysis_dir}")
        
        # Read data and convert numeric columns
        df = pd.read_csv(input_file)
        df = convert_to_numeric(df, ANALYSIS_COLUMNS)
        logging.info(f"Data loaded from {input_file}")
        
        # Perform clustering analysis
        df_with_clusters = cluster_and_plot_boxplot(
            df, 
            'city', 
            ANALYSIS_COLUMNS, 
            n_clusters,
            clustering_dir
        )
        
        # Create normalized boxplots
        create_normalized_boxplot(df_with_clusters, ANALYSIS_COLUMNS, clustering_dir)
        
        # Analyze cluster score distribution
        analyze_cluster_score_distribution(df_with_clusters, clustering_dir)
        
        # Perform detailed component analysis for each column
        for column in ['Employees', 'Revenues']:
            if f"{column}_cluster" in df_with_clusters.columns:
                analyze_cluster_components(df_with_clusters, column, clustering_dir)
        
        # Save processed data
        output_file = clustering_dir / "processed_data_with_clusters.csv"
        df_with_clusters.to_csv(output_file, index=False)
        logging.info(f"Processed data saved to {output_file}")
        
    except Exception as e:
        logging.error(f"Error in main analysis: {str(e)}")

if __name__ == "__main__":
    # Note that data final is the data after getting sustainability scores and demographics information. 
    # I just used older file here but you need to generate the data final file.
    # The parameters that need changing are in the main function.
    input_file = "sustainable_maturity_mapping/data_final.csv"  # Update this path as needed
    base_folder = "sustainable_maturity_mapping"
    main(input_file, base_folder, n_clusters=5)




