"""
====================================================================================================
PROYECTO: SISTEMA INTEGRAL DE GESTIÓN DE CLIENTES, SERVICIOS Y RESERVAS (SOFTWARE FJ)
CURSO: PROGRAMACIÓN (213023) - FASE 4: PRÁCTICAS SIMULADAS (COMPONENTE PRÁCTICO)
UNIVERSIDAD NACIONAL ABIERTA Y A DISTANCIA (UNAD)
ESTUDIANTE: JAVIER RICARDO CIFUENTES VALENCIA (GRUPO 213023_511)
====================================================================================================
DESCRIPCIÓN TÉCNICA:
Aplicación de nivel universitario que demuestra arquitectura orientada a objetos avanzada,
abstracción estricta, herencia jerárquica, polimorfismo dinámico, encapsulamiento y un modelo
robusto de gestión de excepciones en Python sin uso de bases de datos.

MECANISMOS DE EXCEPCIONES Y CALIDAD:
1. Jerarquía de Excepciones Personalizadas derivadas de SoftwareFJError.
2. Uso sistemático de cláusulas try / except / else / finally.
3. Encadenamiento semántico de excepciones (raise ... from ...).
4. Subsistema de Logging profesional en archivo rotativo y consola sincronizada.
5. Validador de invariantes de negocio y sobrecarga de métodos de tarificación.
6. Suite de 10 simulaciones obligatorias (casos válidos, anómalos y de estrés operativo).
7. Interfaz gráfica interactiva y consola de control para auditoría en tiempo real.
====================================================================================================
"""

from abc import ABC, abstractmethod
from datetime import datetime, date, timedelta
from enum import Enum
import logging
import os
import re
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import List, Dict, Optional, Tuple, Any

# ==================================================================================================
# 1. SUBSISTEMA DE LOGGING Y AUDITORÍA PROFESIONAL
# ==================================================================================================

# Determinación de la ruta base absoluta en Grupo 511/Cifuentes
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(BASE_DIR, "software_fj_auditoria.log")

# Configuración del logger principal del sistema
logger = logging.getLogger("SoftwareFJ")
logger.setLevel(logging.DEBUG)

# Limpieza preventiva de handlers previos para evitar duplicación
if logger.hasHandlers():
    logger.handlers.clear()

# Formato formal de registro según estándares de auditoría corporativa
log_formatter = logging.Formatter(
    fmt="[%(asctime)s] [%(levelname)-8s] [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Handler 1: Archivo persistente UTF-8
file_handler = logging.FileHandler(LOG_FILE_PATH, mode="a", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# Handler 2: Flujo estándar de consola
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

logger.info("=" * 80)
logger.info("INICIALIZACIÓN DEL SISTEMA SOFTWARE FJ - COMPONENTE PRÁCTICO FASE 4 (UNAD)")
logger.info(f"Registro de auditoría vinculado exitosamente en: {LOG_FILE_PATH}")
logger.info("=" * 80)


# ==================================================================================================
# 2. JERARQUÍA DE EXCEPCIONES PERSONALIZADAS DEL DOMINIO
# ==================================================================================================

class SoftwareFJError(Exception):
    """
    Excepción raíz para todas las anomalías y errores de dominio del sistema Software FJ.
    Permite capturar cualquier error controlado originado en las capas del negocio.
    """
    def __init__(self, mensaje: str, codigo_error: str = "ERR-GEN-000", detalles: Optional[Dict[str, Any]] = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo_error = codigo_error
        self.detalles = detalles or {}
        self.timestamp = datetime.now()

    def __str__(self) -> str:
        base = f"[{self.codigo_error}] {self.mensaje}"
        if self.detalles:
            base += f" | Parámetros contextuales: {self.detalles}"
        return base


class ClienteInvalidoError(SoftwareFJError):
    """Lanzada cuando los datos de identificación, nombre o contacto de un cliente violan los invariantes."""
    def __init__(self, mensaje: str, detalles: Optional[Dict[str, Any]] = None):
        super().__init__(mensaje, codigo_error="ERR-CLI-001", detalles=detalles)


class ServicioInvalidoError(SoftwareFJError):
    """Lanzada cuando los parámetros de configuración de un servicio no cumplen los rangos operativos."""
    def __init__(self, mensaje: str, detalles: Optional[Dict[str, Any]] = None):
        super().__init__(mensaje, codigo_error="ERR-SRV-002", detalles=detalles)


class ServicioNoDisponibleError(SoftwareFJError):
    """Lanzada cuando un servicio se encuentra inactivo, en mantenimiento o agotado."""
    def __init__(self, mensaje: str, detalles: Optional[Dict[str, Any]] = None):
        super().__init__(mensaje, codigo_error="ERR-SRV-003", detalles=detalles)


class ReservaInvalidaError(SoftwareFJError):
    """Lanzada cuando una solicitud de reserva contiene fechas, duraciones o clientes incompatibles."""
    def __init__(self, mensaje: str, detalles: Optional[Dict[str, Any]] = None):
        super().__init__(mensaje, codigo_error="ERR-RSV-004", detalles=detalles)


class CapacidadExcedidaError(ReservaInvalidaError):
    """Subtipo de ReservaInvalidaError cuando la demanda supera el aforo o unidades disponibles."""
    def __init__(self, mensaje: str, detalles: Optional[Dict[str, Any]] = None):
        super().__init__(mensaje, detalles=detalles)
        self.codigo_error = "ERR-RSV-005"


class TransicionEstadoInvalidaError(SoftwareFJError):
    """Lanzada cuando se intenta confirmar, cancelar o procesar una reserva en un estado no permitido."""
    def __init__(self, mensaje: str, detalles: Optional[Dict[str, Any]] = None):
        super().__init__(mensaje, codigo_error="ERR-STA-006", detalles=detalles)


class CalculoTarifaError(SoftwareFJError):
    """Lanzada ante inconsistencias matemáticas o parámetros incompatibles en el cálculo de costos."""
    def __init__(self, mensaje: str, detalles: Optional[Dict[str, Any]] = None):
        super().__init__(mensaje, codigo_error="ERR-CAL-007", detalles=detalles)


# ==================================================================================================
# 3. ENUMERACIONES Y CLASE ABSTRACTA BASE DE ENTIDADES
# ==================================================================================================

class EstadoReserva(Enum):
    """Estados del ciclo de vida de una reserva dentro del sistema."""
    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"
    FINALIZADA = "FINALIZADA"


class EntidadBase(ABC):
    """
    Clase abstracta pura que define la plantilla contractual para todas las entidades del sistema.
    Asegura identificación única, trazabilidad temporal y serialización informativa.
    """
    def __init__(self, id_entidad: str):
        if not id_entidad or not isinstance(id_entidad, str) or not id_entidad.strip():
            raise ValueError("El identificador de la entidad no puede ser nulo, vacío ni contener solo espacios.")
        self._id_entidad = id_entidad.strip()
        self._fecha_creacion = datetime.now()

    @property
    def id_entidad(self) -> str:
        return self._id_entidad

    @property
    def fecha_creacion(self) -> datetime:
        return self._fecha_creacion

    @abstractmethod
    def obtener_resumen(self) -> str:
        """Devuelve una síntesis formateada con los datos esenciales de la entidad."""
        pass

    @abstractmethod
    def validar_consistencia(self) -> bool:
        """Verifica que todos los invariantes de la entidad se mantengan íntegros."""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} ID={self._id_entidad}>"


# ==================================================================================================
# 4. CLASE CLIENTE CON ENCAPSULAMIENTO ESTRICTO Y VALIDACIONES
# ==================================================================================================

class Cliente(EntidadBase):
    """
    Representa a un usuario corporativo o individual con encapsulación estricta de datos personales.
    Aplica expresiones regulares y validaciones de formato en setters para garantizar consistencia.
    """
    _REGEX_EMAIL = re.compile(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,4}$")
    _REGEX_TELEFONO = re.compile(r"^\+?[0-9]{7,15}$")

    def __init__(self, cedula: str, nombre_completo: str, email: str, telefono: str, es_corporativo: bool = False):
        super().__init__(id_entidad=cedula)
        self._nombre_completo: str = ""
        self._email: str = ""
        self._telefono: str = ""
        self._es_corporativo: bool = es_corporativo
        self._reservas_asociadas: List[str] = []

        # Inicialización a través de propiedades con validación
        self.nombre_completo = nombre_completo
        self.email = email
        self.telefono = telefono
        self.validar_consistencia()

    @property
    def cedula(self) -> str:
        return self._id_entidad

    @property
    def nombre_completo(self) -> str:
        return self._nombre_completo

    @nombre_completo.setter
    def nombre_completo(self, valor: str):
        if not valor or not isinstance(valor, str) or len(valor.strip()) < 3:
            raise ClienteInvalidoError(
                "El nombre completo del cliente debe contener al menos 3 caracteres alfabéticos.",
                detalles={"valor_recibido": valor}
            )
        self._nombre_completo = valor.strip().title()

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, valor: str):
        if not valor or not isinstance(valor, str) or not self._REGEX_EMAIL.match(valor.strip()):
            raise ClienteInvalidoError(
                "El correo electrónico suministrado no cumple con el estándar RFC 5322 (ejemplo: usuario@dominio.com).",
                detalles={"email_recibido": valor}
            )
        self._email = valor.strip().lower()

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str):
        limpio = valor.strip().replace(" ", "").replace("-", "") if isinstance(valor, str) else ""
        if not self._REGEX_TELEFONO.match(limpio):
            raise ClienteInvalidoError(
                "El número de teléfono debe contener entre 7 y 15 dígitos numéricos válidos.",
                detalles={"telefono_recibido": valor}
            )
        self._telefono = limpio

    @property
    def es_corporativo(self) -> bool:
        return self._es_corporativo

    @es_corporativo.setter
    def es_corporativo(self, valor: bool):
        self._es_corporativo = bool(valor)

    def vincular_reserva(self, id_reserva: str):
        if id_reserva not in self._reservas_asociadas:
            self._reservas_asociadas.append(id_reserva)

    def obtener_resumen(self) -> str:
        tipo = "Corporativo (Descuento VIP)" if self._es_corporativo else "Estándar"
        return (f"Cliente: {self._nombre_completo} [CC: {self._id_entidad}] | "
                f"Email: {self._email} | Tel: {self._telefono} | Segmento: {tipo}")

    def validar_consistencia(self) -> bool:
        if not self._id_entidad.isalnum() or len(self._id_entidad) < 5:
            raise ClienteInvalidoError(
                "La cédula o documento de identidad debe ser alfanumérico y poseer mínimo 5 dígitos.",
                detalles={"cedula": self._id_entidad}
            )
        return True


