"""CancerLab - Machine Learning Library for Cancer Detection"""
__version__ = "1.0.0"
__author__ = "Balaga Raghuram"

import numpy as np

class CancerClassifier:
    """
    Cancer classification model using machine learning.
    
    Parameters
    ----------
    model_type : str
        Type of model ('random_forest', 'svm', 'neural_net')
    
    Examples
    --------
    >>> from cancerlab import CancerClassifier, load_sample_data
    >>> X, y = load_sample_data()
    >>> clf = CancerClassifier()
    >>> clf.fit(X[:400], y[:400])
    >>> predictions = clf.predict(X[400:])
    """
    
    def __init__(self, model_type='random_forest'):
        self.model_type = model_type
        self.model = None
        self.is_fitted = False
        
    def fit(self, X, y):
        """Train the cancer classification model."""
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.svm import SVC
            from sklearn.neural_network import MLPClassifier
            
            if self.model_type == 'random_forest':
                self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            elif self.model_type == 'svm':
                self.model = SVC(probability=True, random_state=42)
            elif self.model_type == 'neural_net':
                self.model = MLPClassifier(hidden_layer_sizes=(64,32), random_state=42)
            else:
                raise ValueError(f"Unknown model type: {self.model_type}")
            
            self.model.fit(X, y)
            self.is_fitted = True
        except ImportError:
            raise ImportError("scikit-learn is required. Install with: pip install scikit-learn")
        
        return self
    
    def predict(self, X):
        """Predict cancer class labels."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict class probabilities."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        return self.model.predict_proba(X)

def load_sample_data():
    """
    Load sample breast cancer dataset for testing.
    
    Returns
    -------
    X : array of shape (569, 30)
        Feature matrix
    y : array of shape (569,)
        Target labels (0=malignant, 1=benign)
    """
    try:
        from sklearn.datasets import load_breast_cancer
        data = load_breast_cancer()
        return data.data, data.target
    except ImportError:
        raise ImportError("scikit-learn is required")

__all__ = ['CancerClassifier', 'load_sample_data']
