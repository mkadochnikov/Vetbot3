#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для одновременного запуска Telegram бота и веб-приложения
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
        self.bot_process = None
        self.webapp_process = None
        self.running = True
        
    def start_webapp(self):
        """Запуск веб-приложения"""
        print("🌐 Запуск веб-приложения...")
        try:
            self.webapp_process = subprocess.Popen([
                sys.executable, 'webapp_server.py'
            ], cwd=os.path.dirname(__file__))
            print("✅ Веб-приложение запущено (PID: {})".format(self.webapp_process.pid))
        except Exception as e:
            print(f"❌ Ошибка запуска веб-приложения: {e}")
    
    def start_bot(self):
        """Запуск Telegram бота"""
        print("🤖 Запуск Telegram бота...")
        try:
            self.bot_process = subprocess.Popen([
                sys.executable, 'enhanced_bot.py'
            ], cwd=os.path.dirname(__file__))
            print("✅ Telegram бот запущен (PID: {})".format(self.bot_process.pid))
        except Exception as e:
            print(f"❌ Ошибка запуска бота: {e}")
    
    def stop_all(self):
        """Остановка всех сервисов"""
        print("\n🛑 Остановка сервисов...")
        self.running = False
        
        if self.webapp_process:
            try:
                self.webapp_process.terminate()
                self.webapp_process.wait(timeout=5)
                print("✅ Веб-приложение остановлено")
            except subprocess.TimeoutExpired:
                self.webapp_process.kill()
                print("⚠️ Веб-приложение принудительно завершено")
            except Exception as e:
                print(f"❌ Ошибка остановки веб-приложения: {e}")
        
        if self.bot_process:
            try:
                self.bot_process.terminate()
                self.bot_process.wait(timeout=5)
                print("✅ Telegram бот остановлен")
            except subprocess.TimeoutExpired:
                self.bot_process.kill()
                print("⚠️ Telegram бот принудительно завершен")
            except Exception as e:
                print(f"❌ Ошибка остановки бота: {e}")
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        print(f"\n📡 Получен сигнал {signum}")
        self.stop_all()
        sys.exit(0)
    
    def monitor_processes(self):
        """Мониторинг процессов и перезапуск при необходимости"""
        while self.running:
            time.sleep(5)
            
            # Проверка веб-приложения
            if self.webapp_process and self.webapp_process.poll() is not None:
                print("⚠️ Веб-приложение завершилось, перезапуск...")
                self.start_webapp()
            
            # Проверка бота
            if self.bot_process and self.bot_process.poll() is not None:
                print("⚠️ Telegram бот завершился, перезапуск...")
                self.start_bot()
    
    def run(self):
        """Основной метод запуска"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║              ВЕТЕРИНАРНЫЙ СЕРВИС - ПОЛНЫЙ ЗАПУСК            ║
╠══════════════════════════════════════════════════════════════╣
║ 🤖 Telegram бот с AI-консультациями                        ║
║ 🌐 Веб-приложение для вызова врача                         ║
║ 📊 Версия: 2.1.0                                           ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Регистрация обработчиков сигналов
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Запуск сервисов
            self.start_webapp()
            time.sleep(2)  # Небольшая задержка между запусками
            self.start_bot()
            
            print("\n🎉 Все сервисы запущены!")
            print("📱 Веб-приложение: http://localhost:5000")
            print("🤖 Telegram бот: активен")
            print("\n💡 Для остановки нажмите Ctrl+C")
            
            # Запуск мониторинга в отдельном потоке
            monitor_thread = threading.Thread(target=self.monitor_processes)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            # Ожидание завершения процессов
            while self.running:
                try:
                    if self.bot_process:
                        self.bot_process.wait()
                    if self.webapp_process:
                        self.webapp_process.wait()
                    break
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"❌ Ошибка в основном цикле: {e}")
                    time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n⌨️ Получен сигнал прерывания")
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
        finally:
            self.stop_all()
            print("👋 Все сервисы остановлены. До свидания!")

if __name__ == '__main__':
    # Проверка наличия необходимых файлов
    required_files = ['enhanced_bot.py', 'webapp_server.py', '.env']
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Отсутствуют необходимые файлы: {', '.join(missing_files)}")
        sys.exit(1)
    
    # Запуск лаунчера
    launcher = VetBotLauncher()
    launcher.run()