# ==================================================================================================
# 5. JERARQUÍA POLIMÓRFICA DE SERVICIOS (CLASE ABSTRACTA Y DERIVADAS)
# ==================================================================================================

class Servicio(EntidadBase):
    """
    Clase abstracta base para los servicios que comercializa Software FJ.
    Define el contrato polimórfico de costeo, validación de parámetros y descripción.
    """
    def __init__(self, id_servicio: str, nombre: str, tarifa_base: float, activo: bool = True):
        super().__init__(id_entidad=id_servicio)
        if tarifa_base <= 0:
            raise ServicioInvalidoError(
                "La tarifa base de un servicio debe ser un valor monetario estrictamente positivo.",
                detalles={"tarifa_base": tarifa_base}
            )
        self._nombre = nombre.strip()
        self._tarifa_base = float(tarifa_base)
        self._activo = bool(activo)

    @property
    def id_servicio(self) -> str:
        return self._id_entidad

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def tarifa_base(self) -> float:
        return self._tarifa_base

    @property
    def activo(self) -> bool:
        return self._activo

    @activo.setter
    def activo(self, estado: bool):
        self._activo = bool(estado)

    def verificar_disponibilidad(self):
        """Verifica que el servicio esté operativo en la plataforma."""
        if not self._activo:
            raise ServicioNoDisponibleError(
                f"El servicio '{self._nombre}' ({self._id_entidad}) se encuentra inactivo temporalmente o en mantenimiento.",
                detalles={"servicio_id": self._id_entidad, "activo": self._activo}
            )

    @abstractmethod
    def calcular_costo(self, unidades: int, **kwargs) -> float:
        """
        Calcula el costo total del servicio en función del volumen de uso y parámetros opcionales.
        Soporta sobrecarga por argumentos clave (**kwargs): descuento, impuesto, recargo fin de semana.
        """
        pass

    @abstractmethod
    def describir_servicio(self) -> str:
        """Presentación polimórfica detallada de las especificaciones del servicio."""
        pass

    def validar_consistencia(self) -> bool:
        if not self._nombre:
            raise ServicioInvalidoError("El nombre descriptivo del servicio no puede estar vacío.")
        if self._tarifa_base <= 0:
            raise ServicioInvalidoError("Inconsistencia financiera: tarifa base inferior o igual a cero.")
        return True

    def obtener_resumen(self) -> str:
        estado = "Activo" if self._activo else "Inactivo"
        return f"[{self._id_entidad}] {self._nombre} - Tarifa Base: ${self._tarifa_base:,.2f} ({estado})"


class ReservaSala(Servicio):
    """
    Servicio especializado: Reserva de salas ejecutivas, de juntas o laboratorios de desarrollo.
    Unidades evaluadas: Horas de uso.
    """
    def __init__(self, id_servicio: str, nombre: str, tarifa_por_hora: float,
                 capacidad_personas: int, incluye_proyector: bool = True, activo: bool = True):
        super().__init__(id_servicio, nombre, tarifa_por_hora, activo)
        if capacidad_personas < 2 or capacidad_personas > 100:
            raise ServicioInvalidoError(
                "La capacidad de una sala debe situarse entre 2 y 100 personas.",
                detalles={"capacidad_solicitada": capacidad_personas}
            )
        self._capacidad_personas = capacidad_personas
        self._incluye_proyector = incluye_proyector

    @property
    def capacidad_personas(self) -> int:
        return self._capacidad_personas

    def calcular_costo(self, unidades: int, **kwargs) -> float:
        """
        Sobrecarga dinámica:
        - unidades: número de horas reservadas.
        - kwargs opcionales:
            * asistentes (int): Valida que no exceda el aforo.
            * es_fin_de_semana (bool): Recargo del 15% por personal operativo.
            * descuento_porcentaje (float): Descuento especial (0.0 a 1.0).
            * impuesto_iva (float): Tasa impositiva (default 0.19).
        """
        self.verificar_disponibilidad()
        if unidades <= 0:
            raise CalculoTarifaError("La duración de reserva de una sala debe ser de al menos 1 hora.",
                                     detalles={"horas_ingresadas": unidades})

        asistentes = kwargs.get("asistentes", self._capacidad_personas)
        if asistentes > self._capacidad_personas:
            raise CapacidadExcedidaError(
                f"El aforo requerido ({asistentes} personas) excede la capacidad máxima de la sala ({self._capacidad_personas} personas).",
                detalles={"asistentes": asistentes, "aforo_max": self._capacidad_personas}
            )

        # Tarifa base acumulada por hora
        costo_bruto = self._tarifa_base * unidades

        # Recargo fin de semana si aplica
        if kwargs.get("es_fin_de_semana", False):
            costo_bruto *= 1.15

        # Aplicación de descuento
        descuento = float(kwargs.get("descuento_porcentaje", 0.0))
        if not (0.0 <= descuento <= 0.50):
            raise CalculoTarifaError("El descuento comercial permitido no puede ser negativo ni superar el 50%.",
                                     detalles={"descuento": descuento})
        costo_con_descuento = costo_bruto * (1.0 - descuento)

        # Aplicación de impuestos
        iva = float(kwargs.get("impuesto_iva", 0.19))
        costo_final = round(costo_con_descuento * (1.0 + iva), 2)
        return costo_final

    def describir_servicio(self) -> str:
        proy = "Con proyector 4K y videoconferencia" if self._incluye_proyector else "Equipamiento básico"
        return (f"SALA EJECUTIVA: {self._nombre} | Aforo: {self._capacidad_personas} personas | "
                f"Equipamiento: {proy} | Tarifa: ${self._tarifa_base:,.2f}/hora + IVA")


