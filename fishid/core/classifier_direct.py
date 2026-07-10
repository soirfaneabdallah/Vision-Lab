# fishid/core/classifier_direct.py
import numpy as np
import cv2
import onnxruntime as ort

# Tentative d'import de preprocess_input d'EfficientNet
try:
    from tensorflow.keras.applications.efficientnet import preprocess_input
    PREPROCESS_AVAILABLE = True
except ImportError:
    PREPROCESS_AVAILABLE = False
    print("⚠️ TensorFlow non disponible, fallback à la normalisation manuelle")


class DirectClassifier:
    """
    Classifieur ONNX qui prend directement une image rognée (crop) en entrée.
    S'adapte automatiquement au format d'entrée du modèle (NHWC ou NCHW).
    """

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.session = None
        self.input_name = None
        self.output_name = None
        self.class_names = []
        self.imgsz = 224
        self.input_type = None          # "image" ou "features"
        self.input_format = None        # "NHWC" ou "NCHW"

    def load_model(self, use_gpu: bool = False) -> bool:
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if use_gpu else ['CPUExecutionProvider']
        try:
            self.session = ort.InferenceSession(self.model_path, providers=providers)
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name

            # Détecter le type d'entrée et son format
            input_shape = self.session.get_inputs()[0].shape
            if len(input_shape) == 2:
                self.input_type = "features"
                self.input_format = None
            elif len(input_shape) == 4:
                self.input_type = "image"
                # Déterminer le format : NHWC ou NCHW
                # Si la dimension 1 est 3 ou la dimension 3 est 3
                if input_shape[1] == 3 and (len(input_shape) == 4 and input_shape[3] == -1):
                    self.input_format = "NCHW"
                elif input_shape[3] == 3 or input_shape[3] == -1:
                    self.input_format = "NHWC"
                else:
                    # Fallback : on essaie de deviner par la taille
                    if input_shape[1] in [224, 256, 128] and input_shape[3] in [3, -1]:
                        self.input_format = "NCHW"
                    else:
                        self.input_format = "NHWC"  # Par défaut pour les modèles venant de TF/Keras
                
            else:
                self.input_type = "unknown"
                self.input_format = None
            return True
        except Exception as e:
            print(f"❌ Erreur chargement classifieur direct : {e}")
            return False

    def set_class_names(self, names: list):
        self.class_names = names

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Prépare l'image selon le format attendu par le modèle (NHWC ou NCHW).
        Utilise preprocess_input d'EfficientNet si disponible, sinon normalisation [-1,1].
        """
        # Redimensionner
        img = cv2.resize(image, (self.imgsz, self.imgsz))

        # Convertir en RGB (OpenCV lit en BGR)
        if len(img.shape) == 3 and img.shape[2] == 3:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            img_rgb = img

        # Convertir en float32
        img_float = img_rgb.astype(np.float32)

        # Appliquer le préprocessing
        if PREPROCESS_AVAILABLE:
            img_processed = preprocess_input(img_float)
        else:
            # Normalisation standard [-1, 1] (compatible avec EfficientNet)
            img_processed = (img_float / 127.5) - 1.0

        # Ajouter la dimension batch
        if self.input_format == "NCHW":
            # Format : (batch, channels, height, width)
            img_chw = np.transpose(img_processed, (2, 0, 1))
            img_batch = np.expand_dims(img_chw, axis=0)
        else:
            # Format : (batch, height, width, channels) - par défaut
            img_batch = np.expand_dims(img_processed, axis=0)

        return img_batch

    def classify_image(self, image: np.ndarray) -> dict:
        """
        Classifie une image brute (crop).
        Utilisé si le modèle attend une image en entrée.
        """
        if self.session is None:
            return None

        if self.input_type != "image":
            raise ValueError("Ce modèle attend des features, pas une image. Utilisez classify_from_features().")

        img_batch = self._preprocess_image(image)

        # Inférence ONNX
        outputs = self.session.run([self.output_name], {self.input_name: img_batch})
        probs = outputs[0][0]  # Probabilités

        class_id = int(np.argmax(probs))
        confidence = float(probs[class_id])
        class_name = self.class_names[class_id] if class_id < len(self.class_names) else f"classe_{class_id}"

        return {
            'class_name': class_name,
            'class_id': class_id,
            'confidence': confidence,
            'all_probs': probs.tolist()
        }

    def classify_from_features(self, features: np.ndarray) -> dict:
        """
        Classifie à partir d'un vecteur de caractéristiques (issu de DINOv2).
        Utilisé si le modèle attend des features (shape 2D).
        """
        if self.session is None or features is None:
            return None

        if self.input_type != "features":
            raise ValueError("Ce modèle attend une image, pas des features. Utilisez classify_image().")

        try:
            features = np.array(features).reshape(1, -1).astype(np.float32)
            outputs = self.session.run([self.output_name], {self.input_name: features})
            probs = outputs[0][0]
            class_id = int(np.argmax(probs))
            confidence = float(probs[class_id])
            class_name = self.class_names[class_id] if class_id < len(self.class_names) else f"classe_{class_id}"
            return {
                'class_name': class_name,
                'class_id': class_id,
                'confidence': confidence,
                'all_probs': probs.tolist()
            }
        except Exception as e:
            print(f"❌ Erreur classification depuis features : {e}")
            return None
    def unload_model(self):
        self.session = None
        