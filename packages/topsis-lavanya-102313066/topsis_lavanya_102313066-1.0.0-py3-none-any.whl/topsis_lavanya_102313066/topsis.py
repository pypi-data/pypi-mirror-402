#!/usr/bin/env python3
"""
TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) Implementation
Author: Lavanya Garg (Roll: 102313066)
Institution: Thapar Institute of Engineering and Technology
"""

import sys
import pandas as pd
import numpy as np


def validate_inputs(df, weights, impacts):
    """
    Validate input parameters for TOPSIS analysis.
    
    Args:
        df (pd.DataFrame): Input data with first column as identifiers
        weights (list): List of weights
        impacts (list): List of impacts (+ or -)
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(df.columns) < 2:
        return False, "Error: Input data must have at least 2 columns"
    
    try:
        pd.to_numeric(df.iloc[:, 0])
        return False, "Error: First column must contain non-numeric identifiers"
    except (ValueError, TypeError):
        pass
    
    num_criteria = len(df.columns) - 1
    
    if len(weights) != num_criteria:
        return False, f"Error: Number of weights must match criteria count"
    
    if any(w <= 0 for w in weights):
        return False, "Error: All weights must be positive"
    
    if len(impacts) != num_criteria:
        return False, f"Error: Number of impacts must match criteria count"
    
    if not all(impact in ['+', '-'] for impact in impacts):
        return False, "Error: Impacts must be '+' or '-'"
    
    criteria_data = df.iloc[:, 1:]
    try:
        numeric_df = criteria_data.apply(pd.to_numeric, errors='raise')
    except (ValueError, TypeError):
        return False, "Error: All criteria must be numeric"
    
    if (numeric_df <= 0).any().any():
        return False, "Error: All values must be positive"
    
    return True, "OK"


def normalize_matrix(df):
    """Normalize using vector normalization."""
    matrix = df.values.astype(float)
    norms = np.sqrt((matrix ** 2).sum(axis=0))
    normalized = matrix / norms
    return normalized


def apply_weights(normalized_matrix, weights):
    """Apply weights to normalized matrix."""
    return normalized_matrix * np.array(weights)


def find_ideal_solutions(weighted_matrix, impacts):
    """Find ideal and anti-ideal solutions."""
    ideal = np.zeros(weighted_matrix.shape[1])
    anti_ideal = np.zeros(weighted_matrix.shape[1])
    
    for j in range(weighted_matrix.shape[1]):
        if impacts[j] == '+':
            ideal[j] = weighted_matrix[:, j].max()
            anti_ideal[j] = weighted_matrix[:, j].min()
        else:
            ideal[j] = weighted_matrix[:, j].min()
            anti_ideal[j] = weighted_matrix[:, j].max()
    
    return ideal, anti_ideal


def calculate_separations(weighted_matrix, ideal, anti_ideal):
    """Calculate separation measures."""
    s_plus = np.sqrt(((weighted_matrix - ideal) ** 2).sum(axis=1))
    s_minus = np.sqrt(((weighted_matrix - anti_ideal) ** 2).sum(axis=1))
    return s_plus, s_minus


def calculate_scores(s_plus, s_minus):
    """Calculate TOPSIS scores and ranks."""
    with np.errstate(divide='ignore', invalid='ignore'):
        scores = np.where(s_plus + s_minus != 0, s_minus / (s_plus + s_minus), 0)
    
    ranks = pd.Series(scores).rank(method='min', ascending=False).astype(int).values
    return scores, ranks


def topsis(input_file, weights, impacts, output_file=None):
    """
    Execute complete TOPSIS analysis.
    
    Args:
        input_file (str): Path to input CSV file
        weights (list or str): Weights
        impacts (list or str): Impacts
        output_file (str): Optional output file
    
    Returns:
        pd.DataFrame: Results with scores and ranks
    """
    if isinstance(weights, str):
        weights = list(map(float, weights.split(',')))
    if isinstance(impacts, str):
        impacts = [i.strip() for i in impacts.split(',')]
    
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    is_valid, message = validate_inputs(df, weights, impacts)
    if not is_valid:
        print(message)
        sys.exit(1)
    
    criteria = df.iloc[:, 1:]
    
    normalized = normalize_matrix(criteria)
    weighted = apply_weights(normalized, weights)
    ideal, anti_ideal = find_ideal_solutions(weighted, impacts)
    s_plus, s_minus = calculate_separations(weighted, ideal, anti_ideal)
    scores, ranks = calculate_scores(s_plus, s_minus)
    
    result_df = df.copy()
    result_df['Topsis Score'] = scores
    result_df['Rank'] = ranks
    result_df = result_df.sort_values('Rank')
    
    if output_file:
        result_df.to_csv(output_file, index=False)
        print(f"Results saved to '{output_file}'")
    
    return result_df
