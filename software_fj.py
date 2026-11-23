"""
Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - Fase 4
Sin bases de datos: solo objetos, listas y un archivo de logs (logs.txt).
"""
import re
from abc import ABC, abstractmethod
from datetime import datetime

ARCHIVO_LOG = "logs.txt"  # único archivo usado: registro de eventos y errores


# ---------------------------------------------------------------- LOGS
def registrar_log(nivel, mensaje):
    """Escribe una línea con fecha, nivel y mensaje en el archivo de logs."""
    marca = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{marca}] {nivel}: {mensaje}\n")
    except OSError as e:
        # Si el log falla, el sistema sigue funcionando
        print(f"(No se pudo escribir el log: {e})")


# ---------------------------------------------------- EXCEPCIONES PERSONALIZADAS
class ErrorSistema(Exception):
    """Excepción base de Software FJ."""


class ClienteInvalidoError(ErrorSistema):
    """Datos de cliente inválidos."""


class ServicioInvalidoError(ErrorSistema):
    """Parámetros de servicio inválidos."""


class ParametroFaltanteError(ErrorSistema):
    """Falta un parámetro obligatorio."""


class ReservaError(ErrorSistema):
    """Error al crear o procesar una reserva."""


class OperacionNoPermitidaError(ErrorSistema):
    """Operación no válida para el estado actual."""


# ---------------------------------------------------------- CLASE ABSTRACTA GENERAL
class Entidad(ABC):
    """Entidad general del sistema (abstracción)."""
    _contador = 0  # genera ids únicos

    def __init__(self):
        Entidad._contador += 1
        self._id = Entidad._contador  # encapsulado

    @property
    def id(self):
        return self._id

    @abstractmethod
    def describir(self):
        """Cada entidad debe describirse a sí misma."""


# ------------------------------------------------------------------- CLIENTE
class Cliente(Entidad):
    """Cliente con validaciones robustas y datos personales encapsulados."""

    def __init__(self, nombre, email, telefono):
        super().__init__()
        self.__nombre = self._validar_nombre(nombre)
        self.__email = self._validar_email(email)
        self.__telefono = self._validar_telefono(telefono)

    @staticmethod
    def _validar_nombre(nombre):
        if not isinstance(nombre, str) or len(nombre.strip()) < 3:
            raise ClienteInvalidoError("Nombre inválido (mínimo 3 caracteres).")
        return nombre.strip()

    @staticmethod
    def _validar_email(email):
        if not isinstance(email, str) or not re.fullmatch(r"[\w.+-]+@[\w-]+\.[\w.-]+", email):
            raise ClienteInvalidoError(f"Email inválido: {email!r}")
        return email

    @staticmethod
    def _validar_telefono(tel):
        if not isinstance(tel, str) or not re.fullmatch(r"\d{7,10}", tel):
            raise ClienteInvalidoError(f"Teléfono inválido: {tel!r} (7 a 10 dígitos).")
        return tel

    @property
    def nombre(self):
        return self.__nombre

    @property
    def email(self):
        return self.__email

    @email.setter
    def email(self, nuevo):  # setter con validación
        self.__email = self._validar_email(nuevo)

    def describir(self):
        return f"Cliente #{self.id}: {self.__nombre} ({self.__email}, tel. {self.__telefono})"


# ------------------------------------------------------------------ SERVICIOS
class Servicio(Entidad):
    """Clase abstracta Servicio; las derivadas implementan su propio cálculo."""

    def __init__(self, nombre, tarifa_hora):
        super().__init__()
        if not isinstance(nombre, str) or not nombre.strip():
            raise ServicioInvalidoError("El servicio requiere un nombre.")
        if not isinstance(tarifa_hora, (int, float)) or tarifa_hora <= 0:
            raise ServicioInvalidoError("La tarifa por hora debe ser un número positivo.")
        self._nombre = nombre.strip()
        self._tarifa_hora = float(tarifa_hora)

    @property
    def nombre(self):
        return self._nombre

    def validar_parametros(self, horas):
        """Validación base de la duración (las hijas pueden sobrescribirla)."""
        if not isinstance(horas, (int, float)) or horas <= 0:
            raise ServicioInvalidoError("La duración debe ser mayor que 0.")

    @abstractmethod
    def calcular_costo(self, horas, impuesto=0.19, descuento=0.0):
        """Costo con parámetros opcionales (sobrecarga mediante valores por defecto)."""

    def costo_base(self, horas):
        """Variante sin impuesto ni descuento (sobrecarga)."""
        return self.calcular_costo(horas, impuesto=0.0, descuento=0.0)

    def _aplicar(self, subtotal, impuesto, descuento):
        if not 0 <= descuento < 1 or impuesto < 0:
            raise ServicioInvalidoError("Impuesto o descuento fuera de rango.")
        return round(subtotal * (1 - descuento) * (1 + impuesto), 2)


