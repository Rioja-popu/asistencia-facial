-- Datos mínimos para poder ingresar al sistema recién instalado.
-- Usuario administrador de demostración: admin / admin (se guarda cifrada).
-- Cambiar la contraseña después de instalar, desde "Cambiar contraseña".
INSERT INTO usuario (nombre_usuario, rol, contrasenia)
VALUES ('admin', 'administrador', 'pbkdf2_sha256$200000$5f1d3c9a7b2e4f60819a0b1c2d3e4f50$f99131c974588cceeaa18b27ef806a44f9542f734b8b11749847d8fbbd59dbdb');
