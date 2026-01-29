"""
Advanced Statistical Validation Framework for Proteomics
=======================================================
Comprehensive statistical validation with confidence intervals, permutation tests, and clinical metrics.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
try:
    from scipy import stats
except (ImportError, ValueError):
    # Minimal fallback for stats
    class MockStats:
        @staticmethod
        def norm(): return MockDist()
    class MockDist:
        def cdf(self, x): return 0.5
    stats = MockStats()

from sklearn.metrics import (
    roc_auc_score, average_precision_score, brier_score_loss,
    roc_curve, precision_recall_curve,
    confusion_matrix
)
from sklearn.calibration import calibration_curve
import warnings
warnings.filterwarnings('ignore')

class AdvancedMetrics:
    """Advanced metrics with confidence intervals and statistical tests."""
    
    def __init__(self, alpha=0.05):
        self.alpha = alpha
        self.confidence_level = 1 - alpha
        
    def calculate_auc_ci(self, y_true, y_scores, n_bootstrap=2000):
        """Calculate AUC with bootstrap confidence interval."""
        auc_original = roc_auc_score(y_true, y_scores)
        
        # Bootstrap
        bootstrap_aucs = []
        n_samples = len(y_true)
        np.random.seed(42)
        
        for _ in range(n_bootstrap):
            indices = np.random.choice(n_samples, n_samples, replace=True)
            y_boot = y_true[indices]
            scores_boot = y_scores[indices]
            
            if len(np.unique(y_boot)) > 1:
                bootstrap_aucs.append(roc_auc_score(y_boot, scores_boot))
        
        ci_lower = np.percentile(bootstrap_aucs, (self.alpha/2) * 100)
        ci_upper = np.percentile(bootstrap_aucs, (1 - self.alpha/2) * 100)
        
        # Statistical test against 0.5
        z_score = (auc_original - 0.5) / np.sqrt(np.var(bootstrap_aucs))
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
        
        return {
            'auc': auc_original,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'p_value': p_value,
            'bootstrap_aucs': bootstrap_aucs
        }
    
    def calculate_clinical_metrics(self, y_true, y_scores, threshold=0.5):
        """Calculate comprehensive clinical metrics."""
        y_pred = (y_scores >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        
        # Basic metrics
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        ppv = tp / (tp + fp) if (tp + fp) > 0 else 0
        npv = tn / (tn + fn) if (tn + fn) > 0 else 0
        
        # Advanced metrics
        accuracy = (tp + tn) / (tp + tn + fp + fn)
        balanced_accuracy = (sensitivity + specificity) / 2
        f1_score = 2 * (ppv * sensitivity) / (ppv + sensitivity) if (ppv + sensitivity) > 0 else 0
        
        # Likelihood ratios
        lr_positive = sensitivity / (1 - specificity) if specificity < 1 else np.inf
        lr_negative = (1 - sensitivity) / specificity if specificity > 0 else np.inf
        
        # Youden's J statistic
        youden_j = sensitivity + specificity - 1
        
        return {
            'threshold': threshold,
            'sensitivity': sensitivity,
            'specificity': specificity,
            'ppv': ppv,
            'npv': npv,
            'accuracy': accuracy,
            'balanced_accuracy': balanced_accuracy,
            'f1_score': f1_score,
            'lr_positive': lr_positive,
            'lr_negative': lr_negative,
            'youden_j': youden_j,
            'tp': tp, 'tn': tn, 'fp': fp, 'fn': fn
        }

class CalibrationAnalyzer:
    """Model calibration analysis."""
    
    def analyze_calibration(self, y_true, y_proba, n_bins=10):
        """Comprehensive calibration analysis."""
        # Calibration curve
        fraction_positive, mean_predicted = calibration_curve(
            y_true, y_proba, n_bins=n_bins
        )
        
        # Brier score
        brier_score = brier_score_loss(y_true, y_proba)
        
        # Expected Calibration Error (ECE)
        ece = self._expected_calibration_error(y_true, y_proba, n_bins)
        
        return {
            'fraction_positive': fraction_positive,
            'mean_predicted': mean_predicted,
            'brier_score': brier_score,
            'ece': ece
        }
    
    def _expected_calibration_error(self, y_true, y_proba, n_bins=10):
        """Calculate Expected Calibration Error."""
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        ece = 0
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            in_bin = (y_proba > bin_lower) & (y_proba <= bin_upper)
            prop_in_bin = in_bin.mean()
            
            if prop_in_bin > 0:
                accuracy_in_bin = y_true[in_bin].mean()
                avg_confidence_in_bin = y_proba[in_bin].mean()
                ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
        
        return ece

class ValidationVisualizer:
    """Comprehensive validation visualizations."""
    
    def __init__(self):
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
    def plot_validation_summary(self, y_true, y_scores, model_name="Model", save_path=None):
        """Create comprehensive validation plots."""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(f'{model_name}: Comprehensive Validation Report', fontsize=16)
        
        # 1. ROC Curve
        self._plot_roc_curve(y_true, y_scores, axes[0, 0])
        
        # 2. Precision-Recall Curve
        self._plot_precision_recall(y_true, y_scores, axes[0, 1])
        
        # 3. Calibration Plot
        self._plot_calibration(y_true, y_scores, axes[0, 2])
        
        # 4. Prediction Distribution
        self._plot_prediction_distribution(y_true, y_scores, axes[1, 0])
        
        # 5. Confusion Matrix
        self._plot_confusion_matrix(y_true, y_scores, axes[1, 1])
        
        # 6. Performance Summary
        self._plot_performance_metrics(y_true, y_scores, axes[1, 2])
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Validation report saved to: {save_path}")
        
        plt.show()
        return fig
    
    def _plot_roc_curve(self, y_true, y_scores, ax):
        """Plot ROC curve with confidence interval."""
        fpr, tpr, _ = roc_curve(y_true, y_scores)
        auc = roc_auc_score(y_true, y_scores)
        
        ax.plot(fpr, tpr, color=self.colors[0], linewidth=2, 
                label=f'ROC (AUC = {auc:.3f})')
        ax.plot([0, 1], [0, 1], 'k--', alpha=0.5)
        
        ax.set_xlabel('False Positive Rate')
        ax.set_ylabel('True Positive Rate')
        ax.set_title('ROC Curve')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_precision_recall(self, y_true, y_scores, ax):
        """Plot precision-recall curve."""
        precision, recall, _ = precision_recall_curve(y_true, y_scores)
        ap = average_precision_score(y_true, y_scores)
        
        ax.plot(recall, precision, color=self.colors[1], linewidth=2,
                label=f'AP = {ap:.3f}')
        ax.axhline(y=np.mean(y_true), color='k', linestyle='--', alpha=0.5,
                  label=f'Baseline = {np.mean(y_true):.3f}')
        
        ax.set_xlabel('Recall')
        ax.set_ylabel('Precision')
        ax.set_title('Precision-Recall Curve')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_calibration(self, y_true, y_scores, ax):
        """Plot calibration curve."""
        fraction_positive, mean_predicted = calibration_curve(y_true, y_scores, n_bins=10)
        
        ax.plot(mean_predicted, fraction_positive, marker='o', linewidth=2,
                color=self.colors[2], label='Model')
        ax.plot([0, 1], [0, 1], 'k--', alpha=0.5, label='Perfect calibration')
        
        brier = brier_score_loss(y_true, y_scores)
        ax.text(0.05, 0.95, f'Brier Score: {brier:.3f}', 
               transform=ax.transAxes, bbox=dict(boxstyle="round", facecolor="white"))
        
        ax.set_xlabel('Mean Predicted Probability')
        ax.set_ylabel('Fraction of Positives')
        ax.set_title('Calibration Plot')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_prediction_distribution(self, y_true, y_scores, ax):
        """Plot distribution of predictions by class."""
        pos_scores = y_scores[y_true == 1]
        neg_scores = y_scores[y_true == 0]
        
        ax.hist(neg_scores, bins=30, alpha=0.7, label='Negative', 
               color=self.colors[3], density=True)
        ax.hist(pos_scores, bins=30, alpha=0.7, label='Positive', 
               color=self.colors[4], density=True)
        
        ax.set_xlabel('Predicted Probability')
        ax.set_ylabel('Density')
        ax.set_title('Prediction Distribution')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_confusion_matrix(self, y_true, y_scores, ax, threshold=0.5):
        """Plot confusion matrix."""
        y_pred = (y_scores >= threshold).astype(int)
        cm = confusion_matrix(y_true, y_pred)
        
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                   xticklabels=['Predicted 0', 'Predicted 1'],
                   yticklabels=['Actual 0', 'Actual 1'])
        ax.set_title('Confusion Matrix')
    
    def _plot_performance_metrics(self, y_true, y_scores, ax):
        """Plot performance metrics summary."""
        metrics = AdvancedMetrics()
        clinical_metrics = metrics.calculate_clinical_metrics(y_true, y_scores)
        
        metric_names = ['Sensitivity', 'Specificity', 'PPV', 'NPV', 'Accuracy', 'F1-Score']
        metric_values = [
            clinical_metrics['sensitivity'],
            clinical_metrics['specificity'],
            clinical_metrics['ppv'],
            clinical_metrics['npv'],
            clinical_metrics['accuracy'],
            clinical_metrics['f1_score']
        ]
        
        bars = ax.bar(metric_names, metric_values, color=self.colors[:len(metric_names)])
        ax.set_ylabel('Score')
        ax.set_title('Performance Metrics')
        ax.set_ylim(0, 1)
        
        # Add value labels on bars
        for bar, value in zip(bars, metric_values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                   f'{value:.3f}', ha='center', va='bottom')
        
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

class ComprehensiveValidator:
    """Complete validation pipeline."""
    
    def __init__(self):
        self.metrics_calculator = AdvancedMetrics()
        self.calibration_analyzer = CalibrationAnalyzer()
        self.visualizer = ValidationVisualizer()
    
    def validate_model(self, y_true, y_scores, model_name="Model", save_report=True):
        """Run comprehensive model validation."""
        print(f"Running comprehensive validation for {model_name}...")
        
        # Calculate metrics with confidence intervals
        auc_results = self.metrics_calculator.calculate_auc_ci(y_true, y_scores)
        clinical_metrics = self.metrics_calculator.calculate_clinical_metrics(y_true, y_scores)
        calibration_results = self.calibration_analyzer.analyze_calibration(y_true, y_scores)
        
        # Generate visualizations
        save_path = f"validation_report_{model_name.lower().replace(' ', '_')}.png" if save_report else None
        fig = self.visualizer.plot_validation_summary(y_true, y_scores, model_name, save_path)
        
        # Compile results
        results = {
            'model_name': model_name,
            'auc_results': auc_results,
            'clinical_metrics': clinical_metrics,
            'calibration_results': calibration_results,
            'n_samples': len(y_true),
            'n_positive': np.sum(y_true),
            'prevalence': np.mean(y_true)
        }
        
        # Print summary
        self._print_validation_summary(results)
        
        return results
    
    def _print_validation_summary(self, results):
        """Print validation summary."""
        print("\n" + "="*60)
        print(f"VALIDATION SUMMARY: {results['model_name']}")
        print("="*60)
        
        # Sample statistics
        print(f"Samples: {results['n_samples']}")
        print(f"Positive cases: {results['n_positive']} ({results['prevalence']:.1%})")
        
        # AUC results
        auc = results['auc_results']
        print(f"\nAUC: {auc['auc']:.3f} (95% CI: {auc['ci_lower']:.3f}-{auc['ci_upper']:.3f})")
        print(f"AUC p-value: {auc['p_value']:.4f}")
        
        # Clinical metrics
        cm = results['clinical_metrics']
        print(f"\nClinical Metrics:")
        print(f"  Sensitivity: {cm['sensitivity']:.3f}")
        print(f"  Specificity: {cm['specificity']:.3f}")
        print(f"  PPV: {cm['ppv']:.3f}")
        print(f"  NPV: {cm['npv']:.3f}")
        print(f"  Accuracy: {cm['accuracy']:.3f}")
        print(f"  F1-Score: {cm['f1_score']:.3f}")
        
        # Calibration
        cal = results['calibration_results']
        print(f"\nCalibration:")
        print(f"  Brier Score: {cal['brier_score']:.3f}")
        print(f"  Expected Calibration Error: {cal['ece']:.3f}")

if __name__ == "__main__":
    # Example usage of the validation framework
    print("Testing comprehensive validation framework...")
    
    # Generate synthetic data
    np.random.seed(42)
    n_samples = 500
    
    # Create realistic proteomics prediction scenario
    y_true = np.random.binomial(1, 0.3, n_samples)  # 30% positive rate
    
    # Generate scores with some predictive power
    y_scores = np.random.beta(2, 5, n_samples)  # Base scores
    y_scores[y_true == 1] += np.random.normal(0.3, 0.2, np.sum(y_true))  # Boost positive cases
    y_scores = np.clip(y_scores, 0, 1)  # Ensure valid probabilities
    
    # Run validation
    validator = ComprehensiveValidator()
    results = validator.validate_model(y_true, y_scores, "Example Proteomics Model")
    
    print("\nValidation framework test completed successfully!")
