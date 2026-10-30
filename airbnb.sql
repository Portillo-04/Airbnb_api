-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 29-10-2026 a las 03:00:49
-- Versión del servidor: 10.11.16-MariaDB
-- Versión de PHP: 8.5.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `airbnb`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `contratos`
--

CREATE TABLE `contratos` (
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date NOT NULL,
  `precio_mensual` float NOT NULL,
  `estado` enum('ACTIVO','FINALIZADO','CANCELADO') NOT NULL,
  `propiedad_id` int(11) NOT NULL,
  `inquilino_id` int(11) NOT NULL,
  `id` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pagos`
--

CREATE TABLE `pagos` (
  `monto` float NOT NULL,
  `fecha_pago` datetime NOT NULL,
  `metodo_pago` varchar(50) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `contrato_id` int(11) DEFAULT NULL,
  `id` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `propiedades`
--

CREATE TABLE `propiedades` (
  `direccion` varchar(255) NOT NULL,
  `descripcion` varchar(1000) NOT NULL,
  `precio_mensual` float NOT NULL,
  `estado` enum('DISPONIBLE','ALQUILADA','MANTENIMIENTO') NOT NULL,
  `fotos_url` varchar(500) DEFAULT NULL,
  `propietario_id` int(11) NOT NULL,
  `id` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `solicitudalquiler`
--

CREATE TABLE `solicitudalquiler` (
  `propiedad_id` int(11) NOT NULL,
  `inquilino_id` int(11) NOT NULL,
  `fecha_inicio` datetime NOT NULL,
  `fecha_fin` datetime NOT NULL,
  `estado` enum('PENDIENTE','APROBADA','RECHAZADA','POSPUESTA') NOT NULL,
  `respuesta_propietario` varchar(500) DEFAULT NULL,
  `id` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `solicitudes_mantenimiento`
--

CREATE TABLE `solicitudes_mantenimiento` (
  `titulo` varchar(200) NOT NULL,
  `descripcion` varchar(1000) NOT NULL,
  `estado` enum('PENDIENTE','EN_PROCESO','RESUELTO','CANCELADO') NOT NULL,
  `propiedad_id` int(11) NOT NULL,
  `inquilino_id` int(11) NOT NULL,
  `id` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `solicitudvisita`
--

CREATE TABLE `solicitudvisita` (
  `propiedad_id` int(11) NOT NULL,
  `visitante_id` int(11) NOT NULL,
  `fecha_solicitada` datetime NOT NULL,
  `mensaje` varchar(500) DEFAULT NULL,
  `estado` enum('PENDIENTE','APROBADA','RECHAZADA','COMPLETADA') NOT NULL,
  `respuesta_propietario` varchar(500) DEFAULT NULL,
  `id` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `nombre` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `telefono` varchar(9) DEFAULT NULL,
  `rol` enum('propietario','inquilino','administrador') NOT NULL DEFAULT 'inquilino',
  `id` int(11) NOT NULL,
  `password` varchar(255) NOT NULL,
  `activo` tinyint(1) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`nombre`, `email`, `telefono`, `rol`, `id`, `password`, `activo`, `created_at`) VALUES
('admin', 'admin@gmail.com', '7372-2686', 'administrador', 1, '$argon2id$v=19$m=65536,t=3,p=4$vvuA6HmLWgS/K87vuL5+tQ$et9YE3Smf2woYKDcJXP9H6YrIV6RZ+84KH40IKCBvRU', 1, '2026-10-28 19:13:12'),
('cesia', 'cesia@gmail.com', '7829-6962', 'inquilino', 2, '$argon2id$v=19$m=65536,t=3,p=4$pVVqx1vhAWmDIVvKvmtGng$GHdcDXdhapINf9q0fQMZ303jD4uyFPzVoTPE8iMCDzU', 1, '2026-10-28 19:43:35'),
('diego', 'diego@gmail.com', '6003-2409', 'propietario', 3, '$argon2id$v=19$m=65536,t=3,p=4$qsCrxX+BDywIwuX9YgNUMw$O6vDrdgjlvO8/YexeswCrGDqR0MjdVZs/1FmN/kzfgI', 1, '2026-10-28 19:45:20');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `contratos`
--
ALTER TABLE `contratos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `propiedad_id` (`propiedad_id`),
  ADD KEY `inquilino_id` (`inquilino_id`);

--
-- Indices de la tabla `pagos`
--
ALTER TABLE `pagos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `usuario_id` (`usuario_id`),
  ADD KEY `contrato_id` (`contrato_id`);

--
-- Indices de la tabla `propiedades`
--
ALTER TABLE `propiedades`
  ADD PRIMARY KEY (`id`),
  ADD KEY `propietario_id` (`propietario_id`);

--
-- Indices de la tabla `solicitudalquiler`
--
ALTER TABLE `solicitudalquiler`
  ADD PRIMARY KEY (`id`),
  ADD KEY `propiedad_id` (`propiedad_id`),
  ADD KEY `inquilino_id` (`inquilino_id`);

--
-- Indices de la tabla `solicitudes_mantenimiento`
--
ALTER TABLE `solicitudes_mantenimiento`
  ADD PRIMARY KEY (`id`),
  ADD KEY `propiedad_id` (`propiedad_id`),
  ADD KEY `inquilino_id` (`inquilino_id`);

--
-- Indices de la tabla `solicitudvisita`
--
ALTER TABLE `solicitudvisita`
  ADD PRIMARY KEY (`id`),
  ADD KEY `propiedad_id` (`propiedad_id`),
  ADD KEY `visitante_id` (`visitante_id`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `contratos`
--
ALTER TABLE `contratos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `pagos`
--
ALTER TABLE `pagos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `propiedades`
--
ALTER TABLE `propiedades`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `solicitudalquiler`
--
ALTER TABLE `solicitudalquiler`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `solicitudes_mantenimiento`
--
ALTER TABLE `solicitudes_mantenimiento`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `solicitudvisita`
--
ALTER TABLE `solicitudvisita`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `contratos`
--
ALTER TABLE `contratos`
  ADD CONSTRAINT `contratos_ibfk_1` FOREIGN KEY (`propiedad_id`) REFERENCES `propiedades` (`id`),
  ADD CONSTRAINT `contratos_ibfk_2` FOREIGN KEY (`inquilino_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `pagos`
--
ALTER TABLE `pagos`
  ADD CONSTRAINT `pagos_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`),
  ADD CONSTRAINT `pagos_ibfk_2` FOREIGN KEY (`contrato_id`) REFERENCES `contratos` (`id`);

