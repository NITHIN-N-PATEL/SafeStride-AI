from ultralytics import YOLO

# 1. Load the model you sent
model = YOLO('best.pt')

# 2. Run detection on an image
results = model.predict(source='test_image.jpg', save=True, conf=0.25)

# 3. View the results
results[0].show()
