# convert_keras_classifier_to_onnx.py
import tensorflow as tf
import tf2onnx
import onnx
import os
import argparse

def convert_keras_to_onnx(keras_model_path, onnx_output_path, input_shape=(224,224,3)):
    """
    Convertit un modèle Keras de classification d'images en ONNX.
    
    Args:
        keras_model_path: chemin du modèle .keras
        onnx_output_path: chemin de sortie .onnx
        input_shape: tuple (hauteur, largeur, canaux)
    """
    # Charger le modèle
    model = tf.keras.models.load_model(keras_model_path)
    model.summary()
    
    # Désactiver les couches de dropout (mode inférence)
    # Note : Keras le fait automatiquement lors de l'export, mais par précaution
    # on peut définir training=False dans la signature, mais tf2onnx le gère.
    
    # Signature d'entrée : image batch
    input_signature = [tf.TensorSpec(
        shape=(1, *input_shape),   # batch=1, hauteur, largeur, canaux
        dtype=tf.float32,
        name="input_image"
    )]
    
    # Conversion
    model_proto, _ = tf2onnx.convert.from_keras(
        model,
        input_signature=input_signature,
        opset=13,
        output_path=onnx_output_path
    )
    
    print(f"✅ Modèle ONNX exporté : {onnx_output_path}")
    
    # Vérification
    onnx_model = onnx.load(onnx_output_path)
    onnx.checker.check_model(onnx_model)
    print("✅ Vérification ONNX réussie.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convertir un modèle Keras de classification d'images en ONNX")
    parser.add_argument("--model", type=str, default=r"C:\Users\hp\ProjetMaster\EfficientNetB0_1.keras", 
                        help="Chemin du modèle Keras (.keras)")
    parser.add_argument("--output", type=str, default="models/classifier_waste.onnx", 
                        help="Chemin de sortie ONNX (.onnx)")
    parser.add_argument("--height", type=int, default=224, help="Hauteur d'entrée (pixels)")
    parser.add_argument("--width", type=int, default=224, help="Largeur d'entrée (pixels)")
    parser.add_argument("--channels", type=int, default=3, help="Nombre de canaux (3 pour RGB, 1 pour gris)")
    
    args = parser.parse_args()
    
    input_shape = (args.height, args.width, args.channels)
    convert_keras_to_onnx(args.model, args.output, input_shape)