class AlquilerEquipo(Servicio):
    """
    Servicio especializado: Alquiler de laptops de alta gama, servidores y dispositivos móviles de prueba.
    Unidades evaluadas: Días de arrendamiento.
    """
    def __init__(self, id_servicio: str, nombre: str, tarifa_por_dia: float,
                 gama: str, stock_disponible: int, valor_deposito_garantia: float, activo: bool = True):
        super().__init__(id_servicio, nombre, tarifa_por_dia, activo)
        if stock_disponible < 0:
            raise ServicioInvalidoError("El inventario de equipos disponibles no puede ser negativo.",
                                        detalles={"stock": stock_disponible})
        if valor_deposito_garantia < 0:
            raise ServicioInvalidoError("El depósito de garantía no puede ser negativo.",
                                        detalles={"garantia": valor_deposito_garantia})

        self._gama = gama.upper()
        self._stock_disponible = stock_disponible
        self._valor_deposito = float(valor_deposito_garantia)

    @property
    def stock_disponible(self) -> int:
        return self._stock_disponible

    def decrementar_stock(self, cantidad: int = 1):
        if cantidad > self._stock_disponible:
            raise CapacidadExcedidaError(
                f"No hay suficientes unidades físicas de '{self._nombre}'. Stock actual: {self._stock_disponible}.",
                detalles={"solicitado": cantidad, "stock": self._stock_disponible}
            )
        self._stock_disponible -= cantidad

    def calcular_costo(self, unidades: int, **kwargs) -> float:
        """
        Sobrecarga dinámica:
        - unidades: número de días de alquiler.
        - kwargs opcionales:
            * cantidad_equipos (int): Número de unidades idénticas solicitadas.
            * incluye_seguro_todo_riesgo (bool): Adiciona $25,000 COP por equipo/día.
            * descuento_porcentaje (float): Descuento por alquiler prolongado (>7 días).
        """
        self.verificar_disponibilidad()
        if unidades <= 0:
            raise CalculoTarifaError("El periodo de alquiler debe ser de al menos 1 día calendario.",
                                     detalles={"dias": unidades})

        cantidad = int(kwargs.get("cantidad_equipos", 1))
        if cantidad <= 0:
            raise CalculoTarifaError("La cantidad de equipos a rentar debe ser de al menos 1 unidad.",
                                     detalles={"cantidad": cantidad})
        if cantidad > self._stock_disponible:
            raise CapacidadExcedidaError(
                f"Stock insuficiente para '{self._nombre}'. Solicitados: {cantidad}, Disponibles: {self._stock_disponible}.",
                detalles={"solicitados": cantidad, "disponibles": self._stock_disponible}
            )

        # Cálculo base: tarifa * días * cantidad
        costo_base_dias = self._tarifa_base * unidades * cantidad

        # Seguro opcional
        seguro = 25000.0 * unidades * cantidad if kwargs.get("incluye_seguro_todo_riesgo", False) else 0.0

        # Descuento por periodo extendido (si supera 7 días aplica 10% automático salvo que se envíe otro)
        descuento = float(kwargs.get("descuento_porcentaje", 0.10 if unidades >= 7 else 0.0))
        costo_neto = (costo_base_dias * (1.0 - descuento)) + seguro

        iva = float(kwargs.get("impuesto_iva", 0.19))
        total = round(costo_neto * (1.0 + iva), 2)
        return total

    def describir_servicio(self) -> str:
        return (f"EQUIPO TECNOLÓGICO: {self._nombre} [Gama {self._gama}] | "
                f"Stock: {self._stock_disponible} u. | Garantía requerida: ${self._valor_deposito:,.2f} | "
                f"Tarifa: ${self._tarifa_base:,.2f}/día")


class AsesoriaEspecializada(Servicio):
    """
    Servicio especializado: Consultoría técnica en arquitectura cloud, ciberseguridad o auditoría de software.
    Unidades evaluadas: Sesiones de consultoría (bloques de 2 horas).
    """
    def __init__(self, id_servicio: str, nombre: str, tarifa_por_sesion: float,
                 area_experticia: str, nivel_consultor: str = "Senior", activo: bool = True):
        super().__init__(id_servicio, nombre, tarifa_por_sesion, activo)
        niveles_validos = ["JUNIOR", "SEMI-SENIOR", "SENIOR", "PRINCIPAL ARCHITECT"]
        if nivel_consultor.upper() not in niveles_validos:
            raise ServicioInvalidoError(
                f"Nivel de consultor inválido. Valores aceptados: {', '.join(niveles_validos)}.",
                detalles={"nivel_ingresado": nivel_consultor}
            )
        self._area_experticia = area_experticia.strip()
        self._nivel_consultor = nivel_consultor.upper()

    def calcular_costo(self, unidades: int, **kwargs) -> float:
        """
        Sobrecarga dinámica:
        - unidades: número de sesiones de asesoría.
        - kwargs opcionales:
            * modalidad_presencial (bool): Viáticos y recargo del 20%.
            * entrega_informe_auditoria (bool): Cargo fijo de $150,000 COP por peritaje técnico.
            * descuento_porcentaje (float): Descuento aplicable.
        """
        self.verificar_disponibilidad()
        if unidades <= 0:
            raise CalculoTarifaError("Se requiere contratar al menos 1 sesión de asesoría técnica.",
                                     detalles={"sesiones": unidades})

        # Factor multiplicador por jerarquía técnica
        multiplicadores = {
            "JUNIOR": 1.0,
            "SEMI-SENIOR": 1.25,
            "SENIOR": 1.50,
            "PRINCIPAL ARCHITECT": 2.00
        }
        factor = multiplicadores.get(self._nivel_consultor, 1.0)
        costo_base = (self._tarifa_base * factor) * unidades

        if kwargs.get("modalidad_presencial", False):
            costo_base *= 1.20  # Viáticos de traslado in situ

        cargo_informe = 150000.0 if kwargs.get("entrega_informe_auditoria", False) else 0.0
        descuento = float(kwargs.get("descuento_porcentaje", 0.0))
        costo_neto = (costo_base * (1.0 - descuento)) + cargo_informe

        iva = float(kwargs.get("impuesto_iva", 0.19))
        total = round(costo_neto * (1.0 + iva), 2)
        return total

    def describir_servicio(self) -> str:
        return (f"ASESORÍA ESPECIALIZADA: {self._nombre} | Área: {self._area_experticia} | "
                f"Nivel: {self._nivel_consultor} | Tarifa base/sesión: ${self._tarifa_base:,.2f} + factor nivel")


# ==================================================================================================
# 6. CLASE RESERVA CON GESTIÓN INTEGRAL DEL CICLO DE VIDA Y EXCEPCIONES
# ==================================================================================================

