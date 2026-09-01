import sys
print("1. Iniciando script...")

from PySide6.QtWidgets import QApplication
print("2. PySide6 importado correctamente")

from ui.login_window import LoginWindow
print("3. LoginWindow importado correctamente")

def main():
    print("4. Creando QApplication...")
    app = QApplication(sys.argv)
    
    print("5. Instanciando ventana...")
    window = LoginWindow()
    
    print("6. Mostrando ventana...")
    window.show()
    
    print("7. Entrando al bucle de eventos...")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()