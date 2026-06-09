import os
import sys

def test_auth():
    # Guardar estado original
    original_admin = os.environ.get("ADMIN_PASSWORD")
    original_operator = os.environ.get("OPERATOR_PASSWORD")

    # Asegurarnos de que las variables de entorno están limpias primero
    if "ADMIN_PASSWORD" in os.environ:
        del os.environ["ADMIN_PASSWORD"]
    if "OPERATOR_PASSWORD" in os.environ:
        del os.environ["OPERATOR_PASSWORD"]

    import ui.auth

    usuarios_vacios = ui.auth.get_usuarios()
    assert len(usuarios_vacios) == 0, "Users should be empty when env vars are not set."

    # Configurar las variables de entorno
    os.environ["ADMIN_PASSWORD"] = "secureadmin123"
    os.environ["OPERATOR_PASSWORD"] = "secureoperator123"

    usuarios_con_env = ui.auth.get_usuarios()

    assert "admin" in usuarios_con_env, "Admin should be in users dict."
    assert usuarios_con_env["admin"]["clave"] == "secureadmin123", "Admin password should match env var."
    assert usuarios_con_env["admin"]["rol"] == "admin", "Admin role should be admin."

    assert "operador" in usuarios_con_env, "Operador should be in users dict."
    assert usuarios_con_env["operador"]["clave"] == "secureoperator123", "Operador password should match env var."
    assert usuarios_con_env["operador"]["rol"] == "basico", "Operador role should be basico."

    # Restaurar estado original
    if original_admin is not None:
        os.environ["ADMIN_PASSWORD"] = original_admin
    else:
        del os.environ["ADMIN_PASSWORD"]

    if original_operator is not None:
        os.environ["OPERATOR_PASSWORD"] = original_operator
    else:
        del os.environ["OPERATOR_PASSWORD"]

    print("✅ All authentication tests passed securely.")

if __name__ == "__main__":
    test_auth()
