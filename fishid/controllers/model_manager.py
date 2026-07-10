# fishid/controllers/model_manager.py
import os
import sys
from fishid.core.dinov2_extractor import DINOv2Extractor
from fishid.core.anomaly_detector import AnomalyDetector
from fishid.core.classifier import FishClassifier
from fishid.core.classifier_direct import DirectClassifier  # Nouveau
from fishid.core.object_detector_yolo import YOLOv8Detector
from fishid.utils import resource_path


class ModelManager:
    def __init__(self):
        self.models_dir = self._get_models_dir()
        self.dinov2 = None
        self.anomaly_detector = None
        self.classifier_fish = None
        self.classifier_waste = None
        self.classifier_waste_direct = None  
        self.object_detector = None

    def _get_models_dir(self):
        if getattr(sys, 'frozen', False):
            return os.path.join(os.path.dirname(sys.executable), "models")
        return resource_path("models")

    def load_models(self, use_gpu=False, status_callback=None):
        if status_callback:
            status_callback("🔄 Chargement des modèles...")

        dinov2_path = os.path.join(self.models_dir, "dinov2_backbone.onnx")
        anomaly_path = os.path.join(self.models_dir, "model_det_fish.pkl")
        fish_path = os.path.join(self.models_dir, "classifier_fish.onnx")
        waste_path = os.path.join(self.models_dir, "classifier_waste.onnx")
        waste_direct_path = os.path.join(self.models_dir, "classifier_waste_direct.onnx")  
        yolo_path = os.path.join(self.models_dir, "yolov8n.onnx")

        self.dinov2 = DINOv2Extractor(model_path=dinov2_path)
        self.anomaly_detector = AnomalyDetector(model_path=anomaly_path)
        self.classifier_fish = FishClassifier(model_path=fish_path)
        self.classifier_waste = DirectClassifier(model_path=waste_direct_path)
        
        self.object_detector = YOLOv8Detector(
            model_path=yolo_path, conf_threshold=0.1, nms_threshold=0.2
        )

        # Chargement du classifieur direct (optionnel)
        if os.path.exists(waste_direct_path):
            self.classifier_waste_direct = DirectClassifier(model_path=waste_direct_path)
            direct_ok = self.classifier_waste_direct.load_model(use_gpu=use_gpu)
            if direct_ok:
                self.classifier_waste_direct.set_class_names(['Organique', 'Textile', 'Verre', 'Plastique', 'Canette'])
                if status_callback:
                    status_callback("✅ Classifieur direct déchets chargé")
        else:
            if status_callback:
                status_callback("ℹ️ Classifieur direct déchets non trouvé, utilisation du pipeline standard")

        dino_ok = self.dinov2.load_model(use_gpu=use_gpu)
        anom_ok = self.anomaly_detector.load_model()
        fish_ok = self.classifier_fish.load_model(use_gpu=use_gpu)
        waste_ok = self.classifier_waste.load_model(use_gpu=use_gpu)
        det_ok = self.object_detector.load_model(use_gpu=use_gpu)

        if fish_ok:
            self.classifier_fish.set_class_names([
                'Chaetodon bennetti', 'Diodon hystrix', 'Pomacanthus asfur',
                'Lutjanus argentimaculatus', 'Acanthurus leucosternon',
                'Chaetodon rafflesii', 'Chaetodon semilarvatus', 'Pomacanthus chrysurus',
                'Pterocaesio marri', 'Pterocaesio chrysozona', 'Acanthurus lineatus',
                'Acanthurus sohal', 'Chaetodon interruptus', 'Forcipiger flavissimus',
                'Canthigaster bennetti', 'Heniochus monoceros', 'Chilomycterus reticulatus',
                'Diodon liturosus', 'Canthigaster margaritata', 'Takifugu oblongus',
                'Myripristis adusta', 'Cyclichthys spilostylus', 'Pomacanthus imperator',
                'Pseudanthias ignitus', 'Chaetodon citrinellus', 'Acanthurus guttatus',
                'Cantherhines dumerilii', 'Chaetodon austriacus'
            ])
        if waste_ok:
            self.classifier_waste.set_class_names(
               ['Organique', 'Textile', 'Verre', 'Plastique', 'Canette'])

        if dino_ok and (fish_ok or waste_ok) and anom_ok:
            if status_callback:
                status_callback("✅ Tous les modèles chargés. Prêt.")
            return True
        if dino_ok and status_callback:
            status_callback("⚠️ DINOv2 OK. Vérifiez les classifieurs.")
        return dino_ok

    def get_classifier(self, mode="fish"):
        """Retourne le classifieur standard (poissons ou déchets)."""
        return self.classifier_fish if mode == "fish" else self.classifier_waste

    def get_waste_direct_classifier(self):
        """Retourne le classifieur direct pour les déchets (sans DINOv2)."""
        return self.classifier_waste_direct

    def unload_classifier(self, mode):
        classifier = self.get_classifier(mode)
        if classifier:
            classifier.unload_model()

    def reload_classifier(self, mode, use_gpu):
        classifier = self.get_classifier(mode)
        if classifier:
            classifier.load_model(use_gpu=use_gpu)