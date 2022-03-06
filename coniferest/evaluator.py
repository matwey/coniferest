import numpy as np
from .utils import average_path_length
from .calc_paths_sum import calc_paths_sum  # noqa


class ForestEvaluator:
    selector_dtype = np.dtype([('feature', np.int32), ('left', np.int32), ('value', np.double), ('right', np.int32)])

    def __init__(self, samples, selectors, indices):
        """
        Base class for the forest evaluators. Does the trivial job:
        * runs calc_paths_sum written in cython,
        * helps to combine several trees' representations into two arrays.

        Parameters
        ----------
        samples
            Number of samples in every tree.

        selectors
            Array with all the nodes of all the trees.

        indices
            Indices of starting nodes of every tree.
        """
        self.samples = samples

        self.selectors = selectors
        self.indices = indices

    @classmethod
    def combine_selectors(cls, selectors_list):
        """
        Combine several node arrays into one array of nodes and one array of
        start indices.

        Parameters
        ----------
        selectors_list
            List of node arrays to combine.

        Returns
        -------
        Pair of two arrays: node array and array of starting indices.
        """
        lens = [len(sels) for sels in selectors_list]
        full_len = sum(lens)

        selectors = np.empty((full_len,), dtype=cls.selector_dtype)

        indices = np.empty((len(selectors_list) + 1,), dtype=np.int64)
        indices[0] = 0
        indices[1:] = np.add.accumulate(lens)

        for i in range(len(selectors_list)):
            selectors[indices[i]:indices[i + 1]] = selectors_list[i]

        return selectors, indices

    def score_samples(self, x):
        """
        Perform the computations.

        Parameters
        ----------
        x
            Features to calculate scores of. Should be C-contiguous for performance.

        Returns
        -------
        Array of scores.
        """
        if not x.flags['C_CONTIGUOUS']:
            x = np.ascontiguousarray(x)

        trees = self.indices.shape[0] - 1

        return -2 ** (- calc_paths_sum(self.selectors, self.indices, x) / (self.average_path_length(self.samples) * trees))

    @classmethod
    def average_path_length(cls, n_nodes):
        """
        Average path length is abstracted because in different cases we may want to
        use a bit different formulas to make the exact match with other software.

        By default we use our own implementation.
        """
        return average_path_length(n_nodes)
