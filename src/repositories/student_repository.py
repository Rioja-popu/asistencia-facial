from config.database import get_connection


class StudentRepository:

    def save_student_with_photos(self, student_data, photos_data):
        """Guarda un alumno y sus 3 fotos (BYTEA) dentro de una misma transacción."""
        query_student = """
            INSERT INTO alumno (
                nombre, apellido, dni, carrera, celular, 
                correo_electronico, fecha_nacimiento, anio_ingreso, domicilio, libreta
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """

        query_photo = """
            INSERT INTO foto_alumno (alumno_id, angulo, imagen)
            VALUES (%s, %s, %s);
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. Insertar el alumno y obtener el ID generado
                cur.execute(query_student, student_data)
                student_id = cur.fetchone()[0]

                # 2. Insertar las 3 imágenes vinculadas al ID del alumno
                for angulo, imagen_bytes in photos_data.items():
                    cur.execute(query_photo, (student_id, angulo, imagen_bytes))

            conn.commit()