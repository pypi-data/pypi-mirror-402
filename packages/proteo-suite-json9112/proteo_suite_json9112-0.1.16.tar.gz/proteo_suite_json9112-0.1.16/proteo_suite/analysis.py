"""
Advanced Proteomics Analysis for Medical Outcomes Prediction
Enhanced with state-of-the-art ML/AI tools and mass spectrometry signal processing
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import roc_auc_score, classification_report
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test
import warnings
warnings.filterwarnings('ignore')

# Advanced ML libraries
try:
    import xgboost as xgb
    import lightgbm as lgb
    import catboost as cb
    from sklearn.neural_network import MLPRegressor
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, Matern
    print("Advanced ML libraries loaded successfully")
except (ImportError, ValueError) as e:
    print(f"Some advanced libraries not available: {e}")

# Signal processing libraries

# Signal processing libraries
try:
    from scipy.signal import find_peaks, savgol_filter, butter, filtfilt
    from scipy.stats import zscore, pearsonr
    HAS_SCIPY_ANALYSIS = True
except (ImportError, ValueError) as e:
    HAS_SCIPY_ANALYSIS = False
    print(f"Warning: Scipy functions missing in analysis module: {e}")
    # Fallback definitions
    def find_peaks(x, **kwargs): return (np.array([]), {})
    def savgol_filter(x, *args, **kwargs): return x
    def butter(*args, **kwargs): return (np.array([1.]), np.array([1.]))
    def filtfilt(b, a, x, *args, **kwargs): return x
    def zscore(a, *args, **kwargs): return a
    def pearsonr(x, y): return (0.0, 1.0)
from sklearn.decomposition import PCA, FastICA, TruncatedSVD
from sklearn.manifold import TSNE
try:
    from umap import UMAP
except ImportError:
    UMAP = None
    print("Warning: UMAP not available (install umap-learn)")

from sklearn.cluster import DBSCAN, KMeans

# Deep learning (if available)
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
    print("PyTorch available for deep learning")
except ImportError:
    TORCH_AVAILABLE = False
    print("PyTorch not available - using traditional ML only")

class AdvancedProteomicsAnalyzer:
    """
    Advanced proteomics analyzer with state-of-the-art signal processing and ML
    """
    
    def __init__(self, data_path="merged_data.csv", outcomes_path="days_cols_4.csv"):
        self.data_path = data_path
        self.outcomes_path = outcomes_path
        # self.load_data() # Defer loading until explicitly called or needed
        self.models = {}
        self.results = {}
        
    def load_data(self):
        """Load and preprocess the proteomics data"""
        print("Loading proteomics data...")
        
        # Load main dataset
        self.df = pd.read_csv(self.data_path)
        self.df.replace(['', ' ', 'NA', 'NaN', 'N/A', '--', None], np.nan, inplace=True)
        
        # Load outcomes
        self.outcomes_df = pd.read_csv(self.outcomes_path, index_col=0)
        
        # Separate features and outcomes
        self.samples = self.df.iloc[:, 0]
        self.X_raw = self.df.iloc[:, 1:-14]  # Mass spec features
        self.y_outcomes = self.outcomes_df
        
        # Get numeric columns only
        numeric_cols = self.X_raw.select_dtypes(include=[np.number]).columns
        self.X_raw = self.X_raw[numeric_cols]
        
        print(f"Loaded {len(self.df)} samples with {len(self.X_raw.columns)} mass spec features")
        print(f"Outcomes: {list(self.y_outcomes.columns)}")
        
    def advanced_signal_processing(self):
        """
        Apply advanced signal processing techniques to mass spectrometry data
        """
        print("Applying advanced signal processing...")
        if not hasattr(self, 'X_raw'):
             self.load_data()

        # Fill missing values
        X_filled = self.X_raw.fillna(0)
        
        # 1. Noise reduction using Savitzky-Golay filter
        print("  - Applying Savitzky-Golay smoothing...")
        X_smoothed = np.apply_along_axis(
            lambda x: savgol_filter(x, window_length=min(11, len(x)//2*2+1), polyorder=3),
            axis=1, arr=X_filled.values
        )
        
        # 2. Baseline correction using asymmetric least squares
        print("  - Baseline correction...")
        X_baseline_corrected = self._baseline_correction(X_smoothed)
        
        # 3. Peak detection and enhancement
        print("  - Peak detection and enhancement...")
        X_peak_enhanced = self._enhance_peaks(X_baseline_corrected)
        
        # 4. Normalization strategies
        print("  - Multi-level normalization...")
        X_normalized = self._multi_level_normalization(X_peak_enhanced)
        
        # 5. Feature engineering from signal characteristics
        print("  - Signal feature engineering...")
        X_signal_features = self._extract_signal_features(X_normalized)
        
        # Combine original and engineered features
        feature_names = list(self.X_raw.columns) + [f"signal_feat_{i}" for i in range(X_signal_features.shape[1])]
        self.X_processed = pd.DataFrame(
            np.hstack([X_normalized, X_signal_features]),
            columns=feature_names,
            index=self.X_raw.index
        )
        
        print(f"Signal processing complete. Features expanded from {self.X_raw.shape[1]} to {self.X_processed.shape[1]}")
        
    def _baseline_correction(self, X, lam=1e6, p=0.01, niter=10):
        """Asymmetric Least Squares baseline correction"""
        X_corrected = np.zeros_like(X)
        
        for i in range(X.shape[0]):
            y = X[i, :]
            L = len(y)
            D = np.diff(np.eye(L), 2, axis=0)
            w = np.ones(L)
            
            for _ in range(niter):
                W = np.diag(w)
                Z = W + lam * D.T @ D
                z = np.linalg.solve(Z, w * y)
                w = p * (y > z) + (1 - p) * (y < z)
            
            X_corrected[i, :] = y - z
            
        return X_corrected
    
    def _enhance_peaks(self, X):
        """Enhance peaks using advanced signal processing"""
        X_enhanced = np.zeros_like(X)
        
        for i in range(X.shape[0]):
            signal_data = X[i, :]
            
            # Find peaks
            peaks, properties = find_peaks(
                signal_data, 
                height=np.std(signal_data),
                distance=5,
                prominence=np.std(signal_data) * 0.5
            )
            
            # Enhance peak regions
            enhanced_signal = signal_data.copy()
            for peak in peaks:
                # Gaussian enhancement around peaks
                window = 10
                start = max(0, peak - window)
                end = min(len(signal_data), peak + window)
                
                # Apply Gaussian weighting
                x = np.arange(start, end)
                gaussian_weight = np.exp(-0.5 * ((x - peak) / (window/3))**2)
                enhanced_signal[start:end] *= (1 + 0.5 * gaussian_weight)
            
            X_enhanced[i, :] = enhanced_signal
            
        return X_enhanced
    
    def _multi_level_normalization(self, X):
        """Apply multiple normalization strategies"""
        # 1. Robust scaling (less sensitive to outliers)
        scaler = RobustScaler()
        X_robust = scaler.fit_transform(X)
        
        # 2. Z-score normalization per sample (row-wise)
        X_zscore = zscore(X_robust, axis=1)
        
        # 3. Quantile normalization
        X_quantile = self._quantile_normalize(X_zscore)
        
        return X_quantile
    
    def _quantile_normalize(self, X):
        """Quantile normalization"""
        # Sort each column
        sorted_indices = np.argsort(X, axis=0)
        sorted_X = np.sort(X, axis=0)
        
        # Calculate mean of each rank
        mean_ranks = np.mean(sorted_X, axis=1)
        
        # Assign mean ranks back to original positions
        X_normalized = np.zeros_like(X)
        for col in range(X.shape[1]):
            X_normalized[sorted_indices[:, col], col] = mean_ranks
            
        return X_normalized
    
    def _extract_signal_features(self, X):
        """Extract advanced signal characteristics as features"""
        n_samples = X.shape[0]
        features = []
        
        for i in range(n_samples):
            signal_data = X[i, :]
            
            # Statistical features
            feat = [
                np.mean(signal_data),
                np.std(signal_data),
                np.median(signal_data),
                np.percentile(signal_data, 25),
                np.percentile(signal_data, 75),
                np.max(signal_data) - np.min(signal_data),  # Range
                np.sum(np.abs(np.diff(signal_data))),  # Total variation
            ]
            
            # Spectral features
            freqs, psd = signal.periodogram(signal_data)
            feat.extend([
                np.sum(psd),  # Total power
                freqs[np.argmax(psd)],  # Dominant frequency
                np.sum(psd * freqs) / np.sum(psd),  # Spectral centroid
            ])
            
            # Peak characteristics
            peaks, properties = find_peaks(signal_data, height=np.std(signal_data))
            feat.extend([
                len(peaks),  # Number of peaks
                np.mean(properties['peak_heights']) if len(peaks) > 0 else 0,
                np.std(properties['peak_heights']) if len(peaks) > 0 else 0,
            ])
            
            features.append(feat)
            
        return np.array(features)
    
    def advanced_feature_selection(self, n_features=1000):
        """
        Advanced feature selection using multiple strategies
        """
        print("Performing advanced feature selection...")
        
        # 1. Variance-based filtering
        variances = self.X_processed.var()
        high_var_features = variances.nlargest(n_features * 2).index
        
        # 2. Correlation-based filtering (remove highly correlated features)
        X_high_var = self.X_processed[high_var_features]
        corr_matrix = X_high_var.corr().abs()
        
        # Find pairs of highly correlated features
        upper_tri = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )
        
        # Remove features with correlation > 0.95
        to_drop = [column for column in upper_tri.columns if any(upper_tri[column] > 0.95)]
        X_filtered = X_high_var.drop(columns=to_drop)
        
        # 3. Mutual information-based selection
        from sklearn.feature_selection import mutual_info_regression
        
        # Use first outcome for feature selection (can be improved)
        y_sample = self.y_outcomes.iloc[:, 0].fillna(0)
        
        mi_scores = mutual_info_regression(X_filtered.fillna(0), y_sample)
        mi_features = X_filtered.columns[np.argsort(mi_scores)[-n_features:]]
        
        self.X_selected = X_filtered[mi_features]
        
        print(f"Feature selection complete: {self.X_processed.shape[1]} -> {self.X_selected.shape[1]} features")
        
    def build_advanced_models(self):
        """
        Build ensemble of advanced ML models
        """
        print("Building advanced ML models...")
        
        self.model_configs = {
            'XGBoost': {
                'model': xgb.XGBRegressor(
                    n_estimators=200,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42
                ),
                'type': 'tree'
            },
            'LightGBM': {
                'model': lgb.LGBMRegressor(
                    n_estimators=200,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    verbose=-1
                ),
                'type': 'tree'
            },
            'CatBoost': {
                'model': cb.CatBoostRegressor(
                    iterations=200,
                    depth=6,
                    learning_rate=0.1,
                    random_seed=42,
                    verbose=False
                ),
                'type': 'tree'
            },
            'Neural_Network': {
                'model': MLPRegressor(
                    hidden_layer_sizes=(256, 128, 64),
                    activation='relu',
                    solver='adam',
                    alpha=0.001,
                    max_iter=500,
                    random_state=42
                ),
                'type': 'neural'
            },
            'Gaussian_Process': {
                'model': GaussianProcessRegressor(
                    kernel=RBF(length_scale=1.0) + Matern(length_scale=1.0),
                    random_state=42
                ),
                'type': 'gaussian'
            }
        }
        
        if TORCH_AVAILABLE:
            self.model_configs['Deep_Neural_Network'] = {
                'model': self._create_deep_model(),
                'type': 'deep'
            }
        
    def _create_deep_model(self):
        """Create a deep neural network model using PyTorch"""
        class DeepProteomicsNet(nn.Module):
            def __init__(self, input_size):
                super(DeepProteomicsNet, self).__init__()
                self.layers = nn.Sequential(
                    nn.Linear(input_size, 512),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(512, 256),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(256, 128),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(128, 64),
                    nn.ReLU(),
                    nn.Linear(64, 1)
                )
                
            def forward(self, x):
                return self.layers(x)
        
        return DeepProteomicsNet(self.X_selected.shape[1])
    
    def train_and_evaluate_models(self):
        """
        Train and evaluate all models for each outcome
        """
        print("Training and evaluating models for all outcomes...")
        
        self.results = {}
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        
        for outcome in self.y_outcomes.columns:
            print(f"\nProcessing outcome: {outcome}")
            
            # Prepare target variable
            y = self.y_outcomes[outcome].fillna(0)
            
            # Create binary classification target for stratification
            y_binary = (y > 0).astype(int)
            
            # Skip if no positive cases
            if y_binary.sum() == 0:
                print(f"  Skipping {outcome} - no positive cases")
                continue
                
            self.results[outcome] = {}
            
            # Prepare data
            X_clean = self.X_selected.fillna(0)
            
            for model_name, model_config in self.model_configs.items():
                print(f"  Training {model_name}...")
                
                try:
                    if model_config['type'] == 'deep' and TORCH_AVAILABLE:
                        scores = self._train_deep_model(X_clean, y, cv)
                    else:
                        scores = cross_val_score(
                            model_config['model'], 
                            X_clean, 
                            y, 
                            cv=cv, 
                            scoring='neg_mean_squared_error'
                        )
                    
                    self.results[outcome][model_name] = {
                        'cv_scores': scores,
                        'mean_score': np.mean(scores),
                        'std_score': np.std(scores)
                    }
                    
                    print(f"    {model_name}: {np.mean(scores):.4f} ± {np.std(scores):.4f}")
                    
                except Exception as e:
                    print(f"    Error training {model_name}: {e}")
                    continue
    
    def _train_deep_model(self, X, y, cv):
        """Train deep neural network with cross-validation"""
        scores = []
        
        for train_idx, val_idx in cv.split(X, (y > 0).astype(int)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # Convert to tensors
            X_train_tensor = torch.FloatTensor(X_train.values)
            y_train_tensor = torch.FloatTensor(y_train.values).unsqueeze(1)
            X_val_tensor = torch.FloatTensor(X_val.values)
            y_val_tensor = torch.FloatTensor(y_val.values).unsqueeze(1)
            
            # Create model
            model = self._create_deep_model()
            criterion = nn.MSELoss()
            optimizer = optim.Adam(model.parameters(), lr=0.001)
            
            # Training loop
            model.train()
            for epoch in range(100):
                optimizer.zero_grad()
                outputs = model(X_train_tensor)
                loss = criterion(outputs, y_train_tensor)
                loss.backward()
                optimizer.step()
            
            # Evaluation
            model.eval()
            with torch.no_grad():
                val_outputs = model(X_val_tensor)
                val_loss = criterion(val_outputs, y_val_tensor)
                scores.append(-val_loss.item())  # Negative for consistency with sklearn
        
        return np.array(scores)
    
    def create_survival_analysis(self):
        """
        Advanced survival analysis for time-to-event outcomes
        """
        print("Performing advanced survival analysis...")
        
        survival_outcomes = [col for col in self.y_outcomes.columns 
                           if 'time' in col.lower() or 'day' in col.lower()]
        
        self.survival_results = {}
        
        for outcome in survival_outcomes:
            print(f"\nSurvival analysis for {outcome}")
            
            # Prepare survival data
            time_data = self.y_outcomes[outcome].fillna(0)
            event_data = (time_data > 0).astype(int)
            
            if event_data.sum() == 0:
                continue
            
            # Get best model predictions for risk stratification
            best_model_name = self._get_best_model(outcome)
            if best_model_name is None:
                continue
                
            # Train best model on full data
            X_clean = self.X_selected.fillna(0)
            model = self.model_configs[best_model_name]['model']
            
            if self.model_configs[best_model_name]['type'] != 'deep':
                model.fit(X_clean, time_data)
                risk_scores = model.predict(X_clean)
            else:
                # For deep models, use a simpler approach
                risk_scores = np.random.randn(len(time_data))  # Placeholder
            
            # Risk stratification
            risk_threshold = np.median(risk_scores)
            high_risk = risk_scores >= risk_threshold
            low_risk = risk_scores < risk_threshold
            
            # Kaplan-Meier analysis
            kmf = KaplanMeierFitter()
            
            # Fit survival curves
            kmf_high = KaplanMeierFitter()
            kmf_low = KaplanMeierFitter()
            
            # Handle censoring (assume all events are observed for now)
            kmf_high.fit(time_data[high_risk], event_data[high_risk], label='High Risk')
            kmf_low.fit(time_data[low_risk], event_data[low_risk], label='Low Risk')
            
            # Log-rank test
            try:
                logrank_result = logrank_test(
                    time_data[high_risk], time_data[low_risk],
                    event_data[high_risk], event_data[low_risk]
                )
                p_value = logrank_result.p_value
            except:
                p_value = np.nan
            
            self.survival_results[outcome] = {
                'kmf_high': kmf_high,
                'kmf_low': kmf_low,
                'p_value': p_value,
                'risk_scores': risk_scores,
                'high_risk_mask': high_risk
            }
    
    def _get_best_model(self, outcome):
        """Get the best performing model for an outcome"""
        if outcome not in self.results:
            return None
            
        best_score = -np.inf
        best_model = None
        
        for model_name, results in self.results[outcome].items():
            if results['mean_score'] > best_score:
                best_score = results['mean_score']
                best_model = model_name
                
        return best_model
    
    def create_comprehensive_visualizations(self):
        """
        Create comprehensive visualizations of results
        """
        print("Creating comprehensive visualizations...")
        
        # 1. Model performance comparison
        self._plot_model_performance()
        
        # 2. Survival curves
        self._plot_survival_curves()
        
        # 3. Feature importance analysis
        self._plot_feature_importance()
        
        # 4. Dimensionality reduction visualization
        self._plot_dimensionality_reduction()
        
    def _plot_model_performance(self):
        """Plot model performance comparison"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        axes = axes.flatten()
        
        outcomes = list(self.results.keys())[:4]  # First 4 outcomes
        
        for idx, outcome in enumerate(outcomes):
            if idx >= 4:
                break
                
            models = list(self.results[outcome].keys())
            scores = [self.results[outcome][model]['mean_score'] for model in models]
            errors = [self.results[outcome][model]['std_score'] for model in models]
            
            axes[idx].barh(models, scores, xerr=errors, capsize=5)
            axes[idx].set_title(f'Model Performance: {outcome}')
            axes[idx].set_xlabel('Cross-Validation Score')
            axes[idx].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('model_performance_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def _plot_survival_curves(self):
        """Plot survival curves"""
        if not hasattr(self, 'survival_results'):
            return
            
        n_outcomes = len(self.survival_results)
        if n_outcomes == 0:
            return
            
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        axes = axes.flatten()
        
        for idx, (outcome, results) in enumerate(self.survival_results.items()):
            if idx >= 4:
                break
                
            ax = axes[idx]
            
            # Plot survival curves
            results['kmf_high'].plot_survival_function(ax=ax)
            results['kmf_low'].plot_survival_function(ax=ax)
            
            ax.set_title(f'Survival Analysis: {outcome}\np-value: {results["p_value"]:.4f}')
            ax.set_xlabel('Time (days)')
            ax.set_ylabel('Survival Probability')
            ax.grid(True, alpha=0.3)
            ax.legend()
        
        plt.tight_layout()
        plt.savefig('survival_curves.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def _plot_feature_importance(self):
        """Plot feature importance from tree-based models"""
        # Get feature importance from XGBoost model (if available)
        outcome = list(self.results.keys())[0]  # Use first outcome
        
        if 'XGBoost' in self.model_configs:
            # Train XGBoost on full data to get feature importance
            X_clean = self.X_selected.fillna(0)
            y = self.y_outcomes[outcome].fillna(0)
            
            model = self.model_configs['XGBoost']['model']
            model.fit(X_clean, y)
            
            # Get feature importance
            importance = model.feature_importances_
            feature_names = self.X_selected.columns
            
            # Sort by importance
            sorted_idx = np.argsort(importance)[-20:]  # Top 20 features
            
            plt.figure(figsize=(10, 8))
            plt.barh(range(len(sorted_idx)), importance[sorted_idx])
            plt.yticks(range(len(sorted_idx)), [feature_names[i] for i in sorted_idx])
            plt.xlabel('Feature Importance')
            plt.title(f'Top 20 Feature Importance: {outcome}')
            plt.tight_layout()
            plt.savefig('feature_importance.png', dpi=300, bbox_inches='tight')
            plt.show()
    
    def _plot_dimensionality_reduction(self):
        """Plot dimensionality reduction visualization"""
        X_clean = self.X_selected.fillna(0)
        
        # Apply different dimensionality reduction techniques
        techniques = {
            'PCA': PCA(n_components=2, random_state=42),
            'TSNE': TSNE(n_components=2, random_state=42, perplexity=30),
        }
        
        # Try UMAP if available
        try:
            techniques['UMAP'] = UMAP(n_components=2, random_state=42)
        except:
            pass
        
        fig, axes = plt.subplots(1, len(techniques), figsize=(5*len(techniques), 5))
        if len(techniques) == 1:
            axes = [axes]
        
        # Use first outcome for coloring
        outcome = list(self.y_outcomes.columns)[0]
        y_color = self.y_outcomes[outcome].fillna(0)
        
        for idx, (name, technique) in enumerate(techniques.items()):
            try:
                X_reduced = technique.fit_transform(X_clean)
                
                scatter = axes[idx].scatter(
                    X_reduced[:, 0], X_reduced[:, 1], 
                    c=y_color, cmap='viridis', alpha=0.6
                )
                axes[idx].set_title(f'{name} Visualization')
                axes[idx].set_xlabel('Component 1')
                axes[idx].set_ylabel('Component 2')
                plt.colorbar(scatter, ax=axes[idx])
                
            except Exception as e:
                print(f"Error with {name}: {e}")
                axes[idx].text(0.5, 0.5, f'Error: {name}', 
                              transform=axes[idx].transAxes, ha='center')
        
        plt.tight_layout()
        plt.savefig('dimensionality_reduction.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_comprehensive_report(self):
        """Generate a comprehensive analysis report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE PROTEOMICS ANALYSIS REPORT")
        print("="*80)
        
        print(f"\nDataset Overview:")
        print(f"- Samples: {len(self.df)}")
        print(f"- Original features: {self.X_raw.shape[1]}")
        print(f"- Processed features: {self.X_processed.shape[1]}")
        print(f"- Selected features: {self.X_selected.shape[1]}")
        print(f"- Outcomes analyzed: {len(self.y_outcomes.columns)}")
        
        print(f"\nOutcomes Summary:")
        for outcome in self.y_outcomes.columns:
            y = self.y_outcomes[outcome].fillna(0)
            n_events = (y > 0).sum()
            event_rate = n_events / len(y) * 100
            print(f"- {outcome}: {n_events} events ({event_rate:.1f}%)")
        
        print(f"\nModel Performance Summary:")
        for outcome in self.results:
            print(f"\n{outcome}:")
            for model_name, results in self.results[outcome].items():
                print(f"  {model_name}: {results['mean_score']:.4f} ± {results['std_score']:.4f}")
        
        if hasattr(self, 'survival_results'):
            print(f"\nSurvival Analysis Summary:")
            for outcome, results in self.survival_results.items():
                print(f"- {outcome}: p-value = {results['p_value']:.4f}")
        
        print("\n" + "="*80)
    
    def run_complete_analysis(self):
        """Run the complete advanced analysis pipeline"""
        print("Starting comprehensive proteomics analysis...")
        
        # 1. Advanced signal processing
        self.advanced_signal_processing()
        
        # 2. Feature selection
        self.advanced_feature_selection()
        
        # 3. Build models
        self.build_advanced_models()
        
        # 4. Train and evaluate
        self.train_and_evaluate_models()
        
        # 5. Survival analysis
        self.create_survival_analysis()
        
        # 6. Visualizations
        self.create_comprehensive_visualizations()
        
        # 7. Generate report
        self.generate_comprehensive_report()
        
        print("\nAnalysis complete! Check generated plots and results.")

if __name__ == "__main__":
    # Initialize and run analysis
    analyzer = AdvancedProteomicsAnalyzer()
    analyzer.run_complete_analysis()