--
-- Filtros para la tabla `propiedades`
--
ALTER TABLE `propiedades`
  ADD CONSTRAINT `propiedades_ibfk_1` FOREIGN KEY (`propietario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `solicitudalquiler`
--
ALTER TABLE `solicitudalquiler`
  ADD CONSTRAINT `solicitudalquiler_ibfk_1` FOREIGN KEY (`propiedad_id`) REFERENCES `propiedades` (`id`),
  ADD CONSTRAINT `solicitudalquiler_ibfk_2` FOREIGN KEY (`inquilino_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `solicitudes_mantenimiento`
--
ALTER TABLE `solicitudes_mantenimiento`
  ADD CONSTRAINT `solicitudes_mantenimiento_ibfk_1` FOREIGN KEY (`propiedad_id`) REFERENCES `propiedades` (`id`),
  ADD CONSTRAINT `solicitudes_mantenimiento_ibfk_2` FOREIGN KEY (`inquilino_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `solicitudvisita`
--
ALTER TABLE `solicitudvisita`
  ADD CONSTRAINT `solicitudvisita_ibfk_1` FOREIGN KEY (`propiedad_id`) REFERENCES `propiedades` (`id`),
  ADD CONSTRAINT `solicitudvisita_ibfk_2` FOREIGN KEY (`visitante_id`) REFERENCES `usuarios` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
