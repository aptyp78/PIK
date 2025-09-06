#!/usr/bin/env python3
"""
PIK Framework Management System
===============================

Главный интерфейс для управления всей экосистемой PIK.
Объединяет все компоненты: парсинг, качество, визуализация.
"""

import sys
import os
from pathlib import Path

# Добавляем пути к модулям
sys.path.append(str(Path(__file__).parent / "core"))
sys.path.append(str(Path(__file__).parent / "servers"))
sys.path.append(str(Path(__file__).parent / "tools"))

class PIKManager:
    """Главный менеджер PIK системы"""
    
    def __init__(self):
        self.version = "2.0.0"
        self.components = {
            "parser": "core/intelligent_pik_parser.py",
            "batch": "core/batch_pik_analysis.py", 
            "quality": "core/drawio_quality_tester.py",
            "viz_server": "servers/pik_visualization_server.py",
            "quality_server": "servers/quality_test_server.py",
            "ocr_server": "servers/ocr_server.py"
        }
    
    def show_status(self):
        """Показать статус всех компонентов"""
        print(f"""
🚀 PIK Framework Management System v{self.version}
===================================================

📊 СТАТУС КОМПОНЕНТОВ:
""")
        
        for name, path in self.components.items():
            full_path = Path(__file__).parent / path
            status = "✅" if full_path.exists() else "❌"
            size = full_path.stat().st_size if full_path.exists() else 0
            print(f"{status} {name:15} | {path:35} | {size:>8} bytes")
    
    def run_component(self, component_name: str):
        """Запустить конкретный компонент"""
        if component_name not in self.components:
            print(f"❌ Компонент '{component_name}' не найден")
            self.show_available_components()
            return
        
        path = self.components[component_name]
        full_path = Path(__file__).parent / path
        
        if not full_path.exists():
            print(f"❌ Файл {path} не найден")
            return
        
        print(f"🚀 Запуск {component_name}...")
        print(f"📁 Путь: {path}")
        
        # Импортируем и запускаем
        try:
            if component_name == "parser":
                from intelligent_pik_parser import main
                main()
            elif component_name == "batch":
                from batch_pik_analysis import main
                main()
            elif component_name == "quality":
                from drawio_quality_tester import main
                main()
            elif component_name == "viz_server":
                print("💡 Для запуска сервера используйте: python servers/pik_visualization_server.py")
            elif component_name == "quality_server":
                print("💡 Для запуска сервера используйте: python servers/quality_test_server.py")
            elif component_name == "ocr_server":
                print("💡 Для запуска сервера используйте: python servers/ocr_server.py")
                
        except ImportError as e:
            print(f"❌ Ошибка импорта: {e}")
        except Exception as e:
            print(f"❌ Ошибка выполнения: {e}")
    
    def show_available_components(self):
        """Показать доступные компоненты"""
        print("\n🔧 ДОСТУПНЫЕ КОМПОНЕНТЫ:")
        for name, path in self.components.items():
            print(f"   {name:15} - {path}")
    
    def interactive_menu(self):
        """Интерактивное меню"""
        while True:
            print(f"""
🎯 PIK Framework v{self.version} - Главное меню
===============================================

1. 📊 Показать статус компонентов
2. 🧠 Запустить Intelligent Parser
3. 📦 Запустить Batch Analysis  
4. 🔍 Запустить Quality Testing
5. 🌐 Информация о серверах
6. 🛠️ Запустить инструменты
7. 📚 Показать документацию
8. ❌ Выход

Выберите опцию (1-8): """, end="")
            
            choice = input().strip()
            
            if choice == "1":
                self.show_status()
            elif choice == "2":
                self.run_component("parser")
            elif choice == "3":
                self.run_component("batch")
            elif choice == "4":
                self.run_component("quality")
            elif choice == "5":
                self.show_servers_info()
            elif choice == "6":
                self.show_tools_menu()
            elif choice == "7":
                self.show_documentation()
            elif choice == "8":
                print("👋 До свидания!")
                break
            else:
                print("❌ Неверный выбор")
    
    def show_servers_info(self):
        """Информация о серверах"""
        print("""
🌐 ИНФОРМАЦИЯ О СЕРВЕРАХ:
========================

📊 Visualization Server (порт 8001):
   python servers/pik_visualization_server.py

🔍 Quality Test Server (порт 8002):  
   python servers/quality_test_server.py

👁️ OCR Server (порт 8000):
   python servers/ocr_server.py

💡 Все серверы поддерживают REST API
""")
    
    def show_tools_menu(self):
        """Меню инструментов"""
        tools_dir = Path(__file__).parent / "tools"
        tools = list(tools_dir.glob("*.py"))
        
        print("""
🛠️ ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
=========================""")
        
        for i, tool in enumerate(tools, 1):
            print(f"{i:2}. {tool.name}")
        
        print(f"\nВсего инструментов: {len(tools)}")
    
    def show_documentation(self):
        """Показать документацию"""
        docs_dir = Path(__file__).parent / "docs"
        docs = list(docs_dir.glob("*.md"))
        
        print("""
📚 ДОКУМЕНТАЦИЯ:
================""")
        
        for doc in docs:
            size = doc.stat().st_size
            print(f"📄 {doc.name:<40} ({size:>8} bytes)")

def main():
    """Главная функция"""
    manager = PIKManager()
    
    if len(sys.argv) > 1:
        # Запуск конкретного компонента из командной строки
        component = sys.argv[1]
        manager.run_component(component)
    else:
        # Интерактивное меню
        manager.interactive_menu()

if __name__ == "__main__":
    main()
