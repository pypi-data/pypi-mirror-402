"""Generate sample plots to demonstrate the hmbp plotting module."""

import numpy as np
import hmbp

np.random.seed(42)

# 1. Line plot
fig, ax = hmbp.new_figure()
x = np.linspace(0, 10, 100)
hmbp.line_plot(np.sin(x), x, label="Model A")
hmbp.line_plot(np.cos(x), x, label="Model B", cmap=hmbp.CMAP_ALT)
hmbp.set_labels("Training Loss Over Time", "Epoch", "Loss")
hmbp.save("figures/01_line_plot.png")

# 2. Scatter plot
fig, ax = hmbp.new_figure()
x = np.random.randn(200)
y = 0.5 * x + np.random.randn(200) * 0.3
hmbp.scatter_plot(x, y, c=y, label="Samples")
hmbp.set_labels("Feature Correlation", "Feature A", "Feature B")
hmbp.save("figures/02_scatter_plot.png")

# 3. Histogram
fig, ax = hmbp.new_figure()
data = np.concatenate([np.random.randn(500), np.random.randn(300) + 3])
hmbp.histogram(data, bins=40)
hmbp.set_labels("Score Distribution", "Score", "Count")
hmbp.save("figures/03_histogram.png")

# 4. Bar plot
fig, ax = hmbp.new_figure()
models = ["Random Forest", "XGBoost", "Neural Net", "SVM", "LogReg"]
scores = [0.92, 0.95, 0.91, 0.88, 0.85]
hmbp.bar_plot(scores, models)
hmbp.set_labels("Model Comparison", "", "F1 Score")
hmbp.save("figures/04_bar_plot.png")

# 5. Box plot
fig, ax = hmbp.new_figure()
data = [np.random.randn(100) + i * 0.5 for i in range(4)]
hmbp.box_plot(data, ["Model A", "Model B", "Model C", "Model D"])
hmbp.set_labels("Score Distribution by Model", "", "Score")
hmbp.save("figures/05_box_plot.png")

# 6. Violin plot
fig, ax = hmbp.new_figure()
data = [np.random.randn(100) * (i + 1) * 0.3 for i in range(4)]
hmbp.violin_plot(data, ["Small", "Medium", "Large", "XL"])
hmbp.set_labels("Prediction Variance by Model Size", "", "Prediction Error")
hmbp.save("figures/06_violin_plot.png")

# 7. Heatmap (correlation matrix)
fig, ax = hmbp.new_figure()
corr = np.random.randn(6, 6)
corr = (corr + corr.T) / 2
np.fill_diagonal(corr, 1)
features = ["feat_1", "feat_2", "feat_3", "feat_4", "feat_5", "feat_6"]
hmbp.heatmap(corr, xticklabels=features, yticklabels=features,
             colorbar_label="Correlation", center_zero=True, annot=True)
hmbp.set_labels("Feature Correlation Matrix", "", "")
hmbp.save("figures/07_heatmap.png")

# 8. Line plot with error
fig, ax = hmbp.new_figure()
x = np.arange(10)
y = np.exp(-x * 0.3) + 0.1
yerr = 0.05 + 0.02 * np.random.randn(10)
hmbp.line_plot_with_error(y, np.abs(yerr), x, label="Mean +/- Std")
hmbp.set_labels("Convergence with Uncertainty", "Iteration", "Loss")
hmbp.save("figures/08_line_with_error.png")

# 9. Confusion matrix
fig, ax = hmbp.new_figure()
cm = np.array([[85, 10, 5], [8, 82, 10], [4, 12, 84]])
hmbp.confusion_matrix(cm, class_names=["Cat", "Dog", "Bird"], normalize=True)
hmbp.set_labels("Classification Results", "", "")
hmbp.save("figures/09_confusion_matrix.png")

# 10. ROC curve
fig, ax = hmbp.new_figure()
fpr1 = np.linspace(0, 1, 100)
tpr1 = np.sqrt(fpr1)  # Good model
tpr2 = fpr1 ** 2 + fpr1 * 0.5  # Mediocre model
tpr2 = np.clip(tpr2, 0, 1)
hmbp.roc_curve(fpr1, tpr1, auc=0.92, label="XGBoost")
hmbp.roc_curve(fpr1, tpr2, auc=0.71, label="Baseline", cmap=hmbp.CMAP_ALT)
hmbp.set_labels("ROC Comparison", "", "")
hmbp.save("figures/10_roc_curve.png")

