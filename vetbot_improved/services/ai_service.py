"""
Сервис для работы с AI (DeepSeek API)
"""

import logging
import asyncio
import requests
from typing import Dict, Any, Optional

from vetbot_improved.config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, VERSION

logger = logging.getLogger(__name__)

class AIService:
    """Сервис для работы с DeepSeek API"""
    
    @staticmethod
    async def get_consultation(user_message: str, user_name: str) -> str:
        """
        Получение AI-консультации от DeepSeek
        
        Args:
            user_message: Сообщение пользователя
            user_name: Имя пользователя
            
        Returns:
            str: Ответ AI
        """
        try:
            system_prompt = """Ты опытный ветеринар-фелинолог с 15+ летним стажем, специализирующийся исключительно на лечении кошек.

Важные правила ответа:
- НЕ используй символы ### в ответах
- НЕ используй форматирование **текст**
- Используй простой текст с эмодзи
- Структурируй ответ с помощью номеров и эмодзи

Дай профессиональную консультацию по здоровью кошки, включая:
1. Анализ симптомов
2. Возможные причины
3. Рекомендации по первой помощи
4. Когда обязательно нужен осмотр врача

Помни: ты консультируешь только по кошкам!"""
            
            headers = {
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Пользователь {user_name} спрашивает: {user_message}"}
                ],
                "max_tokens": 1500,
                "temperature": 0.7
            }
            
            # Асинхронный запрос с таймаутом
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    requests.post, 
                    DEEPSEEK_API_URL, 
                    headers=headers, 
                    json=data, 
                    timeout=30
                ),
                timeout=35.0
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                
                # Очистка форматирования
                ai_response = ai_response.replace('###', '').replace('**', '')
                
                # Добавляем информацию о версии
                ai_response += f"\n\n🤖 Консультация предоставлена ветеринарным ботом v{VERSION}"
                ai_response += "\n⚠️ Для точного диагноза рекомендуется очный осмотр"
                
                return ai_response
            else:
                logger.error(f"DeepSeek API error: {response.status_code}")
                return AIService.get_fallback_response()
                
        except Exception as e:
            logger.error(f"Error getting AI consultation: {e}")
            return AIService.get_fallback_response()
    
    @staticmethod
    def get_fallback_response() -> str:
        """
        Резервный ответ в случае ошибки
        
        Returns:
            str: Резервный ответ
        """
        return """😿 Извините, в данный момент я не могу предоставить консультацию.

Возможные причины:
1. Технические проблемы с AI-сервисом
2. Высокая нагрузка на сервер
3. Проблемы с подключением

Пожалуйста, попробуйте повторить запрос позже или обратитесь к живому ветеринару.

🤖 Ветеринарный бот"""