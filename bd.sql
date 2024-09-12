-- Active: 1722942989265@@127.0.0.1@3306@pagCobro
-- ---
-- Table 'Usuario'
-- 
-- ---
		
CREATE TABLE `Usuario` (
  `id_usuario` INT NOT NULL AUTO_INCREMENT,
  `user_usuario` VARCHAR(100) NOT NULL UNIQUE,
  `nombre_apellido` VARCHAR(250) NOT NULL,
  `email` VARCHAR(150) NOT NULL,
  `codigo_postal` INT DEFAULT NULL,
  `contraseña_usuario` VARCHAR(60) NOT NULL,
  `telefono` INT DEFAULT NULL,
  PRIMARY KEY (`id_usuario`)
);

-- Crear tabla Roles
CREATE TABLE Roles (
    id_rol INT PRIMARY KEY AUTO_INCREMENT,
    tipo_rol VARCHAR(50) NOT NULL,
    id_usuario INT
);

-- Crear tabla Carrito
CREATE TABLE Carrito (
    id_carrito INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT,
    status_carrito VARCHAR(50),
    metodo_pago VARCHAR(50),
    fecha_pago DATE
);

CREATE TABLE Carrito_Productos (
    id_carrito_producto INT PRIMARY KEY AUTO_INCREMENT,
    id_carrito INT,
    id_producto INT,
    cantidad INT,
    FOREIGN KEY (id_carrito) REFERENCES Carrito(id_carrito),
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto)
);

-- Crear tabla Producto
CREATE TABLE Producto (
    id_producto INT PRIMARY KEY AUTO_INCREMENT,
    precio DECIMAL(10, 2) NOT NULL,
    descripcion TEXT,
    cantidad_producto INT NOT NULL,
    id_carrito INT
    nombre_producto VARCHAR(255) NOT NULL,
    imagen_producto VARCHAR(1500)
);

-- Agregar clave foránea a la tabla Roles
ALTER TABLE Roles
ADD CONSTRAINT fk_roles_usuario
FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario);

-- Agregar clave foránea a la tabla Carrito
ALTER TABLE Carrito
ADD CONSTRAINT fk_carrito_usuario
FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario);

-- Agregar clave foránea a la tabla Producto
ALTER TABLE Producto
ADD CONSTRAINT fk_producto_carrito
FOREIGN KEY (id_carrito) REFERENCES Carrito(id_carrito);

INSERT INTO Producto (precio, descripcion, cantidad_producto, id_carrito, nombre_producto, imagen_producto) VALUES
(19.99, 'Camiseta básica de algodón', 100, NULL, 'Camiseta Blanca', 'https://acdn.mitiendanube.com/stores/002/273/996/products/boneco-verano-2023-321-c2b221bf98812ae84b16954034290479-1024-1024.png'), 
(29.99, 'Pantalón de mezclilla', 50, NULL, 'Pantalón Jeans', 'https://m.media-amazon.com/images/I/71mwrMva5lL._AC_UY1000_.jpg'),
(15.50, 'Gorra con logo bordado', 75, NULL, 'Gorra', 'https://i.pinimg.com/originals/0b/e9/87/0be9871bf8fa1210997305cb5cabe8ca.png'),
(9.99, 'Par de calcetines de lana', 150, NULL, 'Calcetines', 'https://ih1.redbubble.net/image.2954810594.4653/ur,socks_flatlay_medium,square,600x600-bg,f8f8f8.1.jpg'),
(49.99, 'Suéter de lana', 20, NULL, 'Suéter', 'https://i.pinimg.com/originals/60/59/79/605979a6ed2c1771fa7176b154c10251.png'),
(12.50, 'Bufanda de invierno', 90, NULL, 'Bufanda', 'https://www.regalosfrikis.com/wp-content/uploads/2014/12/regalos-frikis-bufanda-creeper.png')