# 11. Precision-Recall curve
fig, ax = hmbp.new_figure()
recall = np.linspace(0, 1, 100)
precision1 = 1 - 0.3 * recall ** 2
precision2 = 1 - 0.6 * recall
hmbp.precision_recall_curve(precision1, recall, ap=0.89, label="Model A")
hmbp.precision_recall_curve(precision2, recall, ap=0.72, label="Model B", cmap=hmbp.CMAP_ALT)
hmbp.set_labels("Precision-Recall Comparison", "", "")
hmbp.save("figures/11_pr_curve.png")

# 12. Residual plot
fig, ax = hmbp.new_figure()
y_pred = np.linspace(0, 10, 100)
y_true = y_pred + np.random.randn(100) * 0.5
hmbp.residual_plot(y_true, y_pred)
hmbp.set_labels("Residual Analysis", "", "")
hmbp.save("figures/12_residual_plot.png")

# 13. Learning curve
fig, ax = hmbp.new_figure()
sizes = np.array([100, 200, 500, 1000, 2000, 5000])
train_scores = np.column_stack([
    0.99 - 0.1 * np.exp(-sizes / 500) + np.random.randn(6) * 0.01
    for _ in range(5)
])
val_scores = np.column_stack([
    0.85 + 0.1 * (1 - np.exp(-sizes / 1000)) + np.random.randn(6) * 0.02
    for _ in range(5)
])
hmbp.learning_curve(train_scores, val_scores, sizes, metric_name="Accuracy")
hmbp.set_labels("Learning Curve", "", "")
hmbp.save("figures/13_learning_curve.png")

# 14. Metric comparison
fig, ax = hmbp.new_figure()
metrics = {
    "Accuracy": 0.94,
    "Precision": 0.91,
    "Recall": 0.88,
    "F1": 0.89,
    "AUC": 0.96
}
hmbp.metric_comparison(metrics)
hmbp.set_labels("Model Metrics", "", "")
hmbp.save("figures/14_metric_comparison.png")

# 15. Histogram overlay
fig, ax = hmbp.new_figure()
data1 = np.random.randn(500) * 0.8
data2 = np.random.randn(500) * 1.2 + 1.5
data3 = np.random.randn(500) * 0.6 + 3
hmbp.histogram_overlay([data1, data2, data3], labels=["MLP", "Attention", "Ground Truth"], bins=30)
hmbp.set_labels("Score Distributions by Model", "Score", "Count")
hmbp.save("figures/15_histogram_overlay.png")

# 16. Multi-line plot with noisy data and smoothing
fig, ax = hmbp.new_figure()
x = np.arange(100)
y1 = np.exp(-x * 0.03) + np.random.randn(100) * 0.08
y2 = np.exp(-x * 0.025) * 0.9 + np.random.randn(100) * 0.08
y3 = np.exp(-x * 0.035) * 1.1 + np.random.randn(100) * 0.08
hmbp.multi_line_plot([y1, y2, y3], x, labels=["Adam", "SGD", "AdamW"], smooth=0.9)
hmbp.set_labels("Training Loss Comparison (Smoothed)", "Epoch", "Loss")
hmbp.save("figures/16_multi_line.png")

# 17. Raw vs smoothed comparison
import matplotlib.pyplot as plt
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
x = np.arange(100)
y = np.exp(-x * 0.03) + np.random.randn(100) * 0.15
hmbp.line_plot(y, x, label="Raw", ax=ax1, fill=False)
hmbp.set_labels("Raw Training Curve", "Epoch", "Loss", ax=ax1)
hmbp.line_plot(y, x, label="Smoothed (0.9)", ax=ax2, fill=False, smooth=0.9)
hmbp.set_labels("EMA Smoothed (weight=0.9)", "Epoch", "Loss", ax=ax2)
hmbp.save("figures/17_smoothing_comparison.png")

print("Generated 17 sample plots in figures/")
