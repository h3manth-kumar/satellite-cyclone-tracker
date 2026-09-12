"""Grad-CAM (Gradient-weighted Class Activation Mapping) for Cyclone Pattern Explainability."""

import io
import base64
from typing import Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
import matplotlib.cm as cm


class GradCAM:
    """
    Computes Grad-CAM saliency heatmaps highlighting cyclone spiral bands and eye structures.
    """
    def __init__(self, model: nn.Module, target_layer: Optional[nn.Module] = None):
        self.model = model
        self.target_layer = target_layer or model.get_last_conv_layer()
        self.gradients: Optional[torch.Tensor] = None
        self.activations: Optional[torch.Tensor] = None
        self._hooks = []
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()

        self._hooks.append(self.target_layer.register_forward_hook(forward_hook))
        self._hooks.append(self.target_layer.register_full_backward_hook(backward_hook))

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        target_class_idx: Optional[int] = None,
        target_type: str = "classification",  # 'classification' or 'detection'
    ) -> np.ndarray:
        """
        Generates 2D normalized heatmap [H, W] in range [0, 1].
        """
        self.model.eval()
        self.model.zero_grad()

        # Enable gradient computation for Grad-CAM even in eval mode
        input_tensor = input_tensor.clone().requires_grad_(True)
        outputs = self.model(input_tensor)

        if target_type == "detection":
            score = outputs["detection_logit"][0, 0]
        else:
            class_logits = outputs["class_logits"]
            if target_class_idx is None:
                target_class_idx = int(class_logits.argmax(dim=-1).item())
            score = class_logits[0, target_class_idx]

        score.backward(retain_graph=True)

        if self.gradients is None or self.activations is None:
            raise RuntimeError("Gradients or activations not captured for Grad-CAM.")

        # Channel-wise weights: Global average pooling over gradients
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)  # [1, C, 1, 1]

        # Weighted combination of forward activation maps
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True)  # [1, 1, H, W]

        # ReLU to focus only on features with a positive influence
        cam = F.relu(cam)

        # Normalize between 0 and 1
        cam_min, cam_max = cam.min(), cam.max()
        if cam_max > cam_min:
            cam = (cam - cam_min) / (cam_max - cam_min + 1e-8)
        else:
            cam = torch.zeros_like(cam)

        # Upsample to match model input dimensions
        _, _, h, w = input_tensor.shape
        cam = F.interpolate(cam, size=(h, w), mode="bilinear", align_corners=False)

        heatmap = cam.squeeze().cpu().numpy()
        return heatmap

    def overlay_heatmap(
        self,
        original_image: Image.Image,
        heatmap: np.ndarray,
        alpha: float = 0.45,
        colormap_name: str = "jet",
    ) -> Image.Image:
        """
        Overlays the 2D heatmap on the original PIL image.
        """
        orig_w, orig_h = original_image.size
        # Resize heatmap to original image size
        heatmap_pil = Image.fromarray((heatmap * 255).astype(np.uint8)).resize((orig_w, orig_h), Image.Resampling.BILINEAR)
        heatmap_resized = np.array(heatmap_pil) / 255.0

        # Apply colormap
        try:
            import matplotlib
            cmap = matplotlib.colormaps[colormap_name]
        except (AttributeError, KeyError):
            cmap = cm.get_cmap(colormap_name)
        colored_heatmap = cmap(heatmap_resized)[:, :, :3]  # drop alpha, RGB in [0, 1]
        colored_heatmap = (colored_heatmap * 255).astype(np.uint8)

        # Blend
        orig_rgb = original_image.convert("RGB")
        orig_np = np.array(orig_rgb)
        blended = (orig_np * (1 - alpha) + colored_heatmap * alpha).astype(np.uint8)

        return Image.fromarray(blended)

    def generate_base64_overlay(
        self,
        original_image: Image.Image,
        heatmap: np.ndarray,
        alpha: float = 0.45,
    ) -> str:
        """Generates base64 encoded PNG data URI string."""
        overlay_img = self.overlay_heatmap(original_image, heatmap, alpha=alpha)
        buffered = io.BytesIO()
        overlay_img.save(buffered, format="PNG")
        encoded = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"

    def cleanup(self):
        """Remove hooks to prevent memory leaks."""
        for hook in self._hooks:
            hook.remove()
        self._hooks.clear()