class ReservaSala(Servicio):
    def __init__(self, nombre, tarifa_hora, capacidad):
        super().__init__(nombre, tarifa_hora)
        self._capacidad = capacidad

    def validar_parametros(self, horas):
        super().validar_parametros(horas)
        if horas > 12:
            raise ServicioInvalidoError("Una sala no se reserva por más de 12 horas.")

    def calcular_costo(self, horas, impuesto=0.19, descuento=0.0):
        self.validar_parametros(horas)
        return self._aplicar(self._tarifa_hora * horas, impuesto, descuento)

    def describir(self):
        return f"Sala '{self._nombre}' (capacidad {self._capacidad}) - ${self._tarifa_hora:,.0f}/h"


class AlquilerEquipo(Servicio):
    def __init__(self, nombre, tarifa_hora, deposito):
        super().__init__(nombre, tarifa_hora)
        self._deposito = deposito

    def calcular_costo(self, horas, impuesto=0.19, descuento=0.0):
        self.validar_parametros(horas)
        # El depósito se suma al subtotal
        return self._aplicar(self._tarifa_hora * horas + self._deposito, impuesto, descuento)

    def describir(self):
        return f"Equipo '{self._nombre}' - ${self._tarifa_hora:,.0f}/h + depósito ${self._deposito:,.0f}"


class Asesoria(Servicio):
    def __init__(self, nombre, tarifa_hora, especialidad):
        super().__init__(nombre, tarifa_hora)
        self._especialidad = especialidad

    def validar_parametros(self, horas):
        super().validar_parametros(horas)
        if horas < 1:
            raise ServicioInvalidoError("La asesoría dura mínimo 1 hora.")

    def calcular_costo(self, horas, impuesto=0.19, descuento=0.0):
        self.validar_parametros(horas)
        recargo = 1.15  # recargo por especialización
        return self._aplicar(self._tarifa_hora * horas * recargo, impuesto, descuento)

    def describir(self):
        return f"Asesoría '{self._nombre}' ({self._especialidad}) - ${self._tarifa_hora:,.0f}/h"


# -------------------------------------------------------------------- RESERVA
class Reserva(Entidad):
    """Integra cliente, servicio, duración y estado."""
    PENDIENTE, CONFIRMADA, CANCELADA = "Pendiente", "Confirmada", "Cancelada"

    def __init__(self, cliente, servicio, horas):
        super().__init__()
        if cliente is None or servicio is None:
            raise ParametroFaltanteError("La reserva requiere cliente y servicio.")
        servicio.validar_parametros(horas)
        self.cliente, self.servicio, self.horas = cliente, servicio, horas
        self.estado = Reserva.PENDIENTE

    def confirmar(self):
        if self.estado != Reserva.PENDIENTE:
            raise OperacionNoPermitidaError(f"No se puede confirmar una reserva {self.estado}.")
        self.estado = Reserva.CONFIRMADA

    def cancelar(self):
        if self.estado == Reserva.CANCELADA:
            raise OperacionNoPermitidaError("La reserva ya estaba cancelada.")
        self.estado = Reserva.CANCELADA

    def procesar(self, descuento=0.0):
        """Calcula el costo usando try/except/else/finally y encadenamiento."""
        try:
            costo = self.servicio.calcular_costo(self.horas, descuento=descuento)
        except ServicioInvalidoError as e:
            # Encadenamiento: se relanza como ReservaError conservando la causa
            raise ReservaError(f"No se pudo procesar la reserva #{self.id}") from e
        else:
            self.confirmar()
            registrar_log("INFO", f"Reserva #{self.id} procesada. Costo ${costo:,.2f}")
            return costo
        finally:
            registrar_log("INFO", f"Fin de procesamiento de reserva #{self.id} ({self.estado})")

    def describir(self):
        return (f"Reserva #{self.id} [{self.estado}] {self.cliente.nombre} -> "
                f"{self.servicio.nombre} x {self.horas}h")


