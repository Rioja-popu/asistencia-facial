import sys
import os

# Agregar el directorio 'src' al path de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("1. Iniciando script...")

from PySide6.QtWidgets import QApplication
print("2. PySide6 importado correctamente")

from ui.login_window import LoginWindow
print("3. LoginWindow importado correctamente")

def main():
    print("4. Creando QApplication...")
    app = QApplication(sys.argv)

    # Estilo global para corregir el texto blanco en los QMessageBox y diálogos
    app.setStyleSheet("""
        QMessageBox {
            background-color: #ffffff;
        }
        QMessageBox QLabel {
            color: #2c3e50;
            font-size: 13px;
        }
        QMessageBox QPushButton {
            background-color: #3498db;
            color: #ffffff;
            font-weight: bold;
            padding: 6px 16px;
            border-radius: 4px;
            border: none;
            min-width: 60px;
        }
        QMessageBox QPushButton:hover {
            background-color: #2980b9;
        }
    """)
    
    print("5. Instanciando ventana...")
    window = LoginWindow()
    
    print("6. Mostrando ventana...")
    window.show()
    
    print("7. Entrando al bucle de eventos...")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()