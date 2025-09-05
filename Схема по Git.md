graph TD
A[Репозиторий PIK на GitHub] --> B[Клонирование через GitHub Desktop]
B --> C[Открыть папку как vault в Obsidian]
C --> D[Создать .gitignore и commit]
D --> E{Синхронизация}
E -->|Вариант А| F[GitHub Desktop Commit/Push вручную]
E -->|Вариант Б| G[Obsidian Git авто Pull/Commit/Push]