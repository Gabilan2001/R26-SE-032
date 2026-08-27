# Model Results & Limitations — Leaf EfficientNet-B0

## Reported performance (use these numbers)

| Metric | Value |
|--------|-------|
| **Test accuracy** | **81.42%** |
| Test precision | 84.29% |
| Test recall | 81.42% |
| **Test F1** | **81.60%** |
| Best validation accuracy | 86.02% |

Do **not** cite training accuracy (**98.79%**) as the model performance metric.

## Pseudo-label limitation

Labels are **relative pseudo-severity labels** from YOLO-derived affected-area information
(P40 threshold ≈ 0.687), not expert ground truth.

- LOW: 2,765  
- HIGH: 4,141  
- Total: 6,906  

## Overfitting / generalization gap (research note)

Train accuracy (98.79%) ≫ test accuracy (81.42%) indicates a generalization gap.

### Future improvement TODO (do not fake accuracy)

- Stronger data augmentation  
- Dropout / weight decay  
- Early stopping + LR scheduling  
- Confusion matrix and class-wise analysis  
- Grad-CAM / error analysis  
- Prefer expert-labelled severity data when available  

Do not modify labels only to obtain higher accuracy.

## Model replacement

```env
LEAF_SEVERITY_MODEL_PATH=/path/to/new_efficientnet_checkpoint.pth
```

Same inference interface → same observation system → same frontend.

## Fruit

Pending researcher CNN. Configure `FRUIT_SEVERITY_MODEL_PATH` when ready.
