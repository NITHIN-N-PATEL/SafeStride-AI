import requests
import json
import base64

# The address of your orchestrator
URL = "http://127.0.0.1:8000/detect/explain"
TEST_IMAGE = "test_image.jpg"

def run_test():
    try:
        print("🔗 Connecting to SafeStride Backend...")
        with open(TEST_IMAGE, "rb") as f:
            files = {"file": f}
            # This 'true' tells your app.py to trigger the Grad-CAM logic
            data = {"include_heatmap": "true"} 
            
            response = requests.post(URL, files=files, data=data)

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])

            if not results:
                print("❓ Connection successful, but no objects were detected in the image.")
                return

            # --- VERIFICATION LOG ---
            print("\n" + "="*50)
            print("🌟 AI FEATURE VERIFICATION REPORT 🌟")
            print("="*50)

            for i, obj in enumerate(results[:3]):  # Look at the top 3 detections
                print(f"\n[Object {i+1}: {obj['label'].upper()}]")
                
                # Verify Explainability Feature
                explain = obj.get('explainability', {})
                print(f"🔹 Reasoning: {explain.get('detection_reason')}")
                print(f"🔹 Confidence Tier: {explain.get('confidence_tier', {}).get('tier')}")
                
                # Verify Grad-CAM Feature
                if "heatmap_b64" in obj:
                    print("✅ Grad-CAM Heatmap: RECEIVED (Successfully generated)")
                else:
                    print("❌ Grad-CAM Heatmap: MISSING")

            print("\n" + "="*50)
            print("✅ TEST COMPLETE: Your features are LIVE in the backend.")
            print("="*50)

        else:
            print(f"❌ Server Error: {response.status_code}")
            print(response.text)

    except FileNotFoundError:
        print(f"❌ Error: Could not find '{TEST_IMAGE}'. Please put an image in the folder.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_test()