# Polarpor DB

Приложение для управления данными (номера дел, проформы, грузы, поставщики) с использованием Firebase.

## Установка и запуск

### 1. Клонирование репозитория
```bash
git clone https://github.com/Sne51/Polarpor_DB_win.git
cd Polarpor_DB_win
```

### 2. Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Подготовка конфигурации
Создайте файл `config/firebase_credentials.json` и добавьте туда ключи Firebase, полученные в консоли Firebase.

### 5. Запуск приложения
```bash
python main.py
```

---

## Примечания
- Все локальные ключи и конфиги находятся в `.gitignore` и не попадают в репозиторий.
- Для корректной работы необходим доступ к интернету.