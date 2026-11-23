from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import singledispatchmethod
from typing import Any, List, Optional


# ==============================================================================
# CONFIGURACIÓN DE LOGGING (REGISTRO DE EVENTOS Y ERRORES EN ARCHIVO .LOG)
# ==============================================================================
def configurar_logger(archivo_log: str = "software_fj.log") -> logging.Logger:
    """Configura un logger que escribe eventos y errores en archivo y consola."""
    logger = logging.getLogger("SoftwareFJLogger")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formato = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.FileHandler(archivo_log, mode="a", encoding="utf-8")
        file_handler.setFormatter(formato)
        logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formato)
        logger.addHandler(stream_handler)

    return logger


logger = configurar_logger("software_fj.log")


# ==============================================================================
# EXCEPCIONES PERSONALIZADAS DEL DOMINIO (SOFTWARE FJ)
# ==============================================================================
class ErrorSistemaSoftwareFJ(Exception):
    """Excepción base del sistema para errores controlados de negocio."""


class DatoInvalidoError(ErrorSistemaSoftwareFJ):
    """Se lanza cuando un dato de entrada no cumple con las reglas de validación."""


class ParametroFaltanteError(ErrorSistemaSoftwareFJ):
    """Se lanza cuando falta un parámetro obligatorio o es vacío/nulo."""


class OperacionNoPermitidaError(ErrorSistemaSoftwareFJ):
    """Se lanza cuando se intenta una transición de estado o acción no válida."""


class ReservaInvalidaError(ErrorSistemaSoftwareFJ):
    """Se lanza cuando los datos o condiciones de una reserva son incorrectos."""


class ServicioNoDisponibleError(ErrorSistemaSoftwareFJ):
    """Se lanza cuando el servicio no está disponible o no tiene cupo/unidades."""


class CalculoInconsistenteError(ErrorSistemaSoftwareFJ):
    """Se lanza cuando el cálculo de tarifas, descuentos o impuestos resulta inválido."""


# ==============================================================================
# CLASE ABSTRACTA BASE PARA ENTIDADES DEL SISTEMA
# ==============================================================================
class EntidadSistema(ABC):
    """Clase abstracta general para entidades gestionadas en Software FJ."""

    def __init__(self, id_entidad: str) -> None:
        if not isinstance(id_entidad, str) or not id_entidad.strip():
            raise ParametroFaltanteError("El identificador de la entidad es obligatorio.")
        self._id_entidad = id_entidad.strip()
        self._fecha_creacion = datetime.now()

    @property
    def id_entidad(self) -> str:
        return self._id_entidad

    @property
    def fecha_creacion(self) -> datetime:
        return self._fecha_creacion

    @abstractmethod
    def resumen(self) -> str:
        """Retorna un resumen legible de la entidad."""


# ==============================================================================
# CLASE CLIENTE CON ENCAPSULACIÓN Y VALIDACIONES ESTRICTAS
# ==============================================================================
class Cliente(EntidadSistema):
    """Representa un cliente de Software FJ con atributos encapsulados y validados."""

    def __init__(self, id_cliente: str, nombre: str, correo: str, telefono: str) -> None:
        super().__init__(id_cliente)
        self._nombre = ""
        self._correo = ""
        self._telefono = ""

        self.nombre = nombre
        self.correo = correo
        self.telefono = telefono

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise DatoInvalidoError("El nombre del cliente debe tener al menos 3 caracteres.")
        self._nombre = valor.strip()

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor: str) -> None:
        if not isinstance(valor, str) or "@" not in valor or "." not in valor.split("@")[-1]:
            raise DatoInvalidoError(f"Correo electrónico inválido: '{valor}'.")
        self._correo = valor.strip().lower()

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        limpio = "".join(ch for ch in str(valor) if ch.isdigit())
        if len(limpio) < 7:
            raise DatoInvalidoError(f"Teléfono inválido: '{valor}'. Debe tener al menos 7 dígitos.")
        self._telefono = limpio

    def resumen(self) -> str:
        return f"Cliente[{self.id_entidad}] {self.nombre} ({self.correo}, Tel: {self.telefono})"


