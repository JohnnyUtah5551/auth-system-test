-- Заполняем роли
INSERT INTO auth_system_role (name, description) VALUES 
('admin', 'Полный доступ ко всему'),
('manager', 'Управление товарами, но не пользователями'),
('user', 'Обычный пользователь');

-- Заполняем ресурсы
INSERT INTO auth_system_resource (name, description) VALUES 
('products', 'Товары в магазине'),
('users', 'Пользователи системы'),
('orders', 'Заказы');

-- Права для админа
INSERT INTO auth_system_permission 
(role_id, resource_id, can_view, can_view_own, can_create, can_edit, can_edit_own, can_delete, can_delete_own)
VALUES 
(1, 1, true, true, true, true, true, true, true),  -- админ + товары
(1, 2, true, true, true, true, true, true, true),  -- админ + пользователи
(1, 3, true, true, true, true, true, true, true);  -- админ + заказы

-- Права для менеджера
INSERT INTO auth_system_permission 
(role_id, resource_id, can_view, can_view_own, can_create, can_edit, can_edit_own, can_delete, can_delete_own)
VALUES 
(2, 1, true, true, true, true, true, false, true),  -- менеджер + товары (не может удалять чужие)
(2, 2, false, false, false, false, false, false, false),  -- не видит пользователей
(2, 3, true, true, true, true, true, false, true);  -- менеджер + заказы

-- Права для обычного пользователя
INSERT INTO auth_system_permission 
(role_id, resource_id, can_view, can_view_own, can_create, can_edit, can_edit_own, can_delete, can_delete_own)
VALUES 
(3, 1, false, true, false, false, false, false, false),  -- видит только свои товары
(3, 2, false, true, false, false, true, false, false),  -- может редактировать только себя
(3, 3, false, true, true, false, true, false, true);  -- может создавать заказы и удалять свои
