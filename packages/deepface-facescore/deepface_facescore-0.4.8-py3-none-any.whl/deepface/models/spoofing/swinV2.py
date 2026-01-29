import os
import torch
import torch.nn.functional as F
import numpy as np
from torchvision import transforms
from typing import List, Union, Tuple
from deepface.commons import folder_utils

try:
    from .nets.utils import get_model
except ImportError:
    from deepface.models.spoofing.nets.utils import get_model

from torchvision.utils import save_image
class SwinV2:
    """FAS Library"""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # We save weights in ~/.deepface/weights/ (Standard DeepFace location)
        home = folder_utils.get_deepface_home()
        self.weights_dir = os.path.join(home, ".deepface", "weights")

        self.model_filename = "face_swin_v2_base.pth"
        self.model_path = os.path.join(self.weights_dir, self.model_filename)

        self._ensure_weights_exist()

        print("Building SwinV2 model from local 'nets' folder...")
        self.model = get_model('swin_v2_b', 2)

        print(f"Loading weights from {self.model_path}...")
        checkpoint = torch.load(self.model_path, map_location=self.device)

        state_dict = checkpoint.get('model', checkpoint.get('state_dict', checkpoint))
        new_state_dict = {k.replace('module.', ''): v for k, v in state_dict.items()}

        self.model.load_state_dict(new_state_dict, strict=True)
        self.model.to(self.device)
        self.model.eval()

        print(f"[DEBUG] Model successfully loaded on: {next(self.model.parameters()).device}")

        # Standard ImageNet Preprocessing
        self.preprocess = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            # transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def _ensure_weights_exist(self):
        """
        Checks if the .pth file exists. If not, downloads it from Google Drive.
        """
        if os.path.exists(self.model_path):
            return
        print(self.model_path)
        print(f"\n[INFO] Model weights not found at {self.model_path}")
        print("Downloading from Google Drive (approx 80MB)...")

        # Ensure the directory exists
        os.makedirs(self.weights_dir, exist_ok=True)

        # # Google Drive File ID for 'face_swin_v2_base.pth'
        # file_id = "1E4UD8UK_KzjhpAvR6hYInlteOEaxDZbZ"
        # url = f'https://drive.google.com/uc?id={file_id}'

        file_id = "1Ii3JmoRjWcOLF4xNwCqtJyp0Ok0vJva3"
        url = f"https://drive.google.com/uc?id={file_id}"

        try:
            import gdown
            gdown.download(url, self.model_path, quiet=False)
        except ImportError:
            raise ImportError(
                "Auto-download failed because 'gdown' is not installed.\n"
                "Please run: pip install gdown"
            )

        if not os.path.exists(self.model_path):
            raise FileNotFoundError("Download appeared to finish, but file is missing.")
        print("Download complete.\n")

    def _crop_face(self, img_tensor, bbox):
        """Crops face with expansion """
        if torch.is_tensor(img_tensor):
            img = img_tensor.cpu().numpy().transpose(1, 2, 0)
            if img.max() <= 1.0: img = (img * 255).astype(np.uint8)
        else:
            img = img_tensor

        h_img, w_img = img.shape[:2]
        x, y, w, h = bbox

        # Expansion ratio 0.3
        expand_ratio = 0.3
        x_new = max(0, int(x - w * expand_ratio))
        y_new = max(0, int(y - h * expand_ratio))
        w_new = min(w_img - x_new, int(w * (1 + 2 * expand_ratio)))
        h_new = min(h_img - y_new, int(h * (1 + 2 * expand_ratio)))

        return img[y_new:y_new + h_new, x_new:x_new + w_new]

    def analyze(self, imgs: List[torch.Tensor], facial_areas: List[Union[list, tuple]]) -> List[Tuple[bool, float]]:
        results = []

        for img, area in zip(imgs, facial_areas):
            # face_crop = self._crop_face(img, area)

            # input_tensor = self.preprocess(img).unsqueeze(0).to(self.device)
            # input_tensor = img.unsqueeze(0).to(self.device)


            # print(f"[DEBUG] Input Tensor is on: {input_tensor.device}")

            # Check Model Device (verification)
            print(f"[DEBUG] Model is on: {next(self.model.parameters()).device}")

            img_resized = F.interpolate(
                img.unsqueeze(0),
                size=(224, 224),
                mode="bilinear",
                align_corners=False
            )

            input_tensor = img_resized.to(self.device)

            with torch.no_grad():

                outputs = self.model(input_tensor/255.0)
                logits = outputs[1] if isinstance(outputs, tuple) else outputs
                probs = F.softmax(logits, dim=1)

            probs_np = probs.cpu().numpy()[0]
            real_score = float(probs_np[1])
            is_real = real_score < 0.5

            results.append((is_real, real_score))
        return results