# ==============================================================================
# CLASE ABSTRACTA SERVICIO Y SERVICIOS ESPECIALIZADOS (POLIMORFISMO)
# ==============================================================================
class Servicio(EntidadSistema, ABC):
    """Clase abstracta para los servicios que ofrece Software FJ."""

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_base: float,
        disponible: bool = True,
    ) -> None:
        super().__init__(id_servicio)
        if not isinstance(nombre, str) or not nombre.strip():
            raise ParametroFaltanteError("El nombre del servicio es obligatorio.")
        if not isinstance(tarifa_base, (int, float)) or tarifa_base <= 0:
            raise DatoInvalidoError("La tarifa base del servicio debe ser un número mayor que 0.")

        self._nombre = nombre.strip()
        self._tarifa_base = float(tarifa_base)
        self._disponible = bool(disponible)

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def tarifa_base(self) -> float:
        return self._tarifa_base

    @property
    def disponible(self) -> bool:
        return self._disponible

    @disponible.setter
    def disponible(self, estado: bool) -> None:
        self._disponible = bool(estado)

    @abstractmethod
    def validar_parametros(self, duracion: int, **kwargs: Any) -> None:
        """Valida los parámetros específicos del servicio para una reserva."""

    @abstractmethod
    def calcular_costo_base(self, duracion: int, **kwargs: Any) -> float:
        """Calcula el costo base del servicio según su lógica especializada."""

    def calcular_costo(
        self,
        duracion: int,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.0,
        **kwargs: Any,
    ) -> float:
        """Calcula costo con descuento e impuesto opcionales."""
        try:
            if not isinstance(descuento_pct, (int, float)) or not (0 <= descuento_pct < 100):
                raise CalculoInconsistenteError("El descuento debe estar entre 0 y menos de 100%.")
            if not isinstance(impuesto_pct, (int, float)) or impuesto_pct < 0:
                raise CalculoInconsistenteError("El impuesto no puede ser negativo.")

            subtotal = self.calcular_costo_base(duracion, **kwargs)
            con_descuento = subtotal * (1.0 - float(descuento_pct) / 100.0)
            total = con_descuento * (1.0 + float(impuesto_pct) / 100.0)

            if total <= 0:
                raise CalculoInconsistenteError("El costo final calculado no es válido (<= 0).")
            return round(float(total), 2)
        except ErrorSistemaSoftwareFJ:
            raise
        except Exception as exc:
            raise CalculoInconsistenteError(
                "Error inesperado al calcular el costo del servicio."
            ) from exc

    @singledispatchmethod
    def aplicar_ajuste_especial(self, ajuste: Any) -> float:
        """Sobrecarga por tipo de ajuste."""
        raise DatoInvalidoError(f"Tipo de ajuste no soportado: {type(ajuste).__name__}.")

    @aplicar_ajuste_especial.register(float)
    @aplicar_ajuste_especial.register(int)
    def _(self, ajuste: float | int) -> float:
        factor = 1.0 + (float(ajuste) / 100.0)
        if factor <= 0:
            raise CalculoInconsistenteError("El ajuste porcentual produce un costo inválido.")
        return round(self._tarifa_base * factor, 2)

    @aplicar_ajuste_especial.register(dict)
    def _(self, ajuste: dict) -> float:
        if "monto_fijo" not in ajuste or not isinstance(ajuste["monto_fijo"], (int, float)):
            raise ParametroFaltanteError("El ajuste tipo diccionario requiere 'monto_fijo' numérico.")
        total = self._tarifa_base + float(ajuste["monto_fijo"])
        if total <= 0:
            raise CalculoInconsistenteError("El monto ajustado resulta menor o igual a cero.")
        return round(total, 2)

    @abstractmethod
    def describir(self) -> str:
        """Describe las características principales del servicio."""

    def resumen(self) -> str:
        estado_disp = "Disponible" if self._disponible else "No disponible"
        return f"Servicio[{self.id_entidad}] {self.nombre} (${self.tarifa_base:.2f}) - {estado_disp}"


class ReservaSala(Servicio):
    """Servicio especializado para reserva de salas."""

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_hora: float,
        capacidad_maxima: int,
        disponible: bool = True,
    ) -> None:
        super().__init__(id_servicio, nombre, tarifa_hora, disponible)
        if not isinstance(capacidad_maxima, int) or capacidad_maxima <= 0:
            raise DatoInvalidoError("La capacidad máxima de la sala debe ser un entero positivo.")
        self._capacidad_maxima = capacidad_maxima

    @property
    def capacidad_maxima(self) -> int:
        return self._capacidad_maxima

    def validar_parametros(self, duracion: int, **kwargs: Any) -> None:
        if not isinstance(duracion, int) or duracion <= 0:
            raise ReservaInvalidaError("La duración en horas para reserva de sala debe ser > 0.")
        asistentes = kwargs.get("asistentes", 1)
        if not isinstance(asistentes, int) or asistentes <= 0:
            raise DatoInvalidoError("El número de asistentes debe ser un entero positivo.")
        if asistentes > self._capacidad_maxima:
            raise ReservaInvalidaError(
                f"Los asistentes ({asistentes}) exceden la capacidad ({self._capacidad_maxima}) de '{self.nombre}'."
            )

    def calcular_costo_base(self, duracion: int, **kwargs: Any) -> float:
        self.validar_parametros(duracion, **kwargs)
        return self._tarifa_base * duracion

    def describir(self) -> str:
        return f"Sala '{self.nombre}' (Cap. máx.: {self._capacidad_maxima} personas, tarifa/hora: ${self._tarifa_base:.2f})"


