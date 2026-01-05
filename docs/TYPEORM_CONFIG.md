# Настройка TypeORM

## Конфигурация

TypeORM настроен для работы с PostgreSQL с следующими параметрами:

### Основные настройки

- **Тип БД**: PostgreSQL
- **Пул соединений**: 5-20 соединений
- **Автозагрузка entities**: Включена (`autoLoadEntities: true`)
- **Синхронизация схемы**: Отключена (`synchronize: false`) - используем миграции
- **Логирование**: Включено только в тестовом режиме

### Пул соединений

```typescript
extra: {
  max: 20,              // Максимальное количество соединений
  min: 5,               // Минимальное количество соединений
  idleTimeoutMillis: 30000,      // Таймаут простоя (30 сек)
  connectionTimeoutMillis: 2000,  // Таймаут установки (2 сек)
}
```

### Переподключение

- **Попытки**: 3
- **Задержка**: 3000 мс (3 секунды)

## Миграции

### Создание миграции

```bash
# Создать новую пустую миграцию
npm run migration:create src/migrations/MigrationName

# Сгенерировать миграцию на основе изменений entities (автоматически)
# ВАЖНО: Убедитесь, что entities синхронизированы с текущей БД перед генерацией
npm run migration:generate src/migrations/MigrationName
```

**Примечание**: Для генерации миграций TypeORM сравнивает текущие entities с текущей схемой БД. Убедитесь, что БД актуальна перед генерацией.

### Применение миграций

```bash
# Применить все миграции
npm run migration:run

# Откатить последнюю миграцию
npm run migration:revert

# Показать статус миграций
npm run migration:show
```

## Использование в коде

### В сервисах

```typescript
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from '../entities/user.entity';

@Injectable()
export class UsersService {
  constructor(
    @InjectRepository(User)
    private userRepository: Repository<User>,
  ) {}

  async findAll(): Promise<User[]> {
    return await this.userRepository.find();
  }

  async findOne(id: string): Promise<User> {
    return await this.userRepository.findOne({ where: { user_id: id } });
  }

  async create(userData: Partial<User>): Promise<User> {
    const user = this.userRepository.create(userData);
    return await this.userRepository.save(user);
  }
}
```

### В модулях

```typescript
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { User } from '../entities/user.entity';
import { UsersService } from './users.service';

@Module({
  imports: [TypeOrmModule.forFeature([User])],
  providers: [UsersService],
})
export class UsersModule {}
```

## Переменные окружения

Убедитесь, что в `.env` файле указаны:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_user
DB_PASS=your_password
DB_NAME=your_database
MODE=test  # или prod
```

## Важные замечания

1. **НЕ включайте `synchronize: true`** в продакшене - это может привести к потере данных
2. Используйте миграции для изменения схемы БД
3. Настройте пул соединений в зависимости от нагрузки
4. Включите SSL для продакшена, если требуется