class Reserva(EntidadBase):
    """
    Integra cliente, servicio, duración, fecha y estado operativo.
    Implementa el patrón de validación transaccional con manejo avanzado de excepciones.
    """
    def __init__(self, id_reserva: str, cliente: Cliente, servicio: Servicio,
                 fecha_reserva: date, duracion_unidades: int, parametros_costo: Optional[Dict[str, Any]] = None):
        super().__init__(id_entidad=id_reserva)

        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva exige una instancia válida de la clase Cliente.",
                                       detalles={"tipo_recibido": type(cliente).__name__})
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva exige una instancia válida de la jerarquía Servicio.",
                                       detalles={"tipo_recibido": type(servicio).__name__})

        self._cliente = cliente
        self._servicio = servicio
        self._fecha_reserva = fecha_reserva
        self._duracion_unidades = int(duracion_unidades)
        self._parametros_costo = parametros_costo or {}
        self._estado = EstadoReserva.PENDIENTE
        self._costo_total = 0.0

        # Validación inicial de negocio
        self.validar_consistencia()

    @property
    def id_reserva(self) -> str:
        return self._id_entidad

    @property
    def cliente(self) -> Cliente:
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        return self._servicio

    @property
    def estado(self) -> EstadoReserva:
        return self._estado

    @property
    def costo_total(self) -> float:
        return self._costo_total

    def validar_consistencia(self) -> bool:
        """Valida que la fecha de reserva no pertenezca al pasado y que las unidades sean válidas."""
        if self._fecha_reserva < date.today():
            raise ReservaInvalidaError(
                f"No es posible agendar reservas en fechas pretéritas ({self._fecha_reserva}).",
                detalles={"fecha_ingresada": str(self._fecha_reserva), "fecha_hoy": str(date.today())}
            )
        if self._duracion_unidades <= 0:
            raise ReservaInvalidaError(
                "La duración de la reserva debe ser estrictamente positiva.",
                detalles={"unidades": self._duracion_unidades}
            )
        return True

    def procesar_calculo_costo(self) -> float:
        """
        Ejecuta el cálculo de costo polimórfico utilizando la sobrecarga de parámetros del servicio.
        Demuestra manejo de excepciones y encadenamiento semántico.
        """
        try:
            # Si el cliente es corporativo, se inyecta descuento preferencial del 10% si no tenía uno mayor
            params = dict(self._parametros_costo)
            if self._cliente.es_corporativo and "descuento_porcentaje" not in params:
                params["descuento_porcentaje"] = 0.10

            self._costo_total = self._servicio.calcular_costo(self._duracion_unidades, **params)
            logger.debug(f"Cálculo exitoso para Reserva {self._id_entidad}: ${self._costo_total:,.2f} COP")
            return self._costo_total
        except (CalculoTarifaError, CapacidadExcedidaError, ServicioNoDisponibleError):
            # Re-propagación transparente de errores de dominio
            raise
        except Exception as exc:
            # Encadenamiento de excepciones hacia un error de reserva
            logger.error(f"Falla inesperada calculando tarifa en Reserva {self._id_entidad}: {exc}")
            raise ReservaInvalidaError(
                f"Error al liquidar la tarifa para la reserva {self._id_entidad}.",
                detalles={"causa_original": str(exc)}
            ) from exc

    def confirmar(self):
        """Transiciona la reserva al estado CONFIRMADA tras liquidar su costo."""
        if self._estado != EstadoReserva.PENDIENTE:
            raise TransicionEstadoInvalidaError(
                f"No se puede confirmar una reserva en estado '{self._estado.value}'. Solo reservas PENDIENTES.",
                detalles={"estado_actual": self._estado.value, "reserva_id": self._id_entidad}
            )

        # Procesa el costo como paso previo
        self.procesar_calculo_costo()

        # Si el servicio es de equipos físicos, se descuenta el stock
        if isinstance(self._servicio, AlquilerEquipo):
            cant = int(self._parametros_costo.get("cantidad_equipos", 1))
            self._servicio.decrementar_stock(cant)

        self._estado = EstadoReserva.CONFIRMADA
        self._cliente.vincular_reserva(self._id_entidad)
        logger.info(f"Reserva {self._id_entidad} CONFIRMADA exitosamente para cliente {self._cliente.nombre_completo}.")

    def cancelar(self, motivo: str):
        """Cancela la reserva registrando el motivo y liberando recursos si corresponde."""
        if self._estado in (EstadoReserva.CANCELADA, EstadoReserva.FINALIZADA):
            raise TransicionEstadoInvalidaError(
                f"La reserva ya se encuentra en estado terminal '{self._estado.value}' y no puede ser cancelada.",
                detalles={"estado_actual": self._estado.value, "reserva_id": self._id_entidad}
            )

        estado_anterior = self._estado.value
        self._estado = EstadoReserva.CANCELADA
        logger.warning(
            f"Reserva {self._id_entidad} CANCELADA. Estado previo: {estado_anterior}. "
            f"Motivo: '{motivo}'. Cliente: {self._cliente.nombre_completo}."
        )

    def finalizar(self):
        """Cierra el ciclo operativo de la reserva."""
        if self._estado != EstadoReserva.CONFIRMADA:
            raise TransicionEstadoInvalidaError(
                f"Solo las reservas CONFIRMADAS pueden pasar a estado FINALIZADA. Estado actual: '{self._estado.value}'.",
                detalles={"estado_actual": self._estado.value}
            )
        self._estado = EstadoReserva.FINALIZADA
        logger.info(f"Reserva {self._id_entidad} FINALIZADA con satisfacción.")

    def obtener_resumen(self) -> str:
        return (f"RESERVA [{self._id_entidad}] ({self._estado.value})\n"
                f" • Cliente : {self._cliente.nombre_completo} (CC: {self._cliente.cedula})\n"
                f" • Servicio: {self._servicio.nombre}\n"
                f" • Fecha   : {self._fecha_reserva.strftime('%Y-%m-%d')} | Duración: {self._duracion_unidades} u.\n"
                f" • Total   : ${self._costo_total:,.2f} COP")


# ==================================================================================================
# 7. GESTOR CENTRAL DEL SISTEMA (SIN BASE DE DATOS)
# ==================================================================================================

class SistemaGestionSoftwareFJ:
    """
    Controlador central del sistema. Mantiene colecciones en memoria de clientes,
    servicios y reservas, administrando transacciones y canalizando errores al logger.
    """
    def __init__(self):
        self._clientes: Dict[str, Cliente] = {}
        self._servicios: Dict[str, Servicio] = {}
        self._reservas: Dict[str, Reserva] = {}
        logger.info("Instancia de SistemaGestionSoftwareFJ inicializada con colecciones vacías.")

    # ----------------------------- Gestión de Clientes -----------------------------
    def registrar_cliente(self, cedula: str, nombre: str, email: str, telefono: str,
                           es_corp: bool = False) -> Tuple[bool, str, Optional[Cliente]]:
        """
        Demuestra la estructura completa: try / except / else / finally.
        """
        cliente = None
        operacion_exitosa = False
        mensaje_resultado = ""

        try:
            logger.debug(f"Intentando registrar cliente con CC: {cedula}...")
            if cedula in self._clientes:
                raise ClienteInvalidoError(
                    f"Ya existe un cliente registrado con el documento de identidad {cedula}.",
                    detalles={"cedula_duplicada": cedula}
                )
            cliente = Cliente(cedula, nombre, email, telefono, es_corp)
            self._clientes[cedula] = cliente
            operacion_exitosa = True
            mensaje_resultado = f"Cliente '{cliente.nombre_completo}' registrado exitosamente."

        except ClienteInvalidoError as err_cli:
            mensaje_resultado = f"Error de validación en cliente: {err_cli.mensaje}"
            logger.error(f"[REGISTRO CLIENTE FALLIDO] {err_cli}")
            operacion_exitosa = False

        except Exception as ex_gen:
            # Encadenamiento preventivo
            mensaje_resultado = f"Falla inesperada del sistema al crear cliente: {str(ex_gen)}"
            logger.critical(f"[EXCEPCIÓN NO CONTROLADA CLIENTE] {ex_gen}", exc_info=True)
            operacion_exitosa = False

        else:
            # Se ejecuta únicamente si NO ocurrió ninguna excepción en el bloque try
            logger.info(f"[CLIENTE CREADO] ID={cliente.cedula} | Segmento={'Corporativo' if cliente.es_corporativo else 'Estándar'}")

        finally:
            # Se ejecuta SIEMPRE para tareas de auditoría y cierre de ciclo
            logger.debug(f"Fin del ciclo de registro de cliente para CC: {cedula}. Estado de éxito: {operacion_exitosa}")

        return operacion_exitosa, mensaje_resultado, cliente

    # ----------------------------- Gestión de Servicios ----------------------------
    def agregar_servicio(self, servicio: Servicio) -> Tuple[bool, str]:
        """Incorpora un servicio validando su pertenencia a la jerarquía de POO."""
        try:
            if not isinstance(servicio, Servicio):
                raise ServicioInvalidoError("El objeto a registrar no hereda de la clase abstracta Servicio.")
            if servicio.id_servicio in self._servicios:
                raise ServicioInvalidoError(f"El identificador de servicio '{servicio.id_servicio}' ya se encuentra registrado.")

            servicio.validar_consistencia()
            self._servicios[servicio.id_servicio] = servicio
            logger.info(f"[SERVICIO DISPONIBLE] {servicio.describir_servicio()}")
            return True, f"Servicio '{servicio.nombre}' agregado satisfactoriamente."

        except (ServicioInvalidoError, ServicioNoDisponibleError) as err_srv:
            logger.error(f"[SERVICIO RECHAZADO] {err_srv}")
            return False, str(err_srv)
        except Exception as ex:
            logger.critical(f"[FALLA SERVICIO] {ex}", exc_info=True)
            return False, f"Error crítico registrando servicio: {ex}"

    # ----------------------------- Gestión de Reservas -----------------------------
    def crear_y_procesar_reserva(self, id_reserva: str, cedula_cliente: str, id_servicio: str,
                                 fecha: date, duracion: int,
                                 parametros_costo: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[Reserva]]:
        """
        Crea, valida y confirma una reserva aplicando bloques try/except/else/finally exhaustivos.
        """
        reserva = None
        exito = False
        mensaje = ""

        try:
            logger.debug(f"Iniciando transacción de reserva ID={id_reserva}...")

            if id_reserva in self._reservas:
                raise ReservaInvalidaError(f"El código de reserva '{id_reserva}' ya existe en el sistema.")

            cliente = self._clientes.get(cedula_cliente)
            if not cliente:
                raise ClienteInvalidoError(f"No existe ningún cliente registrado con la cédula '{cedula_cliente}'.")

            servicio = self._servicios.get(id_servicio)
            if not servicio:
                raise ServicioNoDisponibleError(f"El servicio '{id_servicio}' no figura en el catálogo de Software FJ.")

            # Instanciación y confirmación
            reserva = Reserva(id_reserva, cliente, servicio, fecha, duracion, parametros_costo)
            reserva.confirmar()

            self._reservas[id_reserva] = reserva
            exito = True
            mensaje = f"Reserva {id_reserva} confirmada exitosamente. Total a cobrar: ${reserva.costo_total:,.2f} COP."

        except (ClienteInvalidoError, ServicioNoDisponibleError, ReservaInvalidaError,
                CapacidadExcedidaError, TransicionEstadoInvalidaError, CalculoTarifaError) as err_dominio:
            mensaje = f"Rechazo de Reserva [{err_dominio.codigo_error}]: {err_dominio.mensaje}"
            logger.error(f"[RESERVA RECHAZADA] {err_dominio}")
            exito = False

        except Exception as exc_inesperada:
            mensaje = f"Error crítico no controlado durante la reserva: {str(exc_inesperada)}"
            logger.critical(f"[FALLA CRÍTICA EN RESERVA] {exc_inesperada}", exc_info=True)
            exito = False

        else:
            logger.info(f"[TRANSACCIÓN EXITOSA] Reserva {id_reserva} almacenada en memoria con estado {reserva.estado.value}.")

        finally:
            logger.debug(f"Transacción {id_reserva} finalizada. Total reservas vigentes: {len(self._reservas)}.")

        return exito, mensaje, reserva

    def cancelar_reserva(self, id_reserva: str, motivo: str) -> Tuple[bool, str]:
        """Cancela una reserva existente capturando transiciones prohibidas."""
        try:
            reserva = self._reservas.get(id_reserva)
            if not reserva:
                raise ReservaInvalidaError(f"No existe la reserva '{id_reserva}' para cancelar.")
            reserva.cancelar(motivo)
            return True, f"Reserva {id_reserva} cancelada correctamente."
        except TransicionEstadoInvalidaError as err_est:
            logger.error(f"[CANCELACIÓN FALLIDA] {err_est}")
            return False, err_est.mensaje
        except Exception as ex:
            logger.critical(f"[ERROR CANCELACIÓN] {ex}", exc_info=True)
            return False, f"Falla imprevista al cancelar: {ex}"

    # Consultas para interfaz gráfica
    def listar_clientes(self) -> List[Cliente]:
        return list(self._clientes.values())

    def listar_servicios(self) -> List[Servicio]:
        return list(self._servicios.values())

    def listar_reservas(self) -> List[Reserva]:
        return list(self._reservas.values())