# --------------------------------------------------------------------- GESTOR
class Gestor:
    """Administra las listas internas de clientes, servicios y reservas."""

    def __init__(self):
        self.clientes, self.servicios, self.reservas = [], [], []

    def _seguro(self, accion, *args, **kwargs):
        """Ejecuta una acción; si falla, registra el error y el sistema continúa."""
        try:
            resultado = accion(*args, **kwargs)
        except ErrorSistema as e:
            causa = f" | causa: {e.__cause__}" if e.__cause__ else ""
            registrar_log("ERROR", f"{type(e).__name__}: {e}{causa}")
            print(f"  [Error controlado] {e}{causa}")
            return None
        except Exception as e:  # error inesperado: tampoco detiene la app
            registrar_log("CRITICO", f"{type(e).__name__}: {e}")
            print(f"  [Error inesperado] {e}")
            return None
        else:
            return resultado

    def agregar_cliente(self, *a):
        c = self._seguro(Cliente, *a)
        if c:
            self.clientes.append(c)
            registrar_log("INFO", f"Cliente creado: {c.describir()}")
        return c

    def agregar_servicio(self, clase, *a):
        s = self._seguro(clase, *a)
        if s:
            self.servicios.append(s)
            registrar_log("INFO", f"Servicio creado: {s.describir()}")
        return s

    def crear_reserva(self, cliente, servicio, horas):
        r = self._seguro(Reserva, cliente, servicio, horas)
        if r:
            self.reservas.append(r)
            registrar_log("INFO", f"Reserva creada: {r.describir()}")
        return r


# ------------------------------------------------------------------ SIMULACIÓN
def main():
    g = Gestor()
    print("== Clientes ==")
    ana = g.agregar_cliente("Ana Pérez", "ana@correo.com", "3001234567")
    g.agregar_cliente("Al", "mal-correo", "123")            # inválido
    luis = g.agregar_cliente("Luis Gómez", "luis@mail.com", "6021234567")

    print("== Servicios ==")
    sala = g.agregar_servicio(ReservaSala, "Sala Norte", 50000, 10)
    equipo = g.agregar_servicio(AlquilerEquipo, "Proyector", 20000, 30000)
    asesoria = g.agregar_servicio(Asesoria, "Asesoría en datos", 80000, "Analítica")
    g.agregar_servicio(ReservaSala, "Sala X", -5, 4)        # tarifa inválida

    print("== Reservas ==")
    reservas = [
        g.crear_reserva(ana, sala, 3),
        g.crear_reserva(luis, equipo, 2),
        g.crear_reserva(ana, asesoria, 0.5),   # asesoría < 1h
        g.crear_reserva(None, sala, 2),        # falta cliente
        g.crear_reserva(luis, sala, 20),       # sala > 12h
        g.crear_reserva(luis, asesoria, 2),
    ]

    print("== Procesamiento (polimorfismo) ==")
    for r in filter(None, reservas):
        costo = g._seguro(r.procesar, descuento=0.1)
        if costo is not None:
            print(f"  {r.describir()} -> ${costo:,.2f}")

    print("== Operaciones no permitidas ==")
    primera = reservas[0]
    g._seguro(primera.confirmar)       # ya confirmada
    g._seguro(primera.cancelar)        # ok
    g._seguro(primera.cancelar)        # ya cancelada

    print("== Sobrecarga de costos ==")
    print(f"  Sala 2h sin impuestos: ${sala.costo_base(2):,.2f}")
    print(f"  Sala 2h con 19% IVA y 5% desc.: ${sala.calcular_costo(2, 0.19, 0.05):,.2f}")
    print(f"\nSistema estable. Revisa {ARCHIVO_LOG} para el detalle de eventos y errores.")


if __name__ == "__main__":
    main()
