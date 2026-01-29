"""
NLP Templates - Production-ready ML classification templates.

This package provides ready-to-use machine learning classification templates
with support for hierarchical classification, neural networks, and MLflow integration.

Example usage:
    >>> from nlp_templates.classifiers import SimpleMulticlassClassifier
    >>> clf = SimpleMulticlassClassifier(name="my_classifier")
    >>> clf.load_data(X, y)
    >>> clf.build_model()
    >>> clf.train()
    >>> results = clf.evaluate()

For hierarchical classification:
    >>> from nlp_templates.classifiers import HierarchicalNNClassifier
    >>> clf = HierarchicalNNClassifier(name="hierarchical_clf")
    >>> clf.load_data(X, y_hierarchy)  # y_hierarchy: (n_samples, n_levels)
    >>> clf.build_model()
    >>> clf.train()
    >>> predictions = clf.predict(X_test)
"""

__version__ = "0.1.0"
__author__ = "Bhavinkumar Rathava"
__email__ = "bhavinr9@gmail.com"

from nlp_templates.classifiers import (
    SimpleMulticlassClassifier,
    HierarchicalNNClassifier,
)
from nlp_templates.evaluation import (
    calculate_metrics,
    get_confusion_matrix,
    get_classification_report,
    plot_confusion_matrix,
    plot_metrics_comparison,
)
from nlp_templates.preprocessing import ConfigLoader

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    # Classifiers
    "SimpleMulticlassClassifier",
    "HierarchicalNNClassifier",
    # Evaluation
    "calculate_metrics",
    "get_confusion_matrix",
    "get_classification_report",
    "plot_confusion_matrix",
    "plot_metrics_comparison",
    # Preprocessing
    "ConfigLoader",
]
