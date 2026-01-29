from sklearn.decomposition import PCA
import numpy as np


def get_pca_loadings(pca_obj: PCA):
    """
    Calculate the loadings of the fitted PCA instance from scikit learn.

    Loadings in PCA are analogous to the coefficients of a linear model.
    """
    return pca_obj.components_.T * np.sqrt(pca_obj.explained_variance_)