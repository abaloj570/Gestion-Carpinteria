# Añadimos 'actualizar_estado_pedido' al import
from database_manager import inicializar_db, guardar_registro, obtener_todo, actualizar_estado_pedido

def menu_principal():
    inicializar_db()
    while True:
        print("\n--- CRM CARPINTERÍA PRO ---")
        print("1. Nuevo Pedido | 2. Ver Listado | 3. Actualizar Estado | 4. Salir")
        opcion = input("Selecciona: ")

        if opcion == "1":
            cliente = input("Cliente: ")
            trabajo = input("Trabajo: ")
            precio = input("Presupuesto: ")
            guardar_registro({'Cliente': cliente, 'Trabajo': trabajo, 'Precio': precio, 'Estado': 'Pendiente'})
        
        elif opcion == "2":
            print("\n--- LISTADO DE TRABAJOS ---")
            print(obtener_todo())
        
        elif opcion == "3":
            nom = input("¿A qué cliente le cambias el estado?: ")
            est = input("Nuevo estado (En proceso/Finalizado/Entregado): ")
            if actualizar_estado_pedido(nom, est):
                print(f"✅ Estado de {nom} actualizado.")
            else:
                print("❌ No se encontró ese cliente.")
        
        elif opcion == "4":
            print("Saliendo... ¡Buen trabajo en el taller!")
            break

if __name__ == "__main__":
    menu_principal()