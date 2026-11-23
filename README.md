# Sistema Integral de Gestión de Clientes, Servicios y Reservas — Software FJ

## Descripción general
Aplicación desarrollada en **Python** aplicando **Programación Orientada a Objetos (POO)** y **manejo avanzado de excepciones**, sin utilizar bases de datos. Toda la gestión de clientes, servicios (reservas de salas, alquiler de equipos y asesorías especializadas) y reservas se realiza mediante objetos en memoria, listas internas y registro de eventos/errores en el archivo `software_fj.log`.

## Características principales
- **Abstracción y herencia (`abc.ABC`):** Clase base `EntidadSistema` y clase abstracta `Servicio` con tres clases hijas: `ReservaSala`, `AlquilerEquipo` y `AsesoriaEspecializada`.
- **Encapsulación y validaciones:** Propiedades y validaciones en `Cliente` y en cada servicio antes de procesar reservas.
- **Polimorfismo y sobrecarga:** Métodos sobrescritos (`validar_parametros`, `calcular_costo_base`, `describir`, `resumen`), cálculo de costos con parámetros opcionales de descuento/impuesto y ajuste especial con `@singledispatchmethod`.
- **Manejo de excepciones y `logging`:** Excepciones personalizadas (`DatoInvalidoError`, `ParametroFaltanteError`, `OperacionNoPermitidaError`, `ReservaInvalidaError`, `ServicioNoDisponibleError`, `CalculoInconsistenteError`), bloques `try/except/else/finally`, encadenamiento (`raise ... from ...`) y registro continuo en `software_fj.log`.
- **Simulaciones:** Ejecución de 12 operaciones combinando registros y reservas válidas e inválidas sin detener el flujo del programa.

## Ejecución
python sistema_software_fj.py