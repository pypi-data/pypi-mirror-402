import numpy as np
from collections import OrderedDict, defaultdict, Counter
import itertools
from itertools import combinations, islice, product
from typing import List, Dict, Tuple, Set, Union, Iterable, Any
import random
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.stats import qmc
from copy import deepcopy
from math import lcm, comb, log2, log
from decimal import Decimal
from multiprocessing import Pool, cpu_count
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import
import re

#import ipympl

VERBOSE = True

class TPM:
    def __init__(
        self,
        init_TPM: np.ndarray, # the TPM that was used to initalize this object
        missing_rows: set,
        input_info: list,
        output_info: dict,
        pattern_to_idx: dict,
        idx_to_pattern: dict
    ):
        self.RN_TPM = init_TPM.copy()
        
        self.MN_TPM = None  # matrix normalized

        self.missing_rows = set(missing_rows)
        
        self.input_info = input_info
        self.output_info = output_info
        
        self.pattern_to_idx = pattern_to_idx
        self.idx_to_pattern = idx_to_pattern
       
        self.n_rows = self.RN_TPM.shape[0]
        self.n_columns = self.RN_TPM.shape[1]

        self.row_overrides = {}

        self._precompute_marginalization_maps() # precalculate lookups used during FID calculations

        self.refresh_TPMs()


    @classmethod
    def from_data(cls, data, input_names=None, output_name='Y'):
        """
        Build TPM from input/output sequences (output last).
        Inputs can be strings, numbers, or mixed types.
        Each sequence must be the same length.
        """
        if len(data) < 2:
            raise ValueError("Data must have at least 1 input and 1 output.")

        inputs = data[:-1]
        output = data[-1]
        n_samples = len(output)

        if not all(len(var) == n_samples for var in inputs):
            raise ValueError("All inputs must match output length.")

        n_inputs = len(inputs)

        # Input names
        if input_names is None:
            input_names = [f'X{i}' for i in range(n_inputs)]
        if len(input_names) != n_inputs:
            raise ValueError("input_names must match number of inputs.")

        input_info = []
        for i, var_data in enumerate(inputs):
            observed_vals = list(OrderedDict.fromkeys(var_data))
            mapping = {j: val for j, val in enumerate(observed_vals)}
            reverse_mapping = {val: j for j, val in mapping.items()}
            series_data = [reverse_mapping[val] for val in var_data]

            input_info.append({
                'name': str(input_names[i]),
                'cardinality': len(observed_vals),
                'mapping': mapping,
                'reverse_mapping': reverse_mapping,
                'series_data': series_data
            })

        # Output
        observed_out = list(OrderedDict.fromkeys(output))
        output_mapping = {j: val for j, val in enumerate(observed_out)}
        output_reverse_mapping = {val: j for j, val in output_mapping.items()}
        output_series_data = [output_reverse_mapping[val] for val in output]

        output_info = {
            'name': str(output_name),
            'cardinality': len(observed_out),
            'mapping': output_mapping,
            'reverse_mapping': output_reverse_mapping,
            'series_data': output_series_data
        }

        # Build all patterns
        all_patterns = list(product(*[range(info['cardinality']) for info in input_info]))
        pattern_to_idx = {pattern: i for i, pattern in enumerate(all_patterns)}
        idx_to_pattern = {i: pattern for pattern, i in pattern_to_idx.items()}
        n_patterns = len(all_patterns)

        # Count observations
        counts = {}
        for i in range(n_samples):
            pattern = tuple(info['series_data'][i] for info in input_info)
            output_val = output_series_data[i]
            counts[(pattern, output_val)] = counts.get((pattern, output_val), 0) + 1

        RN_TPM = np.full((n_patterns, output_info['cardinality']), np.nan)
        
        missing_rows = set()
        for pattern, row_idx in pattern_to_idx.items():
            row_counts = [counts.get((pattern, out_idx), 0) for out_idx in range(output_info['cardinality'])]
            total = sum(row_counts)

            if total > 0:
                row_probs = [c / total for c in row_counts]
                RN_TPM[row_idx, :] = row_probs
            else:
                # Missing row
                missing_rows.add(row_idx)

        return cls(
            init_TPM=RN_TPM,
            missing_rows=missing_rows,
            input_info=input_info,
            output_info=output_info,
            pattern_to_idx=pattern_to_idx,
            idx_to_pattern=idx_to_pattern
        )

    
    def get_input_names(self):
        return [info['name'] for info in self.input_info]
        
    def get_input_symbols(self):
        input_symbols = {}
        for info in self.input_info:
            input_symbols[info['name']] = [info['mapping'][i] for i in range(info['cardinality'])]
        return input_symbols

    def get_output_symbols(self):
        return [self.output_info['mapping'][i] for i in range(self.output_info['cardinality'])]

    
    def refresh_TPMs(self):
    
        # Apply overrides to RN_TPM
        for row_idx, override in self.row_overrides.items():
            if override['type'] == 'prior':
                self.RN_TPM[row_idx, :] = 0.0  # Unspecified symbols get probability 0
                for idx2, val in override['values'].items():
                    self.RN_TPM[row_idx, idx2] = val
            elif override['type'] == 'restriction':
                # Fill restricted row with uniform distribution over allowed outputs
                allowed_indices = override['values']
                row = np.zeros(self.n_columns)
                row[allowed_indices] = 1.0 / len(allowed_indices)
                self.RN_TPM[row_idx, :] = row
                # Mark as complete (remove from missing_rows)
                if row_idx in self.missing_rows:
                    self.missing_rows.remove(row_idx)
    
        # Normalize each row in TPM (only complete rows, preserve NaN for missing rows)
        row_sums = np.nansum(self.RN_TPM, axis=1, keepdims=True)
        # Only normalize rows that have at least some data
        for row_idx in range(self.n_rows):
            if row_idx not in self.missing_rows:
                row_sum = row_sums[row_idx, 0]
                if row_sum > 0:
                    self.RN_TPM[row_idx, :] = self.RN_TPM[row_idx, :] / row_sum
    
        # Compute MN_TPM from RN_TPM (joint distribution)
        # MN_TPM[i,j] = P(X_i, Y_j) = P(Y_j|X_i) * P(X_i)
        # Assuming uniform P(X_i) = 1/n_rows for complete rows
        self.MN_TPM = self.RN_TPM.copy()
        for row_idx in range(self.n_rows):
            if row_idx not in self.missing_rows:
                self.MN_TPM[row_idx, :] = self.RN_TPM[row_idx, :] / self.n_rows
            else:
                # Keep missing rows as NaN in MN_TPM
                self.MN_TPM[row_idx, :] = np.nan


    def display(self):
        print(f"\nTPM Report")
        print("=" * 60)
        print(f"Inputs ({len(self.input_info)}): {', '.join(self.get_input_names())}")
        print(f"Output: {self.output_info['name']}")
        print(f"Number of input patterns: {self.n_rows}")
        print(f"Number of output symbols: {self.n_columns}")
        print(f"Missing rows: {len(self.missing_rows)}")
        print("=" * 60)

        pattern_width = 32
        col_width = 8

        output_symbols = [str(sym) for sym in self.get_output_symbols()]

        header_prefix = " " * (pattern_width-6) + "Y = "
        header_symbols = "".join([f"{sym:^{col_width}}" for sym in output_symbols])

        print(header_prefix + header_symbols)

        sorted_idx = sorted(
            self.idx_to_pattern.keys(),
            key=lambda idx: [
                self.input_info[i]['mapping'][val]
                for i, val in enumerate(self.idx_to_pattern[idx])
            ]
        )

        for idx in sorted_idx:
            pattern = self.idx_to_pattern[idx]
            pattern_symbols = [self.input_info[i]['mapping'][val] for i, val in enumerate(pattern)]
            pattern_str = f"({', '.join(map(str, pattern_symbols))})"

            row_values = self.RN_TPM[idx, :]

            if idx in self.row_overrides:
                override = self.row_overrides[idx]
                if override['type'] == 'restriction':
                    allowed_symbols = [self.output_info['mapping'][v] for v in override['values']]
                    row_status = f"MISSING (restricted to: {allowed_symbols})"
                
                elif override['type'] == 'prior':
                    row_values = np.zeros(self.n_columns)
                    for idx2, val in override['values'].items():
                        row_values[idx2] = val
                    probs = [f"{v:.3f}" for v in row_values]
                    row_status = "   ".join(probs) + "   <- set with prior"
                else:
                    row_status = "MISSING (override: unknown type)"

            elif idx in self.missing_rows or np.isnan(row_values).all():
                row_status = "MISSING"

            else:
                probs = [f"{v:.3f}" if not np.isnan(v) else "NaN" for v in row_values]
                row_status = "   ".join(probs)

            print(f"{pattern_str:<{pattern_width}} {row_status}")

    
    def extend_symbols(self, new_symbols):
        if not isinstance(new_symbols, list):
            raise ValueError("new_symbols must be a list.")
    
        current_symbols = set(self.output_info['mapping'].values())
        next_idx = self.output_info['cardinality']
        old_n_columns = self.n_columns
    
        for sym in new_symbols:
            if sym not in current_symbols:
                self.output_info['mapping'][next_idx] = sym
                self.output_info['reverse_mapping'][sym] = next_idx
                next_idx += 1
    
        self.output_info['cardinality'] = next_idx
    
        if next_idx > old_n_columns:
            new_TPM = np.full((self.RN_TPM.shape[0], next_idx), np.nan)
            new_TPM[:, :old_n_columns] = self.RN_TPM
    
            for row_idx in range(self.n_rows):
                if row_idx not in self.missing_rows:
                    new_TPM[row_idx, old_n_columns:next_idx] = 0.0
    
            self.RN_TPM = new_TPM
    
        self.n_columns = next_idx
        self.refresh_TPMs()
    

    def set_row(self, pattern, symbols):
        """
        Set override for a row:
            - list: restrict to allowed symbols
            - dict: prior over symbols

        Args:
            pattern (tuple): input pattern, using visible symbols
            symbols (list or dict): override
        """
        # Convert pattern to row index
        pattern_indices = []
        for i, val in enumerate(pattern):
            rm = self.input_info[i]['reverse_mapping']
            if val not in rm:
                raise ValueError(f"Invalid symbol '{val}' for input '{self.input_info[i]['name']}'")
            pattern_indices.append(rm[val])

        pattern_indices = tuple(pattern_indices)
        row_idx = self.pattern_to_idx.get(pattern_indices)
        if row_idx is None:
            raise ValueError(f"Pattern {pattern} not found in TPM.")

        # Apply override
        if isinstance(symbols, list):
            if len(symbols) == 1:
                # Promote to prior
                return self.set_row(pattern, {symbols[0]: 1.0})

            # RESTRICTION → row still incomplete
            allowed = []
            for sym in symbols:
                if sym not in self.output_info['reverse_mapping']:
                    raise ValueError(f"Output symbol '{sym}' not recognized.")
                allowed.append(self.output_info['reverse_mapping'][sym])

            self.row_overrides[row_idx] = {
                'type': 'restriction',
                'values': allowed
            }

            # Remove from missing_rows since restriction will be filled with uniform dist
            if row_idx in self.missing_rows:
                self.missing_rows.remove(row_idx)

        elif isinstance(symbols, dict):
            # PRIOR → row is now complete
            weights = {}
            total = 0.0
            for sym, w in symbols.items():
                if sym not in self.output_info['reverse_mapping']:
                    raise ValueError(f"Output symbol '{sym}' not recognized.")
                idx = self.output_info['reverse_mapping'][sym]
                weights[idx] = float(w)
                total += w

            if total <= 0:
                raise ValueError("Prior weights must sum to > 0.")

            normalized = {idx: w / total for idx, w in weights.items()}

            self.row_overrides[row_idx] = {
                'type': 'prior',
                'values': normalized
            }

            # Now complete → remove from missing_rows
            if row_idx in self.missing_rows:
                self.missing_rows.remove(row_idx)

        else:
            raise TypeError("symbols must be a list (restriction) or dict (prior)")

        self.refresh_TPMs() 


    def clear_row(self, pattern):
        """Clear any override and mark this row as missing (unconstrained)."""
        # Convert pattern to row index
        pattern_indices = []
        for i, val in enumerate(pattern):
            rm = self.input_info[i]['reverse_mapping']
            if val not in rm:
                raise ValueError(f"Invalid symbol '{val}' for input '{self.input_info[i]['name']}'")
            pattern_indices.append(rm[val])
    
        pattern_indices = tuple(pattern_indices)
        row_idx = self.pattern_to_idx.get(pattern_indices)
        if row_idx is None:
            raise ValueError(f"Pattern {pattern} not found in TPM.")
    
        # Clear override if present
        self.row_overrides.pop(row_idx, None)
    
        # Mark as missing
        self.RN_TPM[row_idx, :] = np.nan
        self.missing_rows.add(row_idx)
    
        # Recompute RN_TPM and MN_TPM
        self.refresh_TPMs()


    def output_entropy(self) -> float:
        """
        Compute entropy H(Y) from the matrix-normalized TPM.
        """
        if self.missing_rows:
            raise ValueError("Output entropy requires a complete TPM.")
        p_y = self.MN_TPM.sum(axis=0)
        return entropy(p_y)
    
    def mutual_information(self) -> float:
        """
        Compute mutual information I(X;Y) = H(Y) - H(Y|X).
        """
        return self.output_entropy() - self.conditional_entropy()

    
    def conditional_entropy(self) -> float:
        """
        Compute conditional entropy H(Y|X) from the joint distribution (self.MN_TPM).
        Requires a complete TPM (no missing rows).
        """
        if self.missing_rows:
            raise ValueError("conditional_entropy requires a complete TPM (no missing rows).")
    
        MN = self.MN_TPM
        row_sums = np.sum(MN, axis=1, keepdims=True)
        row_probs = np.divide(MN, row_sums, where=row_sums > 0)
        row_entropies = -np.sum(np.clip(row_probs, 1e-12, 1.0) * np.log2(np.clip(row_probs, 1e-12, 1.0)), axis=1)
        weights = row_sums[:, 0]
        return np.sum(weights * row_entropies)


    def _precompute_marginalization_maps(self):
        self._marginalization_maps = {}
        n_inputs = len(self.input_info)
    
        # Single-input groupings
        for i in range(n_inputs):
            self._marginalization_maps[(i,)] = self.get_marginalization_map([i])
    
        # All-input grouping (identity)
        full_indices = tuple(range(n_inputs))
        self._marginalization_maps[full_indices] = self.get_marginalization_map(list(full_indices))
    
    def get_marginalization_map(self, indices_to_keep: Tuple[int]) -> Dict[Tuple[int], List[int]]:
        """
        Return a map from partial pattern (given input indices_to_keep)
        to list of row indices (full input patterns) matching that slice.
        """
        cache_key = tuple(sorted(indices_to_keep))
        if not hasattr(self, "_marginalization_maps"):
            self._marginalization_maps = {}
    
        if cache_key in self._marginalization_maps:
            return self._marginalization_maps[cache_key]
    
        # Build map
        grouping = defaultdict(list)
        for idx, pattern in self.idx_to_pattern.items():
            key = tuple(pattern[i] for i in indices_to_keep)
            grouping[key].append(idx)
    
        result = dict(grouping)
        self._marginalization_maps[cache_key] = result
        return result

    def _marginalize_from_joint(self, joint_matrix: np.ndarray, indices_to_keep: List[int]) -> Dict[Tuple[int], np.ndarray]:
        mapping = self.get_marginalization_map(indices_to_keep)
        return {key: np.sum(joint_matrix[rows, :], axis=0) for key, rows in mapping.items()}

    
    def fid(self):
        """
        Compute the Functional Information Decomposition (FID) for a fully specified TPM.
    
        This method quantifies how much each input independently contributes to predicting the output,
        how much is contributed synergistically (i.e., only by the joint state of inputs),
        and how much each input adds in synergy when considered alone (solo synergy).
    
        The FID decomposition includes:
          - **Independent Information**: How much each input predicts the output by itself.
          - **Synergy**: Information only available when inputs are considered jointly.
          - **Solo Synergy**: The contribution of each input when added to all others.
          - **Total Mutual Information**: Between inputs and outputs.
          - **Output and Conditional Entropy**: For completeness and verification.
    
        Returns:
            dict: A dictionary containing:
                - 'total_information' (float): Total mutual information I(X; Y).
                - 'independents' (dict): Map from input label to I(X_i; Y).
                - 'synergy' (float): Residual synergy not explained by independents.
                - 'solo_synergies' (dict): Map from input label to its solo synergy contribution.
                - 'output_entropy' (float): Entropy H(Y).
                - 'conditional_entropy' (float): Conditional entropy H(Y|X).
                - 'input_labels' (list of str): Input variable names, including symbolic state info.
    
        Raises:
            ValueError: If the TPM is incomplete (i.e., has missing rows).
    
        Notes:
            - This decomposition avoids the complexity of full PID lattices,
              but still separates independent and synergistic contributions.
            - Labels for inputs are formatted as "X0[0,1]", "X1[a,b,c]", etc.
        """
        if len(self.missing_rows) > 0:
            raise ValueError("fid requires a completed TPM (no missing rows).")
    
        MN_TPM = self.MN_TPM  # Joint P(X,Y)
        p_y = MN_TPM.sum(axis=0)
        h_y = entropy(p_y)
    
        row_sums = MN_TPM.sum(axis=1, keepdims=True)
        row_probs = np.divide(MN_TPM, row_sums, where=row_sums > 0)
        row_entropies = entropy(row_probs)
        h_y_given_x = np.sum(row_sums[:, 0] * row_entropies)
    
        total_mi = h_y - h_y_given_x
    
        independents = {}
        solo_synergies = {}
        input_labels = []
        all_indices = list(range(len(self.input_info)))
    
        for i in all_indices:
            info = self.input_info[i]
            symbols = [str(info['mapping'][j]) for j in range(info['cardinality'])]
            label = f"{info['name']}[{','.join(symbols)}]"
            input_labels.append(label)
    
            groups_i = self._marginalize_from_joint(MN_TPM, [i])
    
            h_y_given_xi = 0.0
            for p_y_joint in groups_i.values():
                p_pattern = p_y_joint.sum()
                if p_pattern > 0:
                    p_y_cond = p_y_joint / p_pattern
                    h_y_given_xi += p_pattern * entropy(p_y_cond)
    
            independents[label] = h_y - h_y_given_xi
    
        synergy = total_mi - sum(independents.values())
    
        for i, label in enumerate(input_labels):
            indices_wo = [j for j in all_indices if j != i]
            groups_wo = self._marginalize_from_joint(MN_TPM, indices_wo)
    
            h_y_given_wo = 0.0
            for p_y_joint in groups_wo.values():
                p_pattern = p_y_joint.sum()
                if p_pattern > 0:
                    p_y_cond = p_y_joint / p_pattern
                    h_y_given_wo += p_pattern * entropy(p_y_cond)
    
            mi_wo = h_y - h_y_given_wo
            solo_synergy_i = total_mi - mi_wo - independents[label]
            solo_synergies[label] = solo_synergy_i
    
        return {
            'total_information': total_mi,
            'independents': independents,
            'synergy': synergy,
            'solo_synergies': solo_synergies,
            'output_entropy': h_y,
            'conditional_entropy': h_y_given_x,
            'input_labels': input_labels
        }


    def marginalize_batch(self, matrix_batch: np.ndarray, indices_to_keep: List[int]) -> Dict[Tuple[int], np.ndarray]:
        """
        Vectorized marginalization of matrix_batch over selected input indices.

        Args:
            matrix_batch: shape (n_samples, n_rows, n_columns)
            indices_to_keep: which input indices to keep

        Returns:
            Dict[partial pattern -> np.ndarray of shape (n_samples, n_columns)]
        """
        # Uncomment for debugging if errors occur in this function:
        # n_samples, n_rows, n_columns = matrix_batch.shape
        # if n_rows != self.n_rows:
        #     raise ValueError(f"matrix_batch row count ({n_rows}) must match TPM row count ({self.n_rows})")

        mapping = self.get_marginalization_map(indices_to_keep)
    
        result = {}
        for key, row_indices in mapping.items():
            result[key] = np.sum(matrix_batch[:, row_indices, :], axis=1)
        return result


    def vector_fid(self, matrix_batch: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Compute Functional Information Decomposition (FID) for batch of joint distributions (MN_TPM).
        Each matrix in the batch must sum to 1, each row to 1/n_rows.
        """
        n_samples, n_rows, n_columns = matrix_batch.shape
        n_inputs = len(self.input_info)
        all_indices = list(range(n_inputs))
    
        # Output entropy H(Y)
        p_y = matrix_batch.sum(axis=1)  # (n_samples, n_columns)
        h_y = entropy(p_y)              # (n_samples,)
    
        # Conditional entropy H(Y|X)
        p_x = matrix_batch.sum(axis=2)                    # (n_samples, n_rows)
        p_y_given_x = matrix_batch / p_x[..., None]       # (n_samples, n_rows, n_columns)
        row_entropies = entropy(p_y_given_x)              # (n_samples, n_rows)
        h_y_given_x = (p_x * row_entropies).sum(axis=1)   # (n_samples,)
    
        total_mi = h_y - h_y_given_x
    
        independents = {}
        solo_synergies = {}
        input_labels = []
    
        for i in all_indices:
            info = self.input_info[i]
            symbols = [str(info['mapping'][j]) for j in range(info['cardinality'])]
            label = f"{info['name']}[{','.join(symbols)}]"
            input_labels.append(label)
    
            groups_i = self.marginalize_batch(matrix_batch, [i])
    
            h_y_given_xi = np.zeros(n_samples)
            for p_y_joint in groups_i.values():
                p_pattern = p_y_joint.sum(axis=1)
                p_y_cond = np.divide(p_y_joint, p_pattern[:, None], where=p_pattern[:, None] > 0)
                h_cond = entropy(p_y_cond)
                h_y_given_xi += p_pattern * h_cond
    
            independents[label] = h_y - h_y_given_xi
    
        synergy = total_mi - np.sum(list(independents.values()), axis=0)
    
        for i, label in enumerate(input_labels):
            indices_wo = [j for j in all_indices if j != i]
            groups_wo = self.marginalize_batch(matrix_batch, indices_wo)
    
            h_y_given_wo = np.zeros(n_samples)
            for p_y_joint in groups_wo.values():
                p_pattern = p_y_joint.sum(axis=1)
                p_y_cond = np.divide(p_y_joint, p_pattern[:, None], where=p_pattern[:, None] > 0)
                h_cond = entropy(p_y_cond)
                h_y_given_wo += p_pattern * h_cond
    
            mi_wo = h_y - h_y_given_wo
            solo_synergy_i = total_mi - mi_wo - independents[label]
            solo_synergies[label] = solo_synergy_i
    
        return {
            "total_information": total_mi,
            "synergy": synergy,
            "independents": independents,
            "solo_synergies": solo_synergies,
            "output_entropy": h_y,
            "conditional_entropy": h_y_given_x,
        }


    @staticmethod
    def as_cloud_arrays(fid):
        """
        Wraps any single-point FID result dict so all top-level metrics are 1D np.arrays,
        and per-variable dicts are dicts of arrays, matching cloud output format.
        """
        out = {}
        # Scalar keys (always wrap in np.array)
        scalar_keys = [
            "total_information",
            "synergy",
            "output_entropy",
            "conditional_entropy",
        ]
        for k in scalar_keys:
            v = fid[k]
            out[k] = np.array([v])
        # Per-variable metrics
        for k in ("independents", "solo_synergies"):
            d = fid[k]
            out[k] = {kk: np.array([vv]) for kk, vv in d.items()}
        # n_completions
        out["n_completions"] = 1
        return out


    
    def fid_cloud(self,
                  method='dirichlet',
                  n_samples=50000,
                  alpha=1.0,
                  steps=None) -> Dict[str, Any]:

        """
        Compute FID metrics by sampling a stochastic cloud of completions from a distribution over missing rows.
    
        This method generates `n_samples` probabilistic completions of the TPM by sampling
        each missing row from a Dirichlet distribution (default). This produces a "cloud"
        of soft, plausible completions rather than deterministic or structured ones.
    
        It is especially useful for:
          - Exploring variability in FID metrics under random probabilistic assumptions.
          - Modeling noise, uncertainty, or prior beliefs about the space of completions.
          - Generating input to visualizations like scatter clouds or contour plots.
    
        Currently, only Dirichlet-based sampling is supported.
    
        Args:
            method (str): The sampling method to use. Currently only `"dirichlet"` is implemented.
            n_samples (int): Number of TPM completions to sample. Default is 50,000.
            alpha (float): The Dirichlet concentration parameter. Higher values produce more uniform rows,
                while smaller values generate sparser (peaked) distributions.
            steps (ignored): Reserved for future use.
    
        Returns:
            Dict[str, Any]: A dictionary of computed FID metrics.
                All values are NumPy arrays (via `TPM.as_cloud_arrays` if needed).
                Includes the key `"n_completions"` to indicate the number of completions used.
    
        Notes:
            - If there are no missing rows, this returns the FID of the neutral TPM directly.
            - Each missing row is sampled independently across the batch.
            - Output distributions are scaled by the number of rows for normalization.
        """
        
        if len(self.missing_rows) == 0:
            if VERBOSE:
                print("[fid_cloud] No missing rows — running FID on neutral completion.")
            fid = self.fid()
            return TPM.as_cloud_arrays(fid)
    
        if VERBOSE:
            print(f"[fid_cloud] Sampling {n_samples} completions using method '{method}'...")
    
        n_missing = len(self.missing_rows)
        output_dim = self.n_columns
        n_rows = self.n_rows
    
        # Use MN_TPM as the template
        matrix_batch = np.tile(self.MN_TPM[None, :, :], (n_samples, 1, 1))
    
        if method == 'dirichlet':
            dirich = np.random.dirichlet([alpha] * output_dim, size=(n_samples, n_missing))
            dirich /= n_rows
            for i, row_idx in enumerate(sorted(self.missing_rows)):
                matrix_batch[:, row_idx, :] = dirich[:, i, :]
        else:
            raise ValueError(f"Method '{method}' not implemented in fid_cloud().")
    
        results = self.vector_fid(matrix_batch)
        results["n_completions"] = n_samples
        if VERBOSE:
            print(f"[fid_cloud] Done. ({n_samples} completions)")
    
        return TPM.as_cloud_arrays(results) if results["n_completions"] == 1 else results



    # --- fast_integer_compositions ---
    @staticmethod
    def fast_integer_compositions(n, k):
        """Generate all compositions of integer n into k non-negative integers."""
        if k == 1:
            yield (n,)
        else:
            for i in range(n + 1):
                for tail in TPM.fast_integer_compositions(n - i, k - 1):
                    yield (i,) + tail

    @staticmethod
    def random_integer_composition(steps, output_dim):
        # Uniform random weak composition using stars-and-bars bijection
        # Choose (output_dim - 1) cut points from {1, ..., steps + output_dim - 1} without replacement
        cuts = np.sort(np.random.choice(steps + output_dim - 1, output_dim - 1, replace=False) + 1)
        # Adjust cuts by subtracting 1, 2, 3, ... to get positions in [0, steps]
        adjusted = cuts - np.arange(1, output_dim)
        # Composition is differences between consecutive adjusted cuts (with 0 and steps as endpoints)
        composition = np.diff(np.concatenate([[0], adjusted, [steps]]))
        return composition.astype(float) / steps



    def fid_grid(self, steps=None, n_samples=None) -> Dict[str, Any]:
        """
        Compute FID metrics over a structured grid of probabilistic completions
        for missing rows in the TPM, using integer compositions.

        Args:
            steps (int, optional): Number of discretization steps per missing row.
                If None, steps will be determined automatically from `n_samples`
                by backing off to the largest steps that keeps grid size <= n_samples.
            n_samples (int): Maximum number of TPMs to evaluate. Required.

        Returns:
            Dict[str, Any]: Dictionary of FID metrics, with 'n_completions' key.
        """
        if n_samples is None:
            raise ValueError("[fid_grid] `n_samples` must be specified.")

        n_missing = len(self.missing_rows)
        output_dim = self.n_columns

        if n_missing == 0:
            if VERBOSE:
                print("[fid_grid] No missing rows — computing FID on complete TPM.")
            fid = self.fid()
            return TPM.as_cloud_arrays(fid)

        if VERBOSE:
            print("[fid_grid] Constructing grid-based completions...")

        # --- Auto-select steps if not provided ---
        if steps is None:
            steps = 2
            # Climb steps until the NEXT step would exceed n_samples
            while True:
                per_row_points = comb(steps + output_dim - 1, output_dim - 1)
                
                # Check if next step would exceed n_samples
                next_per_row = comb(steps + 1 + output_dim - 1, output_dim - 1)
                next_total = next_per_row ** n_missing
                
                if next_total > n_samples:
                    # Back off: use current steps
                    break
                steps += 1
            
            if VERBOSE:
                per_row_points = comb(steps + output_dim - 1, output_dim - 1)
                total_grid_points = per_row_points ** n_missing
                print(f"[fid_grid] Auto-selected steps={steps} → {total_grid_points} grid points")

        # --- Estimate grid size and decide whether to enumerate or sample ---
        per_row_points = comb(steps + output_dim - 1, output_dim - 1)
        total_grid_points = per_row_points ** n_missing

        # Use n_samples as the safety limit
        use_full_grid = total_grid_points <= n_samples

        if VERBOSE:
            print(f"[fid_grid] Grid size: {total_grid_points} points (limit={n_samples})")

        selected = []

        if use_full_grid:
            if VERBOSE:
                print("[fid_grid] Enumerating full structured grid.")
            
            # Generate base row grid (one-time for all rows)
            base_row = [
                np.array(div, dtype=float) / steps
                for div in self.fast_integer_compositions(steps, output_dim)
            ]
            
            # Cartesian product of all row completions
            grid_per_row = [base_row for _ in range(n_missing)]
            selected = list(product(*grid_per_row))
        else:
            if VERBOSE:
                print(f"[fid_grid] Grid too large ({total_grid_points} > {n_samples}) — random sampling {n_samples} points.")
            
            for _ in range(n_samples):
                candidate = [
                    self.random_integer_composition(steps, output_dim)
                    for _ in range(n_missing)
                ]
                selected.append(candidate)

        # --- Build batch of TPMs ---
        matrix_batch = np.tile(self.MN_TPM[None, :, :], (len(selected), 1, 1))
        for j, completion in enumerate(selected):
            for i, row_idx in enumerate(sorted(self.missing_rows)):
                matrix_batch[j, row_idx, :] = np.array(completion[i], dtype=float) / self.n_rows

        results = self.vector_fid(matrix_batch)
        results["n_completions"] = len(selected)

        if VERBOSE:
            print(f"[fid_grid] Completed. Evaluated {len(selected)} points.")

        return TPM.as_cloud_arrays(results) if len(selected) == 1 else results



    def fid_edges(self, n_samples: int) -> Dict[str, Any]:
        """
        Compute FID metrics by sampling edges between deterministic completions of the TPM.

        Args:
            n_samples (int): Maximum number of completions to evaluate.

        Returns:
            Dict[str, Any]: FID metrics with key 'n_completions'.
        """
        if n_samples is None:
            raise ValueError("[fid_edges] `n_samples` must be provided.")

        n_missing = len(self.missing_rows)
        output_dim = self.n_columns

        if n_missing == 0:
            if VERBOSE:
                print("[fid_edges] No missing rows — running FID on complete TPM.")
            fid = self.fid()
            return self.as_cloud_arrays(fid)

        if VERBOSE:
            print(f"[fid_edges] Building edge samples (n_samples={n_samples})...")

        # Safety check: avoid enumerating if deterministic set is too big
        try:
            threshold = log(10 * n_samples, output_dim)
        except (OverflowError, ValueError):
            threshold = float('-inf')

        if n_missing > threshold:
            if VERBOSE:
                print(f"[fid_edges] Too many completions — sampling {n_samples} random edge midpoints.")

            # Safe fallback: sample random deterministic pairs and their midpoints
            one_hot = np.eye(output_dim)
            matrix_list = []
            for _ in range(n_samples):
                comp1 = [random.choice(one_hot) for _ in range(n_missing)]
                comp2 = [random.choice(one_hot) for _ in range(n_missing)]

                matrix_new = self.MN_TPM.copy()
                for i, row_idx in enumerate(sorted(self.missing_rows)):
                    midpoint = ((comp1[i] + comp2[i]) / 2) / self.n_rows
                    matrix_new[row_idx, :] = midpoint
                matrix_list.append(matrix_new)

            matrix_batch = np.stack(matrix_list, axis=0)
            results = self.vector_fid(matrix_batch)
            results["n_completions"] = matrix_batch.shape[0]
            return self.as_cloud_arrays(results) if results["n_completions"] == 1 else results

        # Safe to build full deterministic set
        one_hot = np.eye(output_dim)
        row_grid = [list(one_hot) for _ in range(n_missing)]
        deterministic_completions = list(product(*row_grid))
        n_deterministic = len(deterministic_completions)

        if VERBOSE:
            print(f"[fid_edges] Found {n_deterministic} deterministic completions.")

        if n_deterministic < 2:
            if VERBOSE:
                print("[fid_edges] Not enough completions for edges.")
            fid = self.fid()
            return self.as_cloud_arrays(fid)

        # Build edges
        edge_pairs = list(combinations(deterministic_completions, 2))
        n_edges = len(edge_pairs)

        if VERBOSE:
            print(f"[fid_edges] Found {n_edges} edges.")

        # Calculate maximum feasible steps per edge
        max_total_steps = n_samples
        steps_per_edge = max(2, max_total_steps // n_edges)
        total_samples = steps_per_edge * n_edges

        if VERBOSE:
            print(f"[fid_edges] Using {steps_per_edge} samples per edge (~{total_samples} total).")

        if total_samples <= n_samples:
            # Full interpolation along edges
            s_values = np.linspace(0.0, 1.0, steps_per_edge)
            matrix_list = []
            for (completion1, completion2) in edge_pairs:
                for s in s_values:
                    matrix_new = self.MN_TPM.copy()
                    for i, row_idx in enumerate(sorted(self.missing_rows)):
                        c1 = np.array(completion1[i], dtype=float)
                        c2 = np.array(completion2[i], dtype=float)
                        row_interp = ((1 - s) * c1 + s * c2) / self.n_rows
                        matrix_new[row_idx, :] = row_interp
                    matrix_list.append(matrix_new)
            matrix_batch = np.stack(matrix_list, axis=0)
        else:
            # Too many → sample random midpoints only
            if VERBOSE:
                print(f"[fid_edges] Too many edges → sampling {n_samples} random edge midpoints.")
            selected_edges = random.sample(edge_pairs, min(n_samples, n_edges))
            matrix_list = []
            for (completion1, completion2) in selected_edges:
                s = 0.5
                matrix_new = self.MN_TPM.copy()
                for i, row_idx in enumerate(sorted(self.missing_rows)):
                    c1 = np.array(completion1[i], dtype=float)
                    c2 = np.array(completion2[i], dtype=float)
                    midpoint = ((1 - s) * c1 + s * c2) / self.n_rows
                    matrix_new[row_idx, :] = midpoint
                matrix_list.append(matrix_new)
            matrix_batch = np.stack(matrix_list, axis=0)

        if VERBOSE:
            print(f"[fid_edges] Final sample count: {matrix_batch.shape[0]}")

        results = self.vector_fid(matrix_batch)
        results["n_completions"] = matrix_batch.shape[0]

        return self.as_cloud_arrays(results) if results["n_completions"] == 1 else results



    def fid_deterministic(self, n_samples: int) -> Dict[str, Any]:
        """
        Compute FID metrics for deterministic completions of the TPM.

        If the number of completions exceeds n_samples * 10, subsample safely
        without materializing the full grid.

        Args:
            n_samples (int): Maximum number of completions to evaluate.

        Returns:
            Dict[str, Any]: FID metrics with key 'n_completions'.
        """
        if n_samples is None:
            raise ValueError("[fid_deterministic] `n_samples` must be provided.")

        n_missing = len(self.missing_rows)
        output_dim = self.n_columns

        if n_missing == 0:
            if VERBOSE:
                print("[fid_deterministic] No missing rows — running FID on complete TPM.")
            fid = self.fid()
            return TPM.as_cloud_arrays(fid)

        if VERBOSE:
            print(f"[fid_deterministic] Building deterministic completions (n_samples={n_samples})...")

        # Estimate total number of deterministic completions safely
        try:
            threshold = log(10 * n_samples, output_dim)
        except (OverflowError, ValueError):
            threshold = float('-inf')

        use_full_grid = n_missing <= threshold

        selected = []

        if use_full_grid:
            # Safe to build full grid of deterministic completions
            one_hot = np.eye(output_dim)
            row_grid = [list(one_hot) for _ in range(n_missing)]
            full_grid = list(product(*row_grid))

            total_completions = len(full_grid)
            if VERBOSE:
                print(f"[fid_deterministic] Total completions: {total_completions}")

            if total_completions > n_samples:
                selected = random.sample(full_grid, n_samples)
                if VERBOSE:
                    print(f"[fid_deterministic] Subsampled to {len(selected)} completions.")
            else:
                selected = full_grid
                if VERBOSE:
                    print(f"[fid_deterministic] Using full grid ({len(selected)} completions).")

        else:
            # Too big → generate deterministic completions by random sampling on-demand
            if VERBOSE:
                print(f"[fid_deterministic] Grid too large — generating {n_samples} random deterministic completions.")

            one_hot = np.eye(output_dim)
            for _ in range(n_samples):
                completion = [random.choice(one_hot) for _ in range(n_missing)]
                selected.append(completion)

        # Build TPM batch
        matrix_batch = np.tile(self.MN_TPM[None, :, :], (len(selected), 1, 1))
        for j, point in enumerate(selected):
            for i, row_idx in enumerate(sorted(self.missing_rows)):
                matrix_batch[j, row_idx, :] = np.array(point[i], dtype=float) / self.n_rows

        results = self.vector_fid(matrix_batch)
        results["n_completions"] = len(selected)

        if VERBOSE:
            print(f"[fid_deterministic] Done. ({results['n_completions']} completions)")

        return TPM.as_cloud_arrays(results) if results["n_completions"] == 1 else results



    def neutral_completion_fid(self) -> Dict[str, Any]:
        """
        Compute FID using a neutral (uniform) completion of missing rows,
        respecting any row restrictions in self.row_overrides.
    
        Returns:
            FID result dictionary matching the format of `fid()`.
        """
        if len(self.missing_rows) == 0:
            if VERBOSE:
                print("[neutral_completion_fid] No missing rows — using current TPM.")
            return self.fid()
    
        if VERBOSE:
            print("[neutral_completion_fid] Running FID with neutral (uniform) completion...")
    
        # Copy current MN_TPM
        matrix = self.MN_TPM.copy()
    
        # Fill in missing rows with uniform (restricted if necessary)
        for row_idx in self.missing_rows:
            override = self.row_overrides.get(row_idx)
            if override and override.get("type") == "restriction":
                allowed = override["values"]
            else:
                allowed = np.arange(self.n_columns)
    
            row = np.zeros(self.n_columns)
            row[allowed] = 1.0 / len(allowed)
            matrix[row_idx] = row / self.n_rows  # Maintain joint normalization
    
        # Compute FID as a batch of size 1
        batch = matrix[None, :, :]
        result = self.vector_fid(batch)
    
        # Get input labels in the same order as `fid()`
        input_labels = []
        for i in range(len(self.input_info)):
            info = self.input_info[i]
            symbols = [str(info['mapping'][j]) for j in range(info['cardinality'])]
            label = f"{info['name']}[{','.join(symbols)}]"
            input_labels.append(label)
    
        return {
            "total_information": result["total_information"][0],
            "synergy": result["synergy"][0],
            "independents": {k: v[0] for k, v in result["independents"].items()},
            "solo_synergies": {k: v[0] for k, v in result["solo_synergies"].items()},
            "output_entropy": result["output_entropy"][0],
            "conditional_entropy": result["conditional_entropy"][0],
            "input_labels": input_labels,
        }

##############################################################################################

def entropy(probs: np.ndarray) -> np.ndarray:
    """Vectorized entropy."""
    probs = np.clip(probs, 1e-12, 1.0)
    return -np.sum(probs * np.log2(probs), axis=-1)


def display_fid(fid):
    """Display FID results in a human-readable format."""

    print("\nFunctional Information Decomposition Report")
    print("=" * 60)

    # Header
    print(f"{'Variable':<20} {'Independent':<15} {'Solo-Synergy':<15}")
    print("-" * 50)

    # Per-variable info
    for label in fid['input_labels']:
        ind = fid['independents'][label]
        solo = fid['solo_synergies'][label]
        print(f"{label:<20} {ind:>10.4f} bits   {solo:>10.4f} bits")

    print("-" * 50)
    print(f"Synergy: {fid['synergy']:.4f} bits")
    print(f"Total Information: {fid['total_information']:.4f} bits")
    print()
    print(f"H(output)        : {fid['output_entropy']:.4f} bits")
    print(f"H(output|inputs) : {fid['conditional_entropy']:.4f} bits")
    print()

def _format_num(val, width=7, prec=4):
    if abs(val) < 1e-10:
        val = 0.0
    return f"{val:{width}.{prec}f}"


def display_fid_with_bounds(base_fid, clouds):
    """
    Print a FID report with uncertainty bounds for each variable, synergy, total information, etc.
    Assumes all clouds (and base_fid) have metrics as arrays, even for single points.
    """
    print()
    print("Functional Information Decomposition with Uncertainty Bounds")
    print("=" * 70)

    indep_vars = list(base_fid['independents'].keys())
    solo_vars = list(base_fid['solo_synergies'].keys())

    def cat_metric(metric, var):
        # Stack all arrays for a given metric/var from all clouds
        arrs = [np.asarray(cloud[metric][var]) for cloud in clouds]
        return np.concatenate(arrs)

    def cat_top_metric(metric):
        # Stack all arrays for a top-level metric from all clouds
        arrs = [np.asarray(cloud[metric]) for cloud in clouds]
        return np.concatenate(arrs)

    print(f"{'Variable':<14}{'Independent':<22}{'Solo-Synergy':<22}")
    print('-' * 55)

    for var in indep_vars:
        base_indep = np.asarray(base_fid['independents'][var]).item()
        arr_indep = cat_metric('independents', var)
        max_indep = np.max(arr_indep)
        min_indep = np.min(arr_indep)

        base_solo = np.asarray(base_fid['solo_synergies'][var]).item()
        arr_solo = cat_metric('solo_synergies', var)
        max_solo = np.max(arr_solo)
        min_solo = np.min(arr_solo)

        print(f"{var:<14}"
              f"{_format_num(base_indep)} ({_format_num(max_indep)}/{_format_num(min_indep)})"
              f"   {_format_num(base_solo)} ({_format_num(max_solo)}/{_format_num(min_solo)})")

    print('-' * 55)

    base_syn = np.asarray(base_fid['synergy']).item()
    arr_syn = cat_top_metric('synergy')
    max_syn = np.max(arr_syn)
    min_syn = np.min(arr_syn)
    print(f"Synergy: {_format_num(base_syn)} ({_format_num(max_syn)}/{_format_num(min_syn)}) bits")

    base_ti = np.asarray(base_fid['total_information']).item()
    arr_ti = cat_top_metric('total_information')
    max_ti = np.max(arr_ti)
    min_ti = np.min(arr_ti)
    print(f"Total Information: {_format_num(base_ti)} ({_format_num(max_ti)}/{_format_num(min_ti)}) bits")
    print()
    base_hy = np.asarray(base_fid['output_entropy']).item()
    print(f"H(output)        : {_format_num(base_hy)} bits")

    base_hyx = np.asarray(base_fid['conditional_entropy']).item()
    print(f"H(output|inputs) : {_format_num(base_hyx)} bits")
    print()


def get_metric(cloud, metric_name):
    """
    Helper function to retrieve a specific metric from a FID cloud dictionary.

    This function attempts to resolve `metric_name` by:
      1. Looking for an exact key match at the top level of the cloud.
      2. Handling special suffixes:
         - If the name ends with "_solo_synergy", it looks inside cloud["solo_synergies"].
         - If the name ends with "_independent", it looks inside cloud["independents"].
      3. If no exact match is found in those sub-dictionaries, it will attempt to match
         by stripping bracketed suffixes from keys (e.g., "X0[0,1]" → "X0").

    Args:
        cloud (dict): A dictionary representing a FID cloud containing various metrics,
            including top-level keys and optional nested dicts for "solo_synergies" and "independents".
        metric_name (str): The name of the metric to retrieve.

    Returns:
        The corresponding metric value (typically a list or NumPy array), or `None` if not found.
    """

    # 1. Try exact match at top-level
    if metric_name in cloud:
        return cloud[metric_name]
    # 2. Handle "_solo_synergy" and "_independent"
    if metric_name.endswith("_solo_synergy"):
        base = metric_name[:-len("_solo_synergy")]
        # Look in solo_synergies for exact match
        candidates = cloud.get("solo_synergies", {})
        if base in candidates:
            return candidates[base]
        # Try stripping [] (e.g., "X0[0,1]" -> "X0")
        for k in candidates:
            k_base = k.split("[")[0]
            if k_base == base:
                return candidates[k]
    if metric_name.endswith("_independent"):
        base = metric_name[:-len("_independent")]
        candidates = cloud.get("independents", {})
        if base in candidates:
            return candidates[base]
        for k in candidates:
            k_base = k.split("[")[0]
            if k_base == base:
                return candidates[k]
    # Not found
    return None


def plot_fid_clouds(
    fid_clouds: list,
    names: list,
    colors: list,
    alphas: list,
    x_metric: str,
    y_metric: str,
    base_fid: dict = None,
    markers: list = None,
    figsize=(8, 6),
    filename=None
):
    """
    Plot FID clouds on the same axes, optionally with a base assumption.
    Legend shows each cloud's marker and color, alpha=1 in legend.
    If base_fid is provided, it is shown as red crosshairs.
    """
    plt.figure(figsize=figsize)

    if markers is None:
        markers = ['.'] * len(fid_clouds)

    legend_handles = []

    for cloud, label, color, alpha, marker in zip(fid_clouds, names, colors, alphas, markers):
        x_vals = get_metric(cloud, x_metric)
        y_vals = get_metric(cloud, y_metric)
        if x_vals is None or y_vals is None:
            raise ValueError(f"Metric '{x_metric}' or '{y_metric}' not found in cloud '{label}'.")
        x_vals = np.asarray(x_vals)
        y_vals = np.asarray(y_vals)
        plt.scatter(x_vals, y_vals, color=color, alpha=alpha, marker=marker, edgecolors='none', s=10)
        # For the legend: full alpha, same marker and color
        legend_handles.append(Line2D([0], [0], marker=marker, color='w', label=label,
                                     markerfacecolor=color, markeredgecolor=color, markersize=8, alpha=1, linestyle='None'))

    # Base assumption as red crosshair (only if provided)
    if base_fid is not None:
        base_x = get_metric(base_fid, x_metric)
        base_y = get_metric(base_fid, y_metric)
        if base_x is None or base_y is None:
            raise ValueError(f"Metric '{x_metric}' or '{y_metric}' not found in base FID.")
        if isinstance(base_x, (list, np.ndarray)):
            base_x = np.asarray(base_x).item()
        if isinstance(base_y, (list, np.ndarray)):
            base_y = np.asarray(base_y).item()

        plt.axvline(base_x, color='red', linestyle='--', lw=1)
        plt.axhline(base_y, color='red', linestyle='--', lw=1)
        legend_handles.append(Line2D([0], [0], marker='+', color='red', label='Base Assumption',
                                     markerfacecolor='red', markeredgecolor='red', markersize=10, linestyle='None', alpha=1))

    plt.xlabel(x_metric.replace('_', ' '))
    plt.ylabel(y_metric.replace('_', ' '))
    legend = plt.legend(
        handles=legend_handles,
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        borderaxespad=0
    )
    plt.tight_layout()

    if filename is not None:
        plt.savefig(
            filename,
            bbox_extra_artists=(legend,),
            bbox_inches='tight'
        )

    plt.show()

def plot_fid_clouds_3d(
    fid_clouds: list,
    names: list,
    colors: list,
    alphas: list,
    x_metric: str,
    y_metric: str,
    z_metric: str,
    base_fid: dict = None,
    markers: list = None,
    figsize=(10, 8),
    filename=None
):
    """
    Plot FID clouds in 3D (three axes), optionally with a base assumption.
    Legend shows each cloud's marker and color, alpha=1 in legend.
    If base_fid is provided, it is shown as a red '+' marker.
    """
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection='3d')
    ax.set_proj_type('ortho')

    if markers is None:
        markers = ['.'] * len(fid_clouds)

    legend_handles = []

    for cloud, label, color, alpha, marker in zip(fid_clouds, names, colors, alphas, markers):
        x_vals = get_metric(cloud, x_metric)
        y_vals = get_metric(cloud, y_metric)
        z_vals = get_metric(cloud, z_metric)
        if x_vals is None or y_vals is None or z_vals is None:
            raise ValueError(f"Metric '{x_metric}', '{y_metric}', or '{z_metric}' not found in cloud '{label}'.")
        x_vals = np.asarray(x_vals)
        y_vals = np.asarray(y_vals)
        z_vals = np.asarray(z_vals)
        ax.scatter(x_vals, y_vals, z_vals, color=color, alpha=alpha, marker=marker, edgecolors='none', s=10)
        # Legend: marker and color, full alpha
        legend_handles.append(Line2D([0], [0], marker=marker, color='w', label=label,
                                     markerfacecolor=color, markeredgecolor=color, markersize=8, alpha=1, linestyle='None'))

    # Base assumption as red '+' (only if provided)
    if base_fid is not None:
        base_x = get_metric(base_fid, x_metric)
        base_y = get_metric(base_fid, y_metric)
        base_z = get_metric(base_fid, z_metric)
        if base_x is None or base_y is None or base_z is None:
            raise ValueError(f"Metric '{x_metric}', '{y_metric}', or '{z_metric}' not found in base FID.")
        if isinstance(base_x, (list, np.ndarray)):
            base_x = np.asarray(base_x).item()
        if isinstance(base_y, (list, np.ndarray)):
            base_y = np.asarray(base_y).item()
        if isinstance(base_z, (list, np.ndarray)):
            base_z = np.asarray(base_z).item()

        ax.scatter([base_x], [base_y], [base_z], color='red', marker='+', s=100, linewidths=3)
        legend_handles.append(Line2D([0], [0], marker='+', color='red', label='Base Assumption',
                                     markerfacecolor='red', markeredgecolor='red', markersize=10, linestyle='None', alpha=1))

    ax.set_xlabel(x_metric.replace('_', ' '))
    ax.set_ylabel(y_metric.replace('_', ' '))
    ax.set_zlabel(z_metric.replace('_', ' '))
    legend = plt.legend(
        handles=legend_handles,
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        borderaxespad=0
    )
    plt.tight_layout()

    if filename is not None:
        plt.savefig(
            filename,
            bbox_extra_artists=(legend,),
            bbox_inches='tight'
        )

    plt.show()



def plot_fid_relationships(
    fid_clouds: list,
    names: list,
    colors: list,
    alphas: list,
    y_metric: str,
    base_fid: dict = None,
    markers: list = None,
    figsize=(16, 4),
    filename=None,
    share_axis: str = "common",  # accepts: "none", "row", "column", "common", "all"
):

    """
    Plot a grid of scatter plots showing relationships between FID metrics across multiple datasets.

    This function creates a matrix of scatter plots comparing different information-theoretic
    components (e.g., independent, solo synergy, loss) for a set of `fid_clouds`, optionally against a baseline `base_fid`.

    The top row shows global metrics (synergy and total information).
    Each subsequent row corresponds to an input variable, with four columns showing:
      - Independent information vs. y-axis metric
      - Solo synergy vs. y-axis metric
      - Loss vs. y-axis metric
      - Solo synergy vs. independent (2D relationship)

    Axis labels are automatically cleaned to remove bracketed variable state descriptors (e.g., "[0,1]").

    Args:
        fid_clouds (list of dict): List of FID dictionaries to compare.
        names (list of str): Labels for each FID cloud, used in the legend.
        colors (list): Colors for each FID cloud (e.g., strings or RGB tuples).
        alphas (list of float): Alpha (transparency) values for each cloud's scatter points.
        y_metric (str): Key name in the FID dict to use as the Y-axis for most plots.
                      This can be synergy, total_information, or independent or solo_synergy
                      for an input (indicated with inputname_value), e.g., "X1_solo_synergy"
        base_fid (dict, optional): The FID solution for a single function (usually neutral completion).
                      If provided, shown as red crosshairs on each subplot.
        markers (list, optional): Marker styles for each cloud (e.g., '.', 'o'). Defaults to '.' for all.
        figsize (tuple, optional): Figure size for the full plot grid. Default is (16, 4).
        filename (str, optional): If provided, saves the figure to this path.
        share_axis (str): Determines how axis limits are shared across plots.
            Options:
                - "none": Each subplot has its own axis limits.
                - "row": All plots in a row share axis limits.
                - "column": All plots in a column share axis limits.
                - "common": Default. All plots in columns 1, 2 and 3 all share axis limits, all plots in column 4 shares axis
                - "all": All plots share the same axis limits.

    Returns:
        None. Displays (and optionally saves) a matplotlib figure.
    """

    def strip_brackets(name):
        return re.sub(r"\[.*?\]", "", name).strip()

    # Get input_labels from base_fid if provided, otherwise from first cloud's independents keys
    if base_fid is not None:
        input_labels = base_fid["input_labels"]
    else:
        input_labels = list(fid_clouds[0]["independents"].keys())
    n_inputs = len(input_labels)
    total_rows = n_inputs + 1
    total_cols = 4

    if markers is None:
        markers = ['.'] * len(fid_clouds)

    fig, axes = plt.subplots(total_rows, total_cols, figsize=figsize, squeeze=False)

    def get_all_xy():
        data = {
            "full": [],
            "common": [],
            "column3": [],
            "rows": [[] for _ in range(total_rows)],
            "columns": [[] for _ in range(total_cols)],
        }

        for x_key in ["synergy", "total_information"]:
            for cloud in fid_clouds:
                x = np.asarray(get_metric(cloud, x_key))
                y = np.asarray(get_metric(cloud, y_metric))
                data["full"].append((x, y))
                data["common"].append((x, y))
                data["rows"][0].append((x, y))
                if x_key == "synergy":
                    data["columns"][1].append((x, y))
                else:
                    data["columns"][2].append((x, y))

        for i, var in enumerate(input_labels):
            r = i + 1
            for cloud in fid_clouds:
                x_ind = np.asarray(get_metric(cloud, f"{var}_independent"))
                x_solo = np.asarray(get_metric(cloud, f"{var}_solo_synergy"))
                x_loss = x_ind + x_solo
                y_val = np.asarray(get_metric(cloud, y_metric))

                data["full"] += [(x_ind, y_val), (x_solo, y_val), (x_loss, y_val)]
                data["common"] += [(x_ind, y_val), (x_solo, y_val), (x_loss, y_val)]
                data["rows"][r] += [(x_ind, y_val), (x_solo, y_val), (x_loss, y_val)]
                data["columns"][0].append((x_ind, y_val))
                data["columns"][1].append((x_solo, y_val))
                data["columns"][2].append((x_loss, y_val))

                data["full"].append((x_solo, x_ind))
                data["column3"].append((x_solo, x_ind))
                data["rows"][r].append((x_solo, x_ind))
                data["columns"][3].append((x_solo, x_ind))

        return data

    def compute_bounds(pairs):
        x_all = np.concatenate([x for x, _ in pairs])
        y_all = np.concatenate([y for _, y in pairs])
        x_delta = x_all.ptp()
        y_delta = y_all.ptp()
        xlim = (x_all.min() - .05 * x_delta, x_all.max() + .05 * x_delta)
        ylim = (y_all.min() - .05 * y_delta, y_all.max() + .05 * y_delta)
        return xlim, ylim

    def apply_bounds(ax, bounds):
        if bounds:
            xlim, ylim = bounds
            ax.set_xlim(*xlim)
            ax.set_ylim(*ylim)

    global_bounds = {}
    common_bounds = {}
    column3_bounds = {}
    row_bounds = {}
    col_bounds = {}

    axis_data = get_all_xy()

    if share_axis == "all":
        global_bounds = compute_bounds(axis_data["full"])
    elif share_axis == "common":
        common_bounds = compute_bounds(axis_data["common"])
        column3_bounds = compute_bounds(axis_data["column3"])
    elif share_axis == "row":
        row_bounds = {i: compute_bounds(pairs) for i, pairs in enumerate(axis_data["rows"])}
    elif share_axis == "column":
        col_bounds = {j: compute_bounds(pairs) for j, pairs in enumerate(axis_data["columns"])}

    # Top row
    ax = axes[0, 1]
    for cloud, name, color, alpha, marker in zip(fid_clouds, names, colors, alphas, markers):
        x = np.asarray(get_metric(cloud, "synergy"))
        y = np.asarray(get_metric(cloud, y_metric))
        ax.scatter(x, y, alpha=alpha, color=color, marker=marker, edgecolors='none', s=10)
    if base_fid is not None:
        ax.axvline(get_metric(base_fid, "synergy"), color='red', linestyle='--', lw=1)
        ax.axhline(get_metric(base_fid, y_metric), color='red', linestyle='--', lw=1)
    ax.set_xlabel("synergy")
    ax.set_ylabel(y_metric.replace("_", " "))
    apply_bounds(ax, {
        "all": global_bounds,
        "row": row_bounds.get(0),
        "common": common_bounds,
        "column": col_bounds.get(1)
    }.get(share_axis))

    ax2 = axes[0, 2]
    for cloud, name, color, alpha, marker in zip(fid_clouds, names, colors, alphas, markers):
        x = np.asarray(get_metric(cloud, "total_information"))
        y = np.asarray(get_metric(cloud, y_metric))
        ax2.scatter(x, y, alpha=alpha, color=color, marker=marker, edgecolors='none', s=10)
    if base_fid is not None:
        ax2.axvline(get_metric(base_fid, "total_information"), color='red', linestyle='--', lw=1)
        ax2.axhline(get_metric(base_fid, y_metric), color='red', linestyle='--', lw=1)
    ax2.set_xlabel("total information")
    ax2.set_ylabel(y_metric.replace("_", " "))
    apply_bounds(ax2, {
        "all": global_bounds,
        "row": row_bounds.get(0),
        "common": common_bounds,
        "column": col_bounds.get(2)
    }.get(share_axis))

    handles = [
        Line2D([0], [0], marker=marker, color='w', label=name,
               markerfacecolor=color, markeredgecolor=color,
               markersize=10, linestyle='None', alpha=1.0)
        for name, color, marker in zip(names, colors, markers)
    ]
    axes[0, 0].legend(handles=handles, loc='center')
    axes[0, 0].set_axis_off()
    axes[0, 3].axis("off")

    for i, var in enumerate(input_labels):
        r = i + 1
        var_clean = strip_brackets(var)
        if base_fid is not None:
            base_ind = get_metric(base_fid, f"{var}_independent")
            base_solo = get_metric(base_fid, f"{var}_solo_synergy")
            base_loss = base_ind + base_solo

        ax0 = axes[r, 0]
        for cloud, color, alpha, marker in zip(fid_clouds, colors, alphas, markers):
            x = np.asarray(get_metric(cloud, f"{var}_independent"))
            y = np.asarray(get_metric(cloud, y_metric))
            ax0.scatter(x, y, alpha=alpha, color=color, marker=marker, edgecolors='none', s=10)
        if base_fid is not None:
            ax0.axvline(base_ind, color='red', linestyle='--', lw=1)
            ax0.axhline(get_metric(base_fid, y_metric), color='red', linestyle='--', lw=1)
        ax0.set_xlabel(f"{var_clean} independent")
        ax0.set_ylabel(y_metric.replace("_", " "))
        apply_bounds(ax0, {
            "all": global_bounds,
            "row": row_bounds.get(r),
            "common": common_bounds,
            "column": col_bounds.get(0)
        }.get(share_axis))

        ax1 = axes[r, 1]
        for cloud, color, alpha, marker in zip(fid_clouds, colors, alphas, markers):
            x = np.asarray(get_metric(cloud, f"{var}_solo_synergy"))
            y = np.asarray(get_metric(cloud, y_metric))
            ax1.scatter(x, y, alpha=alpha, color=color, marker=marker, edgecolors='none', s=10)
        if base_fid is not None:
            ax1.axvline(base_solo, color='red', linestyle='--', lw=1)
            ax1.axhline(get_metric(base_fid, y_metric), color='red', linestyle='--', lw=1)
        ax1.set_xlabel(f"{var_clean} solo synergy")
        ax1.set_ylabel(y_metric.replace("_", " "))
        apply_bounds(ax1, {
            "all": global_bounds,
            "row": row_bounds.get(r),
            "common": common_bounds,
            "column": col_bounds.get(1)
        }.get(share_axis))

        ax2 = axes[r, 2]
        for cloud, color, alpha, marker in zip(fid_clouds, colors, alphas, markers):
            x = (np.asarray(get_metric(cloud, f"{var}_independent")) +
                 np.asarray(get_metric(cloud, f"{var}_solo_synergy")))
            y = np.asarray(get_metric(cloud, y_metric))
            ax2.scatter(x, y, alpha=alpha, color=color, marker=marker, edgecolors='none', s=10)
        if base_fid is not None:
            ax2.axvline(base_loss, color='red', linestyle='--', lw=1)
            ax2.axhline(get_metric(base_fid, y_metric), color='red', linestyle='--', lw=1)
        ax2.set_xlabel(f"{var_clean} loss")
        ax2.set_ylabel(y_metric.replace("_", " "))
        apply_bounds(ax2, {
            "all": global_bounds,
            "row": row_bounds.get(r),
            "common": common_bounds,
            "column": col_bounds.get(2)
        }.get(share_axis))

        ax3 = axes[r, 3]
        for cloud, color, alpha, marker in zip(fid_clouds, colors, alphas, markers):
            x = np.asarray(get_metric(cloud, f"{var}_solo_synergy"))
            y = np.asarray(get_metric(cloud, f"{var}_independent"))
            ax3.scatter(x, y, alpha=alpha, color=color, marker=marker, edgecolors='none', s=10)
        if base_fid is not None:
            ax3.axvline(base_solo, color='red', linestyle='--', lw=1)
            ax3.axhline(base_ind, color='red', linestyle='--', lw=1)
        ax3.set_xlabel(f"{var_clean} solo synergy")
        ax3.set_ylabel(f"{var_clean} independent")
        apply_bounds(ax3, {
            "all": global_bounds,
            "row": row_bounds.get(r),
            "common": column3_bounds,
            "column": col_bounds.get(3)
        }.get(share_axis))

    plt.tight_layout()
    if filename:
        plt.savefig(filename, bbox_inches='tight')
    plt.show()