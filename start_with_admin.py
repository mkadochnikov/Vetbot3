#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Лаунчер для запуска бота и админ-панели одновременно
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

class VetBotLauncher:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def start_bot(self):
        """Запуск Telegram бота"""
        print("🤖 Запуск Telegram бота...")
        try:
            process = subprocess.Popen([
                sys.executable, 'enhanced_bot.py'
            ], cwd=Path(__file__).parent)
            self.processes.append(('bot', process))
            print("✅ Telegram бот запущен")
            return process
        except Exception as e:
            print(f"❌ Ошибка запуска бота: {e}")
            return None
    
    def start_webapp(self):
        """Запуск веб-приложения"""
        print("🌐 Запуск веб-приложения...")
        try:
            process = subprocess.Popen([
                sys.executable, 'webapp_server.py'
            ], cwd=Path(__file__).parent)
            self.processes.append(('webapp', process))
            print("✅ Веб-приложение запущено на порту 5000")
            return process
        except Exception as e:
            print(f"❌ Ошибка запуска веб-приложения: {e}")
            return None
    
    def start_admin_panel(self):
        """Запуск админ-панели на Streamlit"""
        print("👨‍💼 Запуск админ-панели на Streamlit...")
        try:
            process = subprocess.Popen([
                sys.executable, '-m', 'streamlit', 'run', 'admin_streamlit.py',
                '--server.port=8501',
                '--server.address=0.0.0.0',
                '--browser.gatherUsageStats=false'
            ], cwd=Path(__file__).parent)
            self.processes.append(('admin', process))
            print("✅ Админ-панель запущена на порту 8501")
            return process
        except Exception as e:
            print(f"❌ Ошибка запуска админ-панели: {e}")
            return None
    
    def monitor_processes(self):
        """Мониторинг процессов и автоперезапуск"""
        while self.running:
            time.sleep(5)
            
            for i, (name, process) in enumerate(self.processes):
                if process.poll() is not None:  # Процесс завершился
                    print(f"⚠️ Процесс {name} завершился, перезапускаем...")
                    
                    if name == 'bot':
                        new_process = self.start_bot()
                    elif name == 'webapp':
                        new_process = self.start_webapp()
                    elif name == 'admin':
                        new_process = self.start_admin_panel()
                    
                    if new_process:
                        self.processes[i] = (name, new_process)
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        print("\n🛑 Получен сигнал завершения, останавливаем все процессы...")
        self.running = False
        
        for name, process in self.processes:
            print(f"🔄 Останавливаем {name}...")
            try:
                process.terminate()
                process.wait(timeout=10)
                print(f"✅ {name} остановлен")
            except subprocess.TimeoutExpired:
                print(f"⚠️ Принудительно завершаем {name}...")
                process.kill()
            except Exception as e:
                print(f"❌ Ошибка при остановке {name}: {e}")
        
        print("👋 Все процессы остановлены")
        sys.exit(0)
    
    def run(self):
        """Основной метод запуска"""
        # Регистрируем обработчики сигналов
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("""
🚀 Ветеринарная служба - Полный запуск
=====================================
        """)
        
        # Запускаем все компоненты
        bot_process = self.start_bot()
        webapp_process = self.start_webapp()
        admin_process = self.start_admin_panel()
        
        if not any([bot_process, webapp_process, admin_process]):
            print("❌ Не удалось запустить ни одного компонента")
            return
        
        print("""
✅ Система запущена!

📱 Telegram бот: Активен
🌐 Веб-приложение: http://localhost:5000
👨‍💼 Админ-панель: http://localhost:8501

Для остановки нажмите Ctrl+C
        """)
        
        # Запускаем мониторинг в отдельном потоке
        monitor_thread = threading.Thread(target=self.monitor_processes)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Ожидаем завершения
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)

if __name__ == '__main__':
    launcher = VetBotLauncher()
    launcher.run()

