# scripts/export_dinov2.py
import torch
from transformers import AutoModel
import os

def export_dinov2_to_onnx(model_name="facebook/dinov2-small", output_path="models/dinov2_backbone.onnx"):
    print(f"📥 Chargement du backbone {model_name}...")
    backbone = AutoModel.from_pretrained(model_name)
    backbone.eval()

    # DINOv2 utilise toujours 224x224 (taille standard)
    height, width = 224, 224
    dummy_input = torch.randn(1, 3, height, width)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Export ONNX avec fallback TorchScript
    try:
        torch.onnx.export(
            backbone, dummy_input, output_path,
            input_names=["pixel_values"],
            output_names=["last_hidden_state", "pooler_output"],
            opset_version=12,
            do_constant_folding=True,
            dynamic_axes={
                "pixel_values": {0: "batch_size"},
                "last_hidden_state": {0: "batch_size"},
                "pooler_output": {0: "batch_size"},
            },
        )
        print(f"✅ Export direct réussi : {output_path}")
    except Exception as e:
        print(f"⚠️ Export direct échoué ({e})")
        print("   Utilisation du fallback TorchScript...")
        traced = torch.jit.trace(backbone, dummy_input)
        torch.onnx.export(
            traced, dummy_input, output_path,
            input_names=["pixel_values"],
            output_names=["last_hidden_state", "pooler_output"],
            opset_version=12,
            do_constant_folding=True,
            dynamic_axes={
                "pixel_values": {0: "batch_size"},
                "last_hidden_state": {0: "batch_size"},
                "pooler_output": {0: "batch_size"},
            },
        )
        print(f"✅ Export via TorchScript réussi : {output_path}")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"📦 Taille du modèle ONNX : {size_mb:.1f} Mo")

if __name__ == "__main__":
    export_dinov2_to_onnx()