class AlquilerEquipo(Servicio):
    """Servicio especializado para alquiler de equipos."""

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_dia: float,
        unidades_disponibles: int,
        disponible: bool = True,
    ) -> None:
        super().__init__(id_servicio, nombre, tarifa_dia, disponible and unidades_disponibles > 0)
        if not isinstance(unidades_disponibles, int) or unidades_disponibles < 0:
            raise DatoInvalidoError("Las unidades disponibles deben ser un entero mayor o igual a 0.")
        self._unidades_disponibles = unidades_disponibles
        if self._unidades_disponibles == 0:
            self._disponible = False

    @property
    def unidades_disponibles(self) -> int:
        return self._unidades_disponibles

    def validar_parametros(self, duracion: int, **kwargs: Any) -> None:
        if not isinstance(duracion, int) or duracion <= 0:
            raise ReservaInvalidaError("La duración en días para alquiler de equipo debe ser > 0.")
        unidades = kwargs.get("unidades", 1)
        if not isinstance(unidades, int) or unidades <= 0:
            raise DatoInvalidoError("La cantidad de unidades a alquilar debe ser un entero positivo.")
        if unidades > self._unidades_disponibles:
            raise ServicioNoDisponibleError(
                f"Unidades solicitadas ({unidades}) superan el stock ({self._unidades_disponibles}) de '{self.nombre}'."
            )

    def calcular_costo_base(self, duracion: int, **kwargs: Any) -> float:
        self.validar_parametros(duracion, **kwargs)
        unidades = kwargs.get("unidades", 1)
        return self._tarifa_base * duracion * unidades

    def describir(self) -> str:
        return f"Equipo '{self.nombre}' (Stock: {self._unidades_disponibles} und., tarifa/día: ${self._tarifa_base:.2f})"


class AsesoriaEspecializada(Servicio):
    """Servicio especializado para asesorías técnicas."""

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_sesion: float,
        especialidad: str,
        disponible: bool = True,
    ) -> None:
        super().__init__(id_servicio, nombre, tarifa_sesion, disponible)
        if not isinstance(especialidad, str) or not especialidad.strip():
            raise ParametroFaltanteError("La especialidad de la asesoría es obligatoria.")
        self._especialidad = especialidad.strip()

    @property
    def especialidad(self) -> str:
        return self._especialidad

    def validar_parametros(self, duracion: int, **kwargs: Any) -> None:
        if not isinstance(duracion, int) or duracion <= 0:
            raise ReservaInvalidaError("La cantidad de sesiones/horas de asesoría debe ser > 0.")

    def calcular_costo_base(self, duracion: int, **kwargs: Any) -> float:
        self.validar_parametros(duracion, **kwargs)
        return self._tarifa_base * duracion

    def describir(self) -> str:
        return f"Asesoría '{self.nombre}' [{self._especialidad}] (tarifa/sesión: ${self._tarifa_base:.2f})"


