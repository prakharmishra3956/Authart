import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

model_id = "openai/clip-vit-base-patch32"
processor = CLIPProcessor.from_pretrained(model_id)
model = CLIPModel.from_pretrained(model_id)

image = Image.new('RGB', (224, 224), color = 'red')
inputs = processor(images=image, return_tensors="pt")

print("Keys in inputs:", inputs.keys())
image_features = model.get_image_features(**inputs)

print("Type of image_features:", type(image_features))
print("Attributes of image_features:", dir(image_features))
if hasattr(image_features, 'shape'):
    print("Shape:", image_features.shape)
