import cv2
import numpy as np
from deepface import DeepFace


class FacialRecognitionService:

    def __init__(self):
        self.reference_embeddings = []  # Lista de dicts: {'alumno_id': x, 'nombre': y, 'embedding': vec}
        # Pre-cargar el modelo para agilizar la inferencia posterior
        DeepFace.build_model("Facenet512")

    def cargar_referencias_desde_db(self, alumnos_db):
        """
        Recibe la lista de alumnos recuperados de PostgreSQL y genera sus embeddings de referencia.
        alumnos_db = [(id, nombre, apellido, bytes_frente, bytes_izq, bytes_der), ...]
        """
        self.reference_embeddings.clear()

        for alumno in alumnos_db:
            alumno_id = alumno[0]
            nombre_completo = f"{alumno[1]} {alumno[2]}"
            fotos_bytes = [alumno[3], alumno[4], alumno[5]]  # frente, izq, der

            for img_bytes in fotos_bytes:
                if img_bytes:
                    embedding = self.generar_embedding_desde_bytes(img_bytes)
                    if embedding is not None:
                        self.reference_embeddings.append(
                            {
                                "alumno_id": alumno_id,
                                "nombre": nombre_completo,
                                "embedding": embedding,
                            }
                        )

    def generar_embedding_desde_bytes(self, img_bytes):
        """Convierte bytes de una imagen en un arreglo OpenCV y genera el embedding Facenet512."""
        try:
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return None

            # Generar la representación numérica de 512 valores
            results = DeepFace.represent(
                img_path=img,
                model_name="Facenet512",
                enforce_detection=False,  # No forzar detección estricta si ya viene recortada/valida
            )

            if results and len(results) > 0:
                return np.array(results[0]["embedding"])
        except Exception as e:
            print(f"Error generando embedding: {e}")
        return None

    def calcular_distancia_coseno(self, emb1, emb2):
        """Calcula la distancia coseno entre dos vectores (0.0 = idénticos, 1.0 = totalmente opuestos)."""
        dot_product = np.dot(emb1, emb2)
        norm_emb1 = np.linalg.norm(emb1)
        norm_emb2 = np.linalg.norm(emb2)

        if norm_emb1 == 0 or norm_emb2 == 0:
            return 1.0

        similitud = dot_product / (norm_emb1 * norm_emb2)
        return 1.0 - similitud

    def reconocer_rostro(self, face_crop, threshold=0.40):
        """
        Recibe la imagen recortada del rostro detectado por la webcam,
        genera su embedding y busca el best match dentro de las referencias.
        """
        if not self.reference_embeddings:
            return None, 1.0

        # Generar embedding del rostro actual
        current_embedding = self.generar_embedding_desde_bytes(
            cv2.imencode(".jpg", face_crop)[1].tobytes()
        )

        if current_embedding is None:
            return None, 1.0

        best_match = None
        min_distance = 1.0

        # Comparar con todas las referencias guardadas
        for ref in self.reference_embeddings:
            dist = self.calcular_distancia_coseno(
                current_embedding, ref["embedding"]
            )
            if dist < min_distance:
                min_distance = dist
                best_match = ref

        # Aceptar solo si es menor o igual al umbral 0.40
        if min_distance <= threshold and best_match is not None:
            return best_match, min_distance

        return None, min_distance