# ==============================================================================
# CLASE RESERVA Y GESTIÓN DE ESTADOS
# ==============================================================================
class EstadoReserva(str, Enum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"


@dataclass
class Reserva(EntidadSistema):
    """Integra Cliente, Servicio, duración, costo y ciclo de vida de la reserva."""

    id_reserva: str
    cliente: Cliente
    servicio: Servicio
    duracion: int
    parametros_extra: dict[str, Any]
    costo_total: float
    estado: EstadoReserva = EstadoReserva.PENDIENTE

    def __init__(
        self,
        id_reserva: str,
        cliente: Cliente,
        servicio: Servicio,
        duracion: int,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.0,
        parametros_extra: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(id_reserva)
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva requiere un objeto Cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva requiere un objeto Servicio válido.")
        if not servicio.disponible:
            raise ServicioNoDisponibleError(f"El servicio '{servicio.nombre}' no está disponible.")

        extras = parametros_extra or {}
        try:
            servicio.validar_parametros(duracion, **extras)
            costo = servicio.calcular_costo(
                duracion=duracion,
                descuento_pct=descuento_pct,
                impuesto_pct=impuesto_pct,
                **extras,
            )
        except ErrorSistemaSoftwareFJ as exc:
            raise ReservaInvalidaError(f"No se pudo crear la reserva '{id_reserva}': {exc}") from exc

        self.id_reserva = self._id_entidad
        self.cliente = cliente
        self.servicio = servicio
        self.duracion = duracion
        self.parametros_extra = extras
        self.costo_total = costo
        self.estado = EstadoReserva.PENDIENTE

    def confirmar(self) -> None:
        if self.estado == EstadoReserva.CANCELADA:
            raise OperacionNoPermitidaError(
                f"No se puede confirmar la reserva '{self.id_reserva}' porque está cancelada."
            )
        if self.estado == EstadoReserva.CONFIRMADA:
            raise OperacionNoPermitidaError(
                f"La reserva '{self.id_reserva}' ya se encuentra confirmada."
            )

        if isinstance(self.servicio, AlquilerEquipo):
            unidades = int(self.parametros_extra.get("unidades", 1))
            if unidades > self.servicio.unidades_disponibles:
                raise ServicioNoDisponibleError("Sin stock suficiente al momento de confirmar.")
            self.servicio._unidades_disponibles -= unidades
            if self.servicio._unidades_disponibles == 0:
                self.servicio.disponible = False

        self.estado = EstadoReserva.CONFIRMADA

    def cancelar(self) -> None:
        if self.estado == EstadoReserva.CANCELADA:
            raise OperacionNoPermitidaError(f"La reserva '{self.id_reserva}' ya fue cancelada.")

        if self.estado == EstadoReserva.CONFIRMADA and isinstance(self.servicio, AlquilerEquipo):
            unidades = int(self.parametros_extra.get("unidades", 1))
            self.servicio._unidades_disponibles += unidades
            self.servicio.disponible = True

        self.estado = EstadoReserva.CANCELADA

    def resumen(self) -> str:
        return (
            f"Reserva[{self.id_reserva}] | Cliente: {self.cliente.nombre} | "
            f"Servicio: {self.servicio.nombre} | Duración: {self.duracion} | "
            f"Total: ${self.costo_total:.2f} | Estado: {self.estado.value}"
        )


# ==============================================================================
# GESTOR CENTRAL EN MEMORIA (LISTAS INTERNAS, SIN BASE DE DATOS)
# ==============================================================================
class GestorSoftwareFJ:
    """Administra clientes, servicios y reservas mediante listas internas en memoria."""

    def __init__(self, nombre_empresa: str = "Software FJ") -> None:
        self.nombre_empresa = nombre_empresa
        self.clientes: List[Cliente] = []
        self.servicios: List[Servicio] = []
        self.reservas: List[Reserva] = []

    def registrar_cliente(self, id_cliente: str, nombre: str, correo: str, telefono: str) -> Cliente:
        if any(c.id_entidad == id_cliente.strip() for c in self.clientes):
            raise DatoInvalidoError(f"Ya existe un cliente con ID '{id_cliente}'.")
        cliente = Cliente(id_cliente, nombre, correo, telefono)
        self.clientes.append(cliente)
        return cliente

    def registrar_servicio(self, servicio: Servicio) -> Servicio:
        if not isinstance(servicio, Servicio):
            raise DatoInvalidoError("Solo se pueden registrar instancias válidas de Servicio.")
        if any(s.id_entidad == servicio.id_entidad for s in self.servicios):
            raise DatoInvalidoError(f"Ya existe un servicio con ID '{servicio.id_entidad}'.")
        self.servicios.append(servicio)
        return servicio

    def crear_y_procesar_reserva(
        self,
        id_reserva: str,
        id_cliente: str,
        id_servicio: str,
        duracion: int,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.0,
        parametros_extra: Optional[dict[str, Any]] = None,
        confirmar_inmediato: bool = True,
    ) -> Reserva:
        cliente = next((c for c in self.clientes if c.id_entidad == id_cliente), None)
        if cliente is None:
            raise ReservaInvalidaError(f"Cliente '{id_cliente}' no encontrado en el sistema.")

        servicio = next((s for s in self.servicios if s.id_entidad == id_servicio), None)
        if servicio is None:
            raise ReservaInvalidaError(f"Servicio '{id_servicio}' no encontrado en el sistema.")

        reserva = Reserva(
            id_reserva=id_reserva,
            cliente=cliente,
            servicio=servicio,
            duracion=duracion,
            descuento_pct=descuento_pct,
            impuesto_pct=impuesto_pct,
            parametros_extra=parametros_extra,
        )
        if confirmar_inmediato:
            reserva.confirmar()

        self.reservas.append(reserva)
        return reserva


# ==============================================================================
# EJECUCIÓN DE 10+ SIMULACIONES COMPLETAS (VÁLIDAS E INVÁLIDAS)
# ==============================================================================
def ejecutar_simulaciones() -> None:
    """Ejecuta 12 operaciones de prueba demostrando resiliencia y manejo de excepciones."""
    gestor = GestorSoftwareFJ("Software FJ")
    logger.info("Inicio de simulaciones para %s (sin base de datos).", gestor.nombre_empresa)

    simulaciones = [
        ("SIM-01", "Registro cliente válido", lambda: gestor.registrar_cliente(
            "CLI-01", "Laura Gómez", "laura.gomez@empresa.com", "3105551234"
        )),
        ("SIM-02", "Registro cliente inválido", lambda: gestor.registrar_cliente(
            "CLI-02", "A", "correo_sin_arroba", "12"
        )),
        ("SIM-03", "Registro segundo cliente válido", lambda: gestor.registrar_cliente(
            "CLI-03", "Carlos Méndez", "carlos.mendez@softwarefj.co", "3009876543"
        )),
        ("SIM-04", "Crear servicio ReservaSala", lambda: gestor.registrar_servicio(
            ReservaSala("SRV-SALA-1", "Sala de Conferencias A", 80.0, capacidad_maxima=15)
        )),
        ("SIM-05", "Crear servicio AlquilerEquipo", lambda: gestor.registrar_servicio(
            AlquilerEquipo("SRV-EQ-1", "Laptop Workstation i7", 45.0, unidades_disponibles=2)
        )),
        ("SIM-06", "Crear servicio AsesoriaEspecializada", lambda: gestor.registrar_servicio(
            AsesoriaEspecializada("SRV-ASE-1", "Auditoría de Arquitectura", 150.0, "Software")
        )),
        ("SIM-07", "Crear servicio inválido (tarifa negativa)", lambda: gestor.registrar_servicio(
            ReservaSala("SRV-BAD", "Sala Inválida", -50.0, capacidad_maxima=10)
        )),
        ("SIM-08", "Reserva exitosa de sala con descuento/impuesto", lambda: gestor.crear_y_procesar_reserva(
            id_reserva="RES-01",
            id_cliente="CLI-01",
            id_servicio="SRV-SALA-1",
            duracion=3,
            descuento_pct=10.0,
            impuesto_pct=19.0,
            parametros_extra={"asistentes": 10},
        )),
        ("SIM-09", "Reserva exitosa de asesoría", lambda: gestor.crear_y_procesar_reserva(
            id_reserva="RES-02",
            id_cliente="CLI-03",
            id_servicio="SRV-ASE-1",
            duracion=2,
            descuento_pct=0.0,
            impuesto_pct=0.0,
        )),
        ("SIM-10", "Reserva fallida por exceso de capacidad", lambda: gestor.crear_y_procesar_reserva(
            id_reserva="RES-03",
            id_cliente="CLI-01",
            id_servicio="SRV-SALA-1",
            duracion=2,
            parametros_extra={"asistentes": 30},
        )),
        ("SIM-11", "Reserva fallida por descuento inválido", lambda: gestor.crear_y_procesar_reserva(
            id_reserva="RES-04",
            id_cliente="CLI-03",
            id_servicio="SRV-ASE-1",
            duracion=1,
            descuento_pct=120.0,
        )),
        ("SIM-12", "Reserva fallida por cliente inexistente", lambda: gestor.crear_y_procesar_reserva(
            id_reserva="RES-05",
            id_cliente="CLI-999",
            id_servicio="SRV-ASE-1",
            duracion=1,
        )),
    ]

    for codigo_sim, descripcion, accion in simulaciones:
        try:
            resultado = accion()
        except ErrorSistemaSoftwareFJ as exc:
            logger.error("[%s] Falló '%s' -> %s", codigo_sim, descripcion, exc)
        else:
            detalle = resultado.resumen() if hasattr(resultado, "resumen") else str(resultado)
            logger.info("[%s] Éxito en '%s' -> %s", codigo_sim, descripcion, detalle)
        finally:
            logger.info("[%s] Ciclo de ejecución finalizado para: %s", codigo_sim, descripcion)

    logger.info(
        "Resumen final en memoria -> Clientes: %d | Servicios: %d | Reservas: %d",
        len(gestor.clientes),
        len(gestor.servicios),
        len(gestor.reservas),
    )


if __name__ == "__main__":
    ejecutar_simulaciones()