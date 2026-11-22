# Sistema Integral de Gestión de Clientes, Servicios y Reservas (Software FJ)
## Curso de Programación (Código 213023) - Fase 4: Prácticas Simuladas
### Universidad Nacional Abierta y a Distancia (UNAD) - ECBTI

**Estudiante:** Javier Ricardo Cifuentes Valencia  
**Cédula:** 79065563  
**Grupo:** 213023_511  
**Tutor:** Jorge Eduardo Ospina  

---

## Descripción del Proyecto
El proyecto implementa un sistema empresarial orientado a objetos para la compañía **Software FJ**, especializada en la oferta de servicios tecnológicos:
1. **Reserva de Salas Ejecutivas y de Juntas:** Tarificación horaria, recargo en fines de semana y control de aforo.
2. **Alquiler de Equipos Tecnológicos:** Arrendamiento diario de workstations/laptops, pólizas de seguro todo riesgo y administración física de stock en memoria.
3. **Asesorías Especializadas:** Consultoría técnica clasificada por jerarquía técnica (Junior, Semi-Senior, Senior, Principal Architect) con opción de viáticos presenciales e informes de peritaje de auditoría.

El sistema fue diseñado bajo la restricción estricta de **no utilizar bases de datos**, delegando la consistencia transaccional en listas y diccionarios en memoria y concentrando el almacenamiento secundario en un subsistema de auditoría persistente mediante archivos `.log`.

---

## Arquitectura y Principios de POO Implementados
* **Abstracción:** Clase base pura `EntidadBase` y clase base `Servicio` (derivadas de `abc.ABC`).
* **Encapsulación:** Atributos privados en `Cliente` con getters/setters (`@property`) y validación rigurosa de formato (RFC 5322 para correos electrónicos y rangos numéricos para teléfonos).
* **Herencia y Polimorfismo:** `ReservaSala`, `AlquilerEquipo` y `AsesoriaEspecializada` heredan de `Servicio` implementando métodos sobrescritos (`calcular_costo()`, `describir_servicio()`).
* **Sobrecarga de Métodos:** Mecanismo de tarificación flexible mediante argumentos clave opcionales (`**kwargs`) que admiten cupones, recargos operativos, pólizas de seguro e impuestos.

---

## Manejo Avanzado de Excepciones y Resiliencia
En estricto cumplimiento del **Primer Criterio de la Rúbrica (50 puntos)**:
1. **Jerarquía de Excepciones Personalizadas:**
   * `SoftwareFJError` (Excepción raíz)
   * `ClienteInvalidoError` (`ERR-CLI-001`)
   * `ServicioInvalidoError` (`ERR-SRV-002`)
   * `ServicioNoDisponibleError` (`ERR-SRV-003`)
   * `ReservaInvalidaError` (`ERR-RSV-004`)
   * `CapacidadExcedidaError` (`ERR-RSV-005`)
   * `TransicionEstadoInvalidaError` (`ERR-STA-006`)
   * `CalculoTarifaError` (`ERR-CAL-007`)
2. **Estructuras Completas `try / except / else / finally`:**
   * `else`: Confirmación del registro y actualización de contadores solo en ausencia de fallos.
   * `finally`: Cierre de ciclo transaccional y registro incondicional de auditoría.
3. **Encadenamiento de Excepciones:** Sintaxis `raise ... from exc` para enriquecer excepciones de bajo nivel sin perder la causa raíz.
4. **Subsistema de Logging Profesional:** Registro sincronizado en consola y en el archivo rotativo `software_fj_auditoria.log`.

---

## Suite de 10 Simulaciones Operativas (Criterio 2 - 35 puntos)
El sistema incluye un módulo automatizado que prueba 10 escenarios secuenciales:
1. **Simulación 1:** Registro exitoso de persona natural (Válido).
2. **Simulación 2:** Captura controlada de `ClienteInvalidoError` por correo electrónico mal formado (Inválido).
3. **Simulación 3:** Registro exitoso de cliente corporativo VIP (Válido).
4. **Simulación 4:** Carga e instanciación polimórfica de 3 familias de servicios (Válido).
5. **Simulación 5:** Captura controlada de `ServicioInvalidoError` ante tarifa base negativa (Inválido).
6. **Simulación 6:** Reserva de sala de juntas con descuento corporativo automático (Válido).
7. **Simulación 7:** Captura controlada de `CapacidadExcedidaError` al solicitar 40 asistentes en sala de 18 (Inválido).
8. **Simulación 8:** Alquiler de equipos por 10 días, descuento extendido, seguro y descuento de inventario (Válido).
9. **Simulación 9:** Captura controlada de `ServicioNoDisponibleError` en servicio puesto en mantenimiento (Inválido).
10. **Simulación 10:** Cancelación legítima y captura controlada de `TransicionEstadoInvalidaError` ante intento de doble cancelación (Mixto).

---

## Instrucciones de Ejecución

### Prerrequisitos
* Python 3.10 o superior instalado.
* Biblioteca gráfica estándar `tkinter` habilitada.

### Modo Interfaz Gráfica (GUI)
Para abrir el panel visual con supervisión de entidades, reloj en tiempo real y consola de logs:
```bash
python Fase_4_511.py
```

### Modo Consola / Verificación Rápida (CLI)
Para correr directamente las 10 simulaciones en terminal sin abrir la ventana gráfica:
```bash
python Fase_4_511.py --cli
```

### Auditoría de Logs
El archivo generado puede inspeccionarse en cualquier editor de texto o terminal:
```bash
# En Windows PowerShell
Get-Content -Path "software_fj_auditoria.log" -Tail 50
```

---

## Colaboración y Buenas Prácticas en Git / GitHub (Criterio 4 - 30 puntos)
* **Ramas de Trabajo:** Modelo de ramas por funcionalidad (`feature/excepciones`, `feature/simulaciones`, `feature/gui-tkinter`).
* **Commits Semánticos:** Estructura `feat:`, `fix:`, `docs:`, `refactor:`, `test:`.
* **Pull Requests:** Revisiones cruzadas documentadas para integración en la rama `main`.