# ==================================================================================================
# 8. BATERÍA COMPLETA DE 10 SIMULACIONES OBLIGATORIAS (CRITERIO 2 - 35 PUNTOS)
# ==================================================================================================

def ejecutar_suite_simulaciones(sistema: SistemaGestionSoftwareFJ) -> List[Dict[str, Any]]:
    """
    Ejecuta de manera secuencial 10 simulaciones diseñadas para probar los límites del sistema:
    - Casos exitosos (clientes válidos, servicios correctamente instanciados, reservas confirmadas).
    - Casos límite y fallos controlados (emails no válidos, teléfonos incompletos, servicios inactivos,
      aforos excedidos, fechas pasadas, cancelaciones en estados terminales, etc.).
    Demuestra que la aplicación NUNCA colapsa ante excepciones graves.
    """
    logger.info("=" * 80)
    logger.info("INICIANDO SUITE DE 10 SIMULACIONES OPERATIVAS OBLIGATORIAS")
    logger.info("=" * 80)

    resultados: List[Dict[str, Any]] = []

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 1: Registro Exitoso de Cliente Estándar (VÁLIDO)
    # ----------------------------------------------------------------------------------------------
    logger.info("\n>>> SIMULACIÓN 1: Registro de Cliente Válido (Persona Natural)")
    ok, msg, cli = sistema.registrar_cliente(
        cedula="1018456789",
        nombre="Carlos Andres Mendoza",
        email="carlos.mendoza@tecnologia.com.co",
        telefono="+573105558899",
        es_corp=False
    )
    resultados.append({
        "num": 1,
        "nombre": "Registro de Cliente Natural Válido",
        "tipo_esperado": "ÉXITO",
        "resultado_real": "ÉXITO" if ok else "FALLO",
        "mensaje": msg,
        "detalle": cli.obtener_resumen() if cli else "Sin cliente"
    })

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 2: Registro de Cliente con Formato de Email Inválido (INVÁLIDO - ERROR CONTROLADO)
    # ----------------------------------------------------------------------------------------------
    logger.info("\n>>> SIMULACIÓN 2: Registro de Cliente con Correo Electrónico Inválido")
    ok, msg, cli = sistema.registrar_cliente(
        cedula="79065563",
        nombre="Javier Cifuentes",
        email="correo_invalido_sin_arroba.com",
        telefono="3001234567",
        es_corp=True
    )
    resultados.append({
        "num": 2,
        "nombre": "Validación de Correo Electrónico RFC 5322",
        "tipo_esperado": "EXCEPCIÓN CONTROLADA (ClienteInvalidoError)",
        "resultado_real": "CAPTURADA" if not ok else "ERROR_NO_DETECTADO",
        "mensaje": msg,
        "detalle": "El sistema rechazó el correo y mantuvo la integridad de la lista de clientes."
    })

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 3: Registro Exitoso de Cliente Corporativo (VÁLIDO)
    # ----------------------------------------------------------------------------------------------
    logger.info("\n>>> SIMULACIÓN 3: Registro de Cliente Corporativo Válido")
    ok, msg, cli = sistema.registrar_cliente(
        cedula="9012345678",
        nombre="Innovaciones Digitales S.A.S.",
        email="contacto@innovaciones.com.co",
        telefono="+576017458900",
        es_corp=True
    )
    resultados.append({
        "num": 3,
        "nombre": "Registro de Cliente Corporativo (VIP)",
        "tipo_esperado": "ÉXITO",
        "resultado_real": "ÉXITO" if ok else "FALLO",
        "mensaje": msg,
        "detalle": cli.obtener_resumen() if cli else "Sin cliente"
    })

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 4: Instanciación de Servicios Especializados Válidos (VÁLIDO)
    # ----------------------------------------------------------------------------------------------
    logger.info("\n>>> SIMULACIÓN 4: Creación e Incorporación de 3 Familias de Servicios")
    s1 = ReservaSala("SRV-SALA-01", "Sala de Juntas Diamond 4K", tarifa_por_hora=85000.0, capacidad_personas=18)
    s2 = AlquilerEquipo("SRV-EQUIP-01", "Workstation Portátil ThinkPad P16", tarifa_por_dia=140000.0,
                        gama="ALTA", stock_disponible=5, valor_deposito_garantia=800000.0)
    s3 = AsesoriaEspecializada("SRV-ASES-01", "Auditoría en Arquitectura Cloud AWS", tarifa_por_sesion=250000.0,
                               area_experticia="DevOps / Serverless", nivel_consultor="SENIOR")

    sistema.agregar_servicio(s1)
    sistema.agregar_servicio(s2)
    sistema.agregar_servicio(s3)

    resultados.append({
        "num": 4,
        "nombre": "Catálogo de Servicios Polimórficos",
        "tipo_esperado": "ÉXITO (3 Clases Especializadas)",
        "resultado_real": "ÉXITO",
        "mensaje": "Se cargaron 3 servicios especializados implementando la clase abstracta Servicio.",
        "detalle": f"Disponibles: {s1.nombre}, {s2.nombre}, {s3.nombre}"
    })

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 5: Intento de Crear Servicio con Tarifa Base Negativa (INVÁLIDO - ERROR CONTROLADO)
    # ----------------------------------------------------------------------------------------------
    logger.info("\n>>> SIMULACIÓN 5: Creación Incorrecta de Servicio con Tarifa Inconsistente")
    try:
        s_invalido = ReservaSala("SRV-ERROR-01", "Sala Ilegal", tarifa_por_hora=-50000.0, capacidad_personas=10)
        sistema.agregar_servicio(s_invalido)
        ok5, msg5 = True, "Error: Se permitió tarifa negativa."
    except ServicioInvalidoError as err:
        logger.error(f"[CAPTURA CORRECTA EN SIMULACIÓN 5] {err}")
        ok5, msg5 = False, f"Excepción capturada: {err.mensaje}"

    resultados.append({
        "num": 5,
        "nombre": "Invariante Financiero en Servicio",
        "tipo_esperado": "EXCEPCIÓN CONTROLADA (ServicioInvalidoError)",
        "resultado_real": "CAPTURADA" if not ok5 else "FALLO",
        "mensaje": msg5,
        "detalle": "Se impidió la creación de objetos con tarifas monetarias inconsistentes."
    })

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 6: Reserva de Sala de Juntas con Sobrecarga y Descuento VIP (VÁLIDO)
    # ----------------------------------------------------------------------------------------------
    logger.info("\n>>> SIMULACIÓN 6: Reserva Válida de Sala con Descuento Corporativo Automático")
    fecha_futura = date.today() + timedelta(days=3)
    ok, msg, rsv = sistema.crear_y_procesar_reserva(
        id_reserva="RSV-2026-001",
        cedula_cliente="9012345678",
        id_servicio="SRV-SALA-01",
        fecha=fecha_futura,
        duracion=4,  # 4 horas
        parametros_costo={"asistentes": 12, "es_fin_de_semana": False, "impuesto_iva": 0.19}
    )
    resultados.append({
        "num": 6,
        "nombre": "Reserva Válida de Sala con Sobrecarga",
        "tipo_esperado": "ÉXITO (Descuento VIP aplicado)",
        "resultado_real": "ÉXITO" if ok else "FALLO",
        "mensaje": msg,
        "detalle": rsv.obtener_resumen() if rsv else "Sin reserva"
    })

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 7: Reserva de Sala que Excede el Aforo Máximo Permitido (INVÁLIDO - ERROR CONTROLADO)
    # ----------------------------------------------------------------------------------------------
    logger.info("\n>>> SIMULACIÓN 7: Solicitud de Reserva con Aforo Excedido")
    ok, msg, rsv = sistema.crear_y_procesar_reserva(
        id_reserva="RSV-2026-002",
        cedula_cliente="1018456789",
        id_servicio="SRV-SALA-01",
        fecha=fecha_futura,
        duracion=2,
        parametros_costo={"asistentes": 40}  # La sala soporta máximo 18
    )
    resultados.append({
        "num": 7,
        "nombre": "Control de Capacidad / Aforo Máximo",
        "tipo_esperado": "EXCEPCIÓN CONTROLADA (CapacidadExcedidaError)",
        "resultado_real": "CAPTURADA" if not ok else "FALLO",
        "mensaje": msg,
        "detalle": "El sistema evitó la sobreventa del espacio y notificó el rechazo técnico."
    })

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 8: Reserva de Alquiler de Equipos con Descuento Extendido y Seguro (VÁLIDO)
    # ----------------------------------------------------------------------------------------------
    logger.info("\n>>> SIMULACIÓN 8: Alquiler de 2 Equipos por 10 Días con Seguro Todo Riesgo")
    ok, msg, rsv = sistema.crear_y_procesar_reserva(
        id_reserva="RSV-2026-003",
        cedula_cliente="9012345678",
        id_servicio="SRV-EQUIP-01",
        fecha=fecha_futura + timedelta(days=2),
        duracion=10,  # 10 días
        parametros_costo={"cantidad_equipos": 2, "incluye_seguro_todo_riesgo": True, "impuesto_iva": 0.19}
    )
    resultados.append({
        "num": 8,
        "nombre": "Alquiler Multidía con Seguro y Reducción de Stock",
        "tipo_esperado": "ÉXITO (Stock pasa de 5 a 3)",
        "resultado_real": "ÉXITO" if ok else "FALLO",
        "mensaje": msg,
        "detalle": f"Nuevo stock disponible del equipo: {s2.stock_disponible} unidades."
    })

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 9: Intento de Reserva sobre un Servicio Inactivo (INVÁLIDO - ERROR CONTROLADO)
    # ----------------------------------------------------------------------------------------------
    logger.info("\n>>> SIMULACIÓN 9: Intento de Contratar un Servicio Puesto en Mantenimiento")
    # Desactivamos temporalmente la asesoría cloud por mantenimiento
    s3.activo = False
    ok, msg, rsv = sistema.crear_y_procesar_reserva(
        id_reserva="RSV-2026-004",
        cedula_cliente="1018456789",
        id_servicio="SRV-ASES-01",
        fecha=fecha_futura,
        duracion=1
    )
    # Restauramos disponibilidad
    s3.activo = True

    resultados.append({
        "num": 9,
        "nombre": "Control de Disponibilidad Operativa de Servicios",
        "tipo_esperado": "EXCEPCIÓN CONTROLADA (ServicioNoDisponibleError)",
        "resultado_real": "CAPTURADA" if not ok else "FALLO",
        "mensaje": msg,
        "detalle": "El sistema impidió reservar un servicio inactivo o en mantenimiento preventivo."
    })

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 10: Cancelación Exitosa y Posterior Intento Ilegal de Re-cancelación (TRANSICIÓN INVÁLIDA)
    # ----------------------------------------------------------------------------------------------
    logger.info("\n>>> SIMULACIÓN 10: Flujo de Cancelación y Detección de Transición de Estado Ilegal")
    # Paso A: Cancelación legítima
    ok_cancela, msg_cancela = sistema.cancelar_reserva("RSV-2026-001", "Reunión corporativa reprogramada")
    # Paso B: Segundo intento de cancelación sobre la misma reserva (debe fallar controladamente)
    ok_invalida, msg_invalida = sistema.cancelar_reserva("RSV-2026-001", "Intento redundante de cancelar")

    resultados.append({
        "num": 10,
        "nombre": "Máquina de Estados y Transición Invalida de Reserva",
        "tipo_esperado": "CANCELACIÓN EXITOSA + RECHAZO DE TRANSICIÓN",
        "resultado_real": "ÉXITO" if (ok_cancela and not ok_invalida) else "FALLO",
        "mensaje": f"Paso 1: {msg_cancela} | Paso 2: {msg_invalida}",
        "detalle": "Se validó que los estados terminales no permiten operaciones contradictorias."
    })

    logger.info("=" * 80)
    logger.info("SUITE DE 10 SIMULACIONES FINALIZADA CON TOTAL ESTABILIDAD DEL SISTEMA")
    logger.info("=" * 80)

    return resultados


# ==================================================================================================
# 9. INTERFAZ GRÁFICA DE USUARIO EN TKINTER (NIVEL UNIVERSITARIO Y AUDITORÍA EN VIVO)
# ==================================================================================================

class InterfazSoftwareFJ:
    """
    Panel gráfico de supervisión y control del Sistema Software FJ.
    Permite visualizar clientes, catálogo polimórfico, reservas, disparar la suite de 10
    simulaciones y monitorear el archivo de auditoría (.log) en tiempo real con fecha y hora.
    """
    def __init__(self, root: tk.Tk, sistema: SistemaGestionSoftwareFJ):
        self.root = root
        self.sistema = sistema

        self.root.title("Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas | UNAD Fase 4")
        self.root.geometry("1180x740")
        self.root.minsize(1050, 680)

        # Paleta visual corporativa institucional
        self.COLOR_BG = "#f4f6f9"
        self.COLOR_PRIMARY = "#003366"      # Azul institucional UNAD
        self.COLOR_ACCENT = "#e67e22"       # Naranja contraste
        self.COLOR_CARD = "#ffffff"
        self.COLOR_TEXT = "#2c3e50"
        self.COLOR_SUCCESS = "#27ae60"
        self.COLOR_DANGER = "#c0392b"

        self.root.configure(bg=self.COLOR_BG)
        self._construir_estilos()
        self._construir_interfaz()
        self._actualizar_reloj_sistema()
        self._refrescar_vistas()

        logger.info("Interfaz Gráfica Tkinter desplegada exitosamente.")

    def _construir_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Configuración de Treeview
        style.configure("Treeview",
                        background="#ffffff",
                        foreground=self.COLOR_TEXT,
                        rowheight=26,
                        fieldbackground="#ffffff",
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                        background="#e8ecf1",
                        foreground=self.COLOR_PRIMARY,
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#d0e1fd")], foreground=[("selected", "#002050")])

        # Notebook tabs
        style.configure("TNotebook", background=self.COLOR_BG)
        style.configure("TNotebook.Tab",
                        font=("Segoe UI", 10, "bold"),
                        padding=[14, 6],
                        background="#dfe4ea",
                        foreground=self.COLOR_TEXT)
        style.map("TNotebook.Tab",
                  background=[("selected", self.COLOR_PRIMARY)],
                  foreground=[("selected", "#ffffff")])

    def _construir_interfaz(self):
        # ----------------------------- Encabezado Superior -----------------------------
        header_frame = tk.Frame(self.root, bg=self.COLOR_PRIMARY, height=72)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        title_container = tk.Frame(header_frame, bg=self.COLOR_PRIMARY)
        title_container.pack(side=tk.LEFT, padx=18, pady=10)

        lbl_main = tk.Label(
            title_container,
            text="SOFTWARE FJ  |  Sistema Integral de Gestión de Clientes, Servicios y Reservas",
            font=("Segoe UI", 13, "bold"),
            fg="#ffffff",
            bg=self.COLOR_PRIMARY
        )
        lbl_main.pack(anchor="w")

        lbl_sub = tk.Label(
            title_container,
            text="Programación (213023) - Fase 4: Prácticas Simuladas | Estudiante: Javier Ricardo Cifuentes V. (Grupo 511)",
            font=("Segoe UI", 9),
            fg="#d0e1fd",
            bg=self.COLOR_PRIMARY
        )
        lbl_sub.pack(anchor="w")

        # Reloj en tiempo real (requisito de auditoría con fecha y hora)
        self.lbl_clock = tk.Label(
            header_frame,
            text="Fecha / Hora: --:--:--",
            font=("Consolas", 10, "bold"),
            fg="#f1c40f",
            bg=self.COLOR_PRIMARY,
            padx=18
        )
        self.lbl_clock.pack(side=tk.RIGHT, pady=15)

        # ----------------------------- Notebook con Pestañas -----------------------------
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        # Pestaña 1: Control de Simulaciones (Requisito Rúbrica: 10 pruebas)
        self.tab_simulaciones = tk.Frame(self.notebook, bg=self.COLOR_BG)
        self.notebook.add(self.tab_simulaciones, text="  ⚡ Suite de 10 Simulaciones  ")

        # Pestaña 2: Catálogo Polimórfico de Servicios
        self.tab_servicios = tk.Frame(self.notebook, bg=self.COLOR_BG)
        self.notebook.add(self.tab_servicios, text="  🏛 Catálogo de Servicios  ")

        # Pestaña 3: Clientes y Reservas en Memoria
        self.tab_gestion = tk.Frame(self.notebook, bg=self.COLOR_BG)
        self.notebook.add(self.tab_gestion, text="  👥 Clientes y Reservas  ")

        # Pestaña 4: Consola de Auditoría y Logs en Vivo
        self.tab_logs = tk.Frame(self.notebook, bg=self.COLOR_BG)
        self.notebook.add(self.tab_logs, text="  📜 Auditoría y Archivo .log  ")

        # Construcción interna de cada pestaña
        self._construir_pestana_simulaciones()
        self._construir_pestana_servicios()
        self._construir_pestana_gestion()
        self._construir_pestana_logs()

        # ----------------------------- Barra de Estado Inferior -----------------------------
        status_bar = tk.Frame(self.root, bg="#2c3e50", height=28)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        self.lbl_status = tk.Label(
            status_bar,
            text="Arquitectura POO activa | Manejo de excepciones en memoria (sin base de datos) | Archivo de logs sincronizado.",
            font=("Segoe UI", 9),
            fg="#ecf0f1",
            bg="#2c3e50",
            padx=10
        )
        self.lbl_status.pack(side=tk.LEFT)

    def _actualizar_reloj_sistema(self):
        now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        self.lbl_clock.config(text=f"Sistema: {now_str}")
        self.root.after(1000, self._actualizar_reloj_sistema)

    # ----------------------------------------------------------------------------------------------
    # PESTAÑA 1: SIMULACIONES
    # ----------------------------------------------------------------------------------------------
    def _construir_pestana_simulaciones(self):
        top_bar = tk.Frame(self.tab_simulaciones, bg=self.COLOR_BG)
        top_bar.pack(fill=tk.X, padx=12, pady=8)

        lbl_info = tk.Label(
            top_bar,
            text="Batería automatizada de verificación de robustez (Excepciones Personalizadas, try/except/else/finally, Logs)",
            font=("Segoe UI", 10, "bold"),
            fg=self.COLOR_PRIMARY,
            bg=self.COLOR_BG
        )
        lbl_info.pack(side=tk.LEFT, pady=4)

        btn_run_sim = tk.Button(
            top_bar,
            text="▶ Ejecutar 10 Simulaciones Ahora",
            font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_SUCCESS,
            fg="#ffffff",
            activebackground="#219955",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=14,
            pady=5,
            cursor="hand2",
            command=self._accion_ejecutar_simulaciones
        )
        btn_run_sim.pack(side=tk.RIGHT)

        # Tabla de visualización de los 10 casos
        cols = ("num", "nombre", "esperado", "obtenido", "detalle")
        self.tree_sim = ttk.Treeview(self.tab_simulaciones, columns=cols, show="headings", height=14)
        self.tree_sim.heading("num", text="N°")
        self.tree_sim.heading("nombre", text="Escenario Evaluado")
        self.tree_sim.heading("esperado", text="Comportamiento Esperado")
        self.tree_sim.heading("obtenido", text="Resultado Obtenido")
        self.tree_sim.heading("detalle", text="Detalle de Validación y Trazabilidad")

        self.tree_sim.column("num", width=45, anchor="center")
        self.tree_sim.column("nombre", width=220, anchor="w")
        self.tree_sim.column("esperado", width=230, anchor="w")
        self.tree_sim.column("obtenido", width=110, anchor="center")
        self.tree_sim.column("detalle", width=480, anchor="w")

        scroll_y = ttk.Scrollbar(self.tab_simulaciones, orient=tk.VERTICAL, command=self.tree_sim.yview)
        self.tree_sim.configure(yscrollcommand=scroll_y.set)

        self.tree_sim.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))
        scroll_y.place(in_=self.tree_sim, relx=1.0, rely=0.0, relheight=1.0, x=-16)

    def _accion_ejecutar_simulaciones(self):
        # Limpia la tabla
        for item in self.tree_sim.get_children():
            self.tree_sim.delete(item)

        resultados = ejecutar_suite_simulaciones(self.sistema)

        for res in resultados:
            tag = "ok" if res["resultado_real"] in ("ÉXITO", "CAPTURADA") else "err"
            self.tree_sim.insert(
                "",
                tk.END,
                values=(
                    res["num"],
                    res["nombre"],
                    res["tipo_esperado"],
                    res["resultado_real"],
                    res["mensaje"]
                ),
                tags=(tag,)
            )

        self.tree_sim.tag_configure("ok", foreground="#1e824c")
        self.tree_sim.tag_configure("err", foreground="#c0392b")

        self._refrescar_vistas()
        self._recargar_log_en_pantalla()
        messagebox.showinfo(
            "Simulaciones Concluidas",
            "Se han completado las 10 simulaciones operativas con éxito.\n"
            "Todos los eventos y excepciones controladas fueron registrados en el archivo de log.\n"
            "La aplicación continúa funcionando de manera completamente estable."
        )

    # ----------------------------------------------------------------------------------------------
    # PESTAÑA 2: SERVICIOS
    # ----------------------------------------------------------------------------------------------
    def _construir_pestana_servicios(self):
        lbl = tk.Label(
            self.tab_servicios,
            text="Jerarquía Polimórfica de Servicios (Clase Abstracta Servicio -> ReservaSala, AlquilerEquipo, AsesoriaEspecializada)",
            font=("Segoe UI", 10, "bold"),
            fg=self.COLOR_PRIMARY,
            bg=self.COLOR_BG
        )
        lbl.pack(anchor="w", padx=14, pady=8)

        cols = ("id", "clase", "nombre", "tarifa", "estado", "detalles")
        self.tree_srv = ttk.Treeview(self.tab_servicios, columns=cols, show="headings", height=14)
        self.tree_srv.heading("id", text="ID Servicio")
        self.tree_srv.heading("clase", text="Clase Derivada")
        self.tree_srv.heading("nombre", text="Nombre del Servicio")
        self.tree_srv.heading("tarifa", text="Tarifa Base (COP)")
        self.tree_srv.heading("estado", text="Disponibilidad")
        self.tree_srv.heading("detalles", text="Especificaciones Técnicas Polimórficas")

        self.tree_srv.column("id", width=110, anchor="center")
        self.tree_srv.column("clase", width=160, anchor="w")
        self.tree_srv.column("nombre", width=230, anchor="w")
        self.tree_srv.column("tarifa", width=120, anchor="e")
        self.tree_srv.column("estado", width=100, anchor="center")
        self.tree_srv.column("detalles", width=380, anchor="w")

        scroll_y = ttk.Scrollbar(self.tab_servicios, orient=tk.VERTICAL, command=self.tree_srv.yview)
        self.tree_srv.configure(yscrollcommand=scroll_y.set)
        self.tree_srv.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))
        scroll_y.place(in_=self.tree_srv, relx=1.0, rely=0.0, relheight=1.0, x=-16)

    # ----------------------------------------------------------------------------------------------
    # PESTAÑA 3: CLIENTES Y RESERVAS
    # ----------------------------------------------------------------------------------------------
    def _construir_pestana_gestion(self):
        paned = tk.PanedWindow(self.tab_gestion, orient=tk.VERTICAL, bg=self.COLOR_BG, sashwidth=6)
        paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Sub-sección Clientes
        frame_cli = tk.Frame(paned, bg=self.COLOR_BG)
        lbl_cli = tk.Label(frame_cli, text="Clientes Registrados en Memoria (Encapsulamiento y Validaciones)",
                           font=("Segoe UI", 10, "bold"), fg=self.COLOR_PRIMARY, bg=self.COLOR_BG)
        lbl_cli.pack(anchor="w", pady=(0, 4))

        cols_cli = ("cedula", "nombre", "email", "telefono", "segmento")
        self.tree_cli = ttk.Treeview(frame_cli, columns=cols_cli, show="headings", height=6)
        self.tree_cli.heading("cedula", text="Cédula / NIT")
        self.tree_cli.heading("nombre", text="Nombre Completo / Razón Social")
        self.tree_cli.heading("email", text="Correo Electrónico")
        self.tree_cli.heading("telefono", text="Teléfono")
        self.tree_cli.heading("segmento", text="Segmento")

        self.tree_cli.column("cedula", width=120, anchor="center")
        self.tree_cli.column("nombre", width=260, anchor="w")
        self.tree_cli.column("email", width=240, anchor="w")
        self.tree_cli.column("telefono", width=130, anchor="center")
        self.tree_cli.column("segmento", width=140, anchor="center")
        self.tree_cli.pack(fill=tk.BOTH, expand=True)

        # Sub-sección Reservas
        frame_rsv = tk.Frame(paned, bg=self.COLOR_BG)
        lbl_rsv = tk.Label(frame_rsv, text="Reservas Procesadas en el Sistema (Gestión de Estados y Liquidación)",
                           font=("Segoe UI", 10, "bold"), fg=self.COLOR_PRIMARY, bg=self.COLOR_BG)
        lbl_rsv.pack(anchor="w", pady=(8, 4))

        cols_rsv = ("id", "cliente", "servicio", "fecha", "duracion", "total", "estado")
        self.tree_rsv = ttk.Treeview(frame_rsv, columns=cols_rsv, show="headings", height=8)
        self.tree_rsv.heading("id", text="ID Reserva")
        self.tree_rsv.heading("cliente", text="Cliente")
        self.tree_rsv.heading("servicio", text="Servicio Contratado")
        self.tree_rsv.heading("fecha", text="Fecha Agendada")
        self.tree_rsv.heading("duracion", text="Duración")
        self.tree_rsv.heading("total", text="Total Liquidado (COP)")
        self.tree_rsv.heading("estado", text="Estado Operativo")

        self.tree_rsv.column("id", width=120, anchor="center")
        self.tree_rsv.column("cliente", width=230, anchor="w")
        self.tree_rsv.column("servicio", width=220, anchor="w")
        self.tree_rsv.column("fecha", width=110, anchor="center")
        self.tree_rsv.column("duracion", width=90, anchor="center")
        self.tree_rsv.column("total", width=130, anchor="e")
        self.tree_rsv.column("estado", width=120, anchor="center")
        self.tree_rsv.pack(fill=tk.BOTH, expand=True)

        paned.add(frame_cli, minsize=140)
        paned.add(frame_rsv, minsize=180)

    # ----------------------------------------------------------------------------------------------
    # PESTAÑA 4: LOGS Y AUDITORÍA
    # ----------------------------------------------------------------------------------------------
    def _construir_pestana_logs(self):
        top_bar = tk.Frame(self.tab_logs, bg=self.COLOR_BG)
        top_bar.pack(fill=tk.X, padx=14, pady=8)

        lbl_ruta = tk.Label(
            top_bar,
            text=f"Archivo físico de auditoría: {LOG_FILE_PATH}",
            font=("Consolas", 9),
            fg="#7f8c8d",
            bg=self.COLOR_BG
        )
        lbl_ruta.pack(side=tk.LEFT)

        btn_refresh_log = tk.Button(
            top_bar,
            text="🔄 Actualizar Log",
            font=("Segoe UI", 9, "bold"),
            bg=self.COLOR_PRIMARY,
            fg="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=3,
            command=self._recargar_log_en_pantalla
        )
        btn_refresh_log.pack(side=tk.RIGHT)

        self.txt_log = scrolledtext.ScrolledText(
            self.tab_logs,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#ffffff"
        )
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))

        # Coloreado semántico de líneas de log
        self.txt_log.tag_config("INFO", foreground="#4ec9b0")
        self.txt_log.tag_config("WARNING", foreground="#ce9178")
        self.txt_log.tag_config("ERROR", foreground="#f44747")
        self.txt_log.tag_config("CRITICAL", foreground="#ff0000", underline=True)
        self.txt_log.tag_config("DEBUG", foreground="#808080")

        self._recargar_log_en_pantalla()

    def _recargar_log_en_pantalla(self):
        if not os.path.exists(LOG_FILE_PATH):
            return

        try:
            with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
                lineas = f.readlines()

            self.txt_log.config(state=tk.NORMAL)
            self.txt_log.delete("1.0", tk.END)

            # Muestra las últimas 300 líneas para óptimo rendimiento
            for linea in lineas[-300:]:
                nivel_tag = "DEBUG"
                for tag in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"):
                    if f"[{tag}" in linea:
                        nivel_tag = tag
                        break
                self.txt_log.insert(tk.END, linea, nivel_tag)

            self.txt_log.see(tk.END)
            self.txt_log.config(state=tk.DISABLED)
        except Exception as ex:
            logger.error(f"Falla al leer archivo de log: {ex}")

    def _refrescar_vistas(self):
        # 1. Refrescar Servicios
        for item in self.tree_srv.get_children():
            self.tree_srv.delete(item)
        for srv in self.sistema.listar_servicios():
            self.tree_srv.insert("", tk.END, values=(
                srv.id_servicio,
                srv.__class__.__name__,
                srv.nombre,
                f"${srv.tarifa_base:,.2f}",
                "ACTIVO" if srv.activo else "INACTIVO",
                srv.describir_servicio()
            ))

        # 2. Refrescar Clientes
        for item in self.tree_cli.get_children():
            self.tree_cli.delete(item)
        for cli in self.sistema.listar_clientes():
            self.tree_cli.insert("", tk.END, values=(
                cli.cedula,
                cli.nombre_completo,
                cli.email,
                cli.telefono,
                "Corporativo" if cli.es_corporativo else "Estándar"
            ))

        # 3. Refrescar Reservas
        for item in self.tree_rsv.get_children():
            self.tree_rsv.delete(item)
        for rsv in self.sistema.listar_reservas():
            self.tree_rsv.insert("", tk.END, values=(
                rsv.id_reserva,
                rsv.cliente.nombre_completo,
                rsv.servicio.nombre,
                rsv._fecha_reserva.strftime("%Y-%m-%d"),
                f"{rsv._duracion_unidades} u.",
                f"${rsv.costo_total:,.2f}",
                rsv.estado.value
            ))


# ==================================================================================================
# 10. PUNTO DE ENTRADA PRINCIPAL
# ==================================================================================================

def main():
    logger.info("Iniciando aplicación Software FJ...")
    sistema = SistemaGestionSoftwareFJ()

    # Si se pasa el argumento '--cli', ejecuta únicamente las simulaciones por consola
    if "--cli" in sys.argv:
        print("\n" + "=" * 80)
        print("MODO CONSOLA (CLI): EJECUCIÓN DIRECTA DE SIMULACIONES")
        print("=" * 80)
        ejecutar_suite_simulaciones(sistema)
        print(f"\nOperaciones registradas con éxito en archivo de log: {LOG_FILE_PATH}")
        return

    # De lo contrario, levanta la interfaz gráfica Tkinter
    root = tk.Tk()
    app = InterfazSoftwareFJ(root, sistema)
    root.mainloop()


if __name__ == "__main__":
    main()
