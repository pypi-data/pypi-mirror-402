import matplotlib.pyplot as plt
import numpy as np
import scipy.io
from matplotlib import gridspec
from scipy.stats import pearsonr
from sklearn.base import BaseEstimator, TransformerMixin
from scipy import stats

class PartialCCA(BaseEstimator, TransformerMixin):

    # Joaquin Gonzalez, Buzsaki lab, Chen Lab.
    
    def __init__(self, regularization=1e-3):
        self.regularization = regularization

    def fit(self, X, Y, Z = None, verbose=True):

        """
        Computes Partial Canonical Correlation Analysis (pCCA) using eigenvalue decomposition
        based on sklearn's cross decomposition approach. Aims to extract eigenvectors
        corresponding to CCA weights for datax and datay from the m_matrix.
    
        Args:
            datax (numpy.ndarray): Data array X of shape (n_samples, n_features_x).
            datay (numpy.ndarray): Data array Y of shape (n_samples, n_features_y).
            dataz (numpy.ndarray): Conditional data array Z of shape (n_samples, n_features_z).
            regularization (float, optional): Regularization parameter. Defaults to 1e-6.
    
        Returns:
            tuple: A tuple containing:
                - canonical_correlations (numpy.ndarray): Real-valued canonical correlations, shape (min(n_features_x, n_features_y),).
                - wx (numpy.ndarray): Real-valued canonical weights for datax, shape (n_features_x, min(n_features_x, n_features_y)).
                - wy (numpy.ndarray): Real-valued canonical weights for datay, shape (n_features_y, min(n_features_x, n_features_y)).
                           Returns empty arrays if there are issues in computation.
        """

        # default to regular CCA if z is not provided  
        if Z is None:
            if verbose:
                print("The variable Z is not provided for partial CCA, defaulting to regular CCA.")
            n_samples = X.shape[0]
            X_resid = X
            Y_resid = Y
            
        else:
            n_samples = X.shape[0]
            ZTZ_inv = np.linalg.pinv(Z.T @ Z)
            self.X_beta_ = ZTZ_inv @ Z.T @ X
            self.Y_beta_ = ZTZ_inv @ Z.T @ Y
    
            X_resid = X - Z @ self.X_beta_
            Y_resid = Y - Z @ self.Y_beta_
            self.X_resid_ = X - Z @ self.X_beta_
            self.Y_resid_ = Y - Z @ self.Y_beta_

        sigma_xx = (X_resid.T @ X_resid) / (n_samples - 1)
        sigma_yy = (Y_resid.T @ Y_resid) / (n_samples - 1)
        sigma_xy = (X_resid.T @ Y_resid) / (n_samples - 1)
        sigma_yx = sigma_xy.T

        sigma_xx += self.regularization * np.eye(X.shape[1])
        sigma_yy += self.regularization * np.eye(Y.shape[1])

        sigma_xx_inv = np.linalg.pinv(sigma_xx)
        sigma_yy_inv = np.linalg.pinv(sigma_yy)

        m = sigma_xx_inv @ sigma_xy @ sigma_yy_inv @ sigma_yx
        eigvals, eigvecs_x = np.linalg.eig(m)

        canonical_corrs_sq = np.clip(np.real(eigvals), 0, None)
        canonical_corrs = np.sqrt(canonical_corrs_sq)
        sorted_idx = np.argsort(canonical_corrs)[::-1]

        n_components = min(X_resid.shape[1], Y_resid.shape[1])
        self.canonical_correlations_ = canonical_corrs[sorted_idx][:n_components]
        self.weights_x_ = np.real(eigvecs_x[:, sorted_idx][:, :n_components])
        self.weights_x_ /= np.linalg.norm(self.weights_x_, axis=0, keepdims=True)
        
        self.weights_y_ = np.linalg.solve(sigma_yy, sigma_yx @ self.weights_x_)
        self.weights_y_ = np.real(self.weights_y_)
        self.weights_y_ /= np.linalg.norm(self.weights_y_, axis=0, keepdims=True)

        return self

    def transform(self, X, Y):
        projections_x = []
        projections_y = []
        for i in range(self.weights_x_.shape[1]):
            # Custom projection: weighted sum across neurons (features) at each time point
            proj_x = np.nansum(X.T * self.weights_x_[:, i][:, np.newaxis], axis=0)
            proj_y = np.nansum(Y.T * self.weights_y_[:, i][:, np.newaxis], axis=0)
            projections_x.append(proj_x)
            projections_y.append(proj_y)
        return np.array(projections_x), np.array(projections_y)

    def fit_transform(self, X, Y, Z = None):
        self.fit(X, Y, Z)
        return self.transform(X, Y)
        
    def score(self, X, Y):
        proj_x, proj_y = self.transform(X, Y)
        return np.array([
            pearsonr(proj_x[i], proj_y[i])[0]
            for i in range(proj_x.shape[0])
        ])

    def surrogate_test(self, X, Y, Z = None, n_surrogates = 100):    
        # perform surrogates based on randomly circularly shifting one population and keeping the other two the same
        r_real = self.canonical_correlations_
        r_surr = []    
        if Z is None:
            print("The variable Z is not provided for partial CCA, defaulting to regular CCA.")
            
        for surrogates in range(n_surrogates):
            shift_val = np.random.randint(1, X.shape[0])
            X_roll = np.roll(X,shift = shift_val,axis = 0) # circular shift
            temp_model = PartialCCA()
            if Z is None:
                temp_model.fit(X_roll, Y, verbose = False)
            else:
                temp_model.fit(X_roll, Y, Z)
            r = temp_model.canonical_correlations_[0]
            r_surr.append(r)

        p_value = []
        for comp in r_real:
            p_value.append(np.sum(r_surr>comp)/n_surrogates)
        return p_value, r_surr