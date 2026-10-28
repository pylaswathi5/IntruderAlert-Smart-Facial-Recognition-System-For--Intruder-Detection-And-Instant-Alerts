import cv2

for i in range(5):  # Try first 5 indexes
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera index {i} is working")
        cap.release()
    else:
        print(f"Camera index {i} failed")