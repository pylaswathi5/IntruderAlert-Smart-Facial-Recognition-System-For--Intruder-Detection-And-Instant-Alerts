import os
import cv2
import numpy as np
from mtcnn import MTCNN
from keras_facenet import FaceNet
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AUTHORIZED_DIR = "authorized_faces"
THRESHOLD = 0.7

detector = MTCNN()
embedder = FaceNet()

authorized_embeddings = []
authorized_names = []

os.makedirs(AUTHORIZED_DIR, exist_ok=True)

def extract_embedding(image):
    """Extract face embedding from image"""
    try:
        if image is None:
            logger.warning("Empty image provided")
            return None
        
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        faces = detector.detect_faces(rgb)
        if not faces:
            logger.warning("No faces detected in image")
            return None

        x, y, w, h = faces[0]["box"]
        # Ensure coordinates are positive
        x, y = max(0, x), max(0, y)
        w, h = max(0, w), max(0, h)
        
        face = rgb[y:y+h, x:x+w]
        if face.size == 0:
            logger.warning("Invalid face region")
            return None
            
        face = cv2.resize(face, (160, 160))
        embedding = embedder.embeddings([face])[0]
        return embedding
    except Exception as e:
        logger.error(f"Error extracting embedding: {str(e)}")
        return None

def load_authorized_faces():
    """Load all authorized face embeddings from directory"""
    authorized_embeddings.clear()
    authorized_names.clear()

    if not os.path.exists(AUTHORIZED_DIR):
        logger.warning(f"Authorized directory {AUTHORIZED_DIR} does not exist")
        return

    for person in os.listdir(AUTHORIZED_DIR):
        person_path = os.path.join(AUTHORIZED_DIR, person)
        if not os.path.isdir(person_path):
            continue

        for img_name in os.listdir(person_path):
            if not img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
                
            img_path = os.path.join(person_path, img_name)
            img = cv2.imread(img_path)
            if img is None:
                logger.warning(f"Could not read image: {img_path}")
                continue

            emb = extract_embedding(img)
            if emb is not None:
                authorized_embeddings.append(emb)
                authorized_names.append(person)
    
    logger.info(f"Loaded {len(authorized_embeddings)} authorized face embeddings")

def recognize_face(embedding):
    """Recognize face by comparing embedding with authorized faces"""
    if not authorized_embeddings:
        logger.warning("No authorized faces loaded")
        return "INTRUDER", 0.0

    try:
        sims = cosine_similarity([embedding], authorized_embeddings)[0]
        best = np.argmax(sims)
        score = float(sims[best])

        if score >= THRESHOLD:
            return authorized_names[best], score
        return "INTRUDER", score
    except Exception as e:
        logger.error(f"Error recognizing face: {str(e)}")
        return "INTRUDER", 0.0

def get_authorized_users():
    """Get list of all authorized user names"""
    if not os.path.exists(AUTHORIZED_DIR):
        return []
    return [name for name in os.listdir(AUTHORIZED_DIR) 
            if os.path.isdir(os.path.join(AUTHORIZED_DIR, name))]
