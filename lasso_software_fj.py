"""
Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación (213023) - Fase 4
Autor: Mauricio Lasso Ortiz
Sin bases de datos: solo objetos, listas y un archivo de logs.
"""
import re                                # Validar email y teléfono con patrones
from abc import ABC, abstractmethod      # Clases abstractas
from datetime import datetime            # Fecha y hora para los logs

ARCHIVO_LOG = "logs.txt"  # Único archivo usado: registro de eventos y errores


# ------------------------- LOGS -------------------------
def registrar_log(nivel, mensaje):
    """Escribe una línea en el archivo de logs."""
    marca = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Fecha y hora actual
    try:
        with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:  # "a" agrega al final
            f.write(f"[{marca}] {nivel}: {mensaje}\n")       # Guarda la línea
    except OSError as e:
        print(f"(No se pudo escribir el log: {e})")  # Si falla, el sistema sigue


# ------------------ EXCEPCIONES PERSONALIZADAS ------------------
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


# ------------------ CLASE ABSTRACTA GENERAL ------------------
class Entidad(ABC):
    """Entidad general del sistema (abstracción)."""
    _contador = 0  # Contador compartido para generar ids únicos

    def _init_(self):
        Entidad._contador += 1       # Aumenta el contador
        self._id = Entidad._contador  # Guarda el id (encapsulado)

    @property
    def id(self):
        return self._id  # Permite leer el id, no modificarlo

    @abstractmethod
    def describir(self):
        """Cada entidad debe describirse a sí misma."""


# ------------------------- CLIENTE -------------------------
class Cliente(Entidad):
    """Cliente con validaciones y datos personales encapsulados."""

    def _init_(self, nombre, email, telefono):
        super()._init_()                              # Genera el id
        self._nombre = self._validar_nombre(nombre)    # Atributos privados (_)
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
    def email(self, nuevo):
        self.__email = self._validar_email(nuevo)  # Valida antes de cambiar

    def describir(self):
        return f"Cliente #{self.id}: {self._nombre} ({self.email}, tel. {self._telefono})"


# ------------------------ SERVICIOS ------------------------
class Servicio(Entidad):
    """Clase abstracta Servicio; cada hija calcula su costo a su manera."""

    def _init_(self, nombre, tarifa_hora):
        super()._init_()
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
        """Costo con parámetros opcionales (sobrecarga con valores por defecto)."""

    def costo_base(self, horas):
        """Variante sin impuesto ni descuento (sobrecarga)."""
        return self.calcular_costo(horas, impuesto=0.0, descuento=0.0)

    def _aplicar(self, subtotal, impuesto, descuento):
        if not 0 <= descuento < 1 or impuesto < 0:
            raise ServicioInvalidoError("Impuesto o descuento fuera de rango.")
        return round(subtotal * (1 - descuento) * (1 + impuesto), 2)


class ReservaSala(Servicio):
    def _init_(self, nombre, tarifa_hora, capacidad):
        super()._init_(nombre, tarifa_hora)
        self._capacidad = capacidad

    def validar_parametros(self, horas):  # Método sobrescrito
        super().validar_parametros(horas)
        if horas > 12:
            raise ServicioInvalidoError("Una sala no se reserva por más de 12 horas.")

    def calcular_costo(self, horas, impuesto=0.19, descuento=0.0):
        self.validar_parametros(horas)
        return self._aplicar(self._tarifa_hora * horas, impuesto, descuento)

    def describir(self):
        return f"Sala '{self._nombre}' (capacidad {self._capacidad}) - ${self._tarifa_hora:,.0f}/h"


class AlquilerEquipo(Servicio):
    def _init_(self, nombre, tarifa_hora, deposito):
        super()._init_(nombre, tarifa_hora)
        self._deposito = deposito

    def calcular_costo(self, horas, impuesto=0.19, descuento=0.0):
        self.validar_parametros(horas)
        # El depósito se suma al subtotal
        return self._aplicar(self._tarifa_h