from deepface.modules import representation
import torch

sub_img_tensors = torch.load("deepface/modules/pic.pt")  # shape [N, C, H, W]
# print(len(sub_img_tensors), sub_img_tensors.shape, sub_img_tensors.size())
embeddings = representation.represent(
            img_tensors=sub_img_tensors,
            model_name="Facenet512ONNX",
            detector_backend="fastmtcnn",
            align=True,
            expand_percentage=0,
            anti_spoofing=True
        )

print(embeddings)