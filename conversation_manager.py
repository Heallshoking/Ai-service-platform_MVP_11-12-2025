"""
Conversation Manager - AI-powered conversation system
Управление AI-диалогами с клиентами и мастерами
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class ConversationType(str, Enum):
    """Типы разговоров"""
    CLIENT_REQUEST = "client_request"
    MASTER_ONBOARDING = "master_onboarding"


class ConversationChannel(str, Enum):
    """Каналы коммуникации"""
    PHONE = "phone"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    FORM = "form"
    WEBSITE = "website"


class ConversationStatus(str, Enum):
    """Статусы разговора"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class Message:
    """Сообщение в разговоре"""
    def __init__(self, role: str, content: str, timestamp: datetime = None):
        self.role = role  # 'user' или 'assistant'
        self.content = content
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Message':
        return Message(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


class Conversation:
    """Управление одним разговором"""
    
    def __init__(
        self,
        conversation_type: ConversationType,
        channel: ConversationChannel,
        participant_name: Optional[str] = None,
        participant_phone: Optional[str] = None,
        conversation_id: Optional[str] = None
    ):
        self.id = conversation_id or str(uuid.uuid4())
        self.type = conversation_type
        self.channel = channel
        self.participant_name = participant_name
        self.participant_phone = participant_phone
        self.messages: List[Message] = []
        self.status = ConversationStatus.ACTIVE
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.audio_url: Optional[str] = None
        self.extracted_data: Dict[str, Any] = {}
    
    def add_message(self, role: str, content: str):
        """Добавить сообщение в разговор"""
        message = Message(role=role, content=content)
        self.messages.append(message)
    
    def get_transcript(self) -> str:
        """Получить полную текстовую транскрипцию"""
        transcript = []
        for msg in self.messages:
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            speaker = "Клиент" if msg.role == "user" else "AI"
            transcript.append(f"[{timestamp}] {speaker}: {msg.content}")
        return "\n".join(transcript)
    
    def complete(self):
        """Завершить разговор"""
        self.status = ConversationStatus.COMPLETED
        self.completed_at = datetime.now()
    
    def abandon(self):
        """Отменить разговор"""
        self.status = ConversationStatus.ABANDONED
        self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Сериализация в словарь"""
        return {
            "id": self.id,
            "type": self.type.value,
            "channel": self.channel.value,
            "participant_name": self.participant_name,
            "participant_phone": self.participant_phone,
            "messages": [msg.to_dict() for msg in self.messages],
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "audio_url": self.audio_url,
            "extracted_data": self.extracted_data
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Conversation':
        """Десериализация из словаря"""
        conv = Conversation(
            conversation_type=ConversationType(data["type"]),
            channel=ConversationChannel(data["channel"]),
            participant_name=data.get("participant_name"),
            participant_phone=data.get("participant_phone"),
            conversation_id=data["id"]
        )
        conv.messages = [Message.from_dict(msg) for msg in data.get("messages", [])]
        conv.status = ConversationStatus(data["status"])
        conv.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("completed_at"):
            conv.completed_at = datetime.fromisoformat(data["completed_at"])
        conv.audio_url = data.get("audio_url")
        conv.extracted_data = data.get("extracted_data", {})
        return conv


class ConversationManager:
    """Менеджер разговоров с AI"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._init_conversations_table()
    
    def _init_conversations_table(self):
        """Инициализация таблицы разговоров"""
        cursor = self.db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                channel TEXT NOT NULL,
                participant_name TEXT,
                participant_phone TEXT,
                messages_json TEXT,
                transcript TEXT,
                audio_url TEXT,
                status TEXT DEFAULT 'active',
                extracted_data_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        self.db.commit()
    
    def create_conversation(
        self,
        conversation_type: ConversationType,
        channel: ConversationChannel,
        participant_name: Optional[str] = None,
        participant_phone: Optional[str] = None
    ) -> Conversation:
        """Создать новый разговор"""
        conversation = Conversation(
            conversation_type=conversation_type,
            channel=channel,
            participant_name=participant_name,
            participant_phone=participant_phone
        )
        
        self._save_conversation(conversation)
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Получить разговор по ID"""
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_conversation(row)
    
    def add_message(self, conversation_id: str, role: str, content: str):
        """Добавить сообщение в разговор"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation.add_message(role, content)
        self._save_conversation(conversation)
    
    def complete_conversation(self, conversation_id: str, extracted_data: Dict[str, Any] = None):
        """Завершить разговор"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        if extracted_data:
            conversation.extracted_data = extracted_data
        
        conversation.complete()
        self._save_conversation(conversation)
    
    def _save_conversation(self, conversation: Conversation):
        """Сохранить разговор в БД"""
        cursor = self.db.cursor()
        
        messages_json = json.dumps([msg.to_dict() for msg in conversation.messages], ensure_ascii=False)
        extracted_data_json = json.dumps(conversation.extracted_data, ensure_ascii=False)
        transcript = conversation.get_transcript()
        
        cursor.execute("""
            INSERT OR REPLACE INTO conversations (
                id, type, channel, participant_name, participant_phone,
                messages_json, transcript, audio_url, status, extracted_data_json,
                created_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            conversation.id,
            conversation.type.value,
            conversation.channel.value,
            conversation.participant_name,
            conversation.participant_phone,
            messages_json,
            transcript,
            conversation.audio_url,
            conversation.status.value,
            extracted_data_json,
            conversation.created_at.isoformat(),
            conversation.completed_at.isoformat() if conversation.completed_at else None
        ))
        
        self.db.commit()
    
    def _row_to_conversation(self, row) -> Conversation:
        """Преобразовать строку БД в объект Conversation"""
        return Conversation.from_dict({
            "id": row[0],
            "type": row[1],
            "channel": row[2],
            "participant_name": row[3],
            "participant_phone": row[4],
            "messages": json.loads(row[5]) if row[5] else [],
            "status": row[8],
            "extracted_data": json.loads(row[9]) if row[9] else {},
            "created_at": row[10],
            "completed_at": row[11],
            "audio_url": row[7]
        })


class ClientRequestConversation:
    """Специализированный класс для разговора с клиентом о запросе"""
    
    QUESTIONS = {
        "problem": "Расскажите, пожалуйста, подробнее о проблеме. Что именно не работает?",
        "location": "Укажите, пожалуйста, адрес, по которому нужно выполнить работы?",
        "timing": "Когда вам удобно, чтобы мастер приехал?",
        "urgency": "Это срочный вызов или можно запланировать на ближайшие дни?",
        "photos": "Можете отправить фото проблемы? Это поможет мастеру лучше подготовиться.",
    }
    
    def __init__(self, conversation: Conversation):
        self.conversation = conversation
        self.required_fields = ["problem", "location", "category"]
        self.extracted = conversation.extracted_data
    
    def get_next_question(self) -> Optional[str]:
        """Получить следующий вопрос для клиента"""
        # Проверяем, какие поля уже собраны
        if "problem" not in self.extracted:
            return self.QUESTIONS["problem"]
        
        if "location" not in self.extracted:
            return self.QUESTIONS["location"]
        
        if "timing" not in self.extracted:
            return self.QUESTIONS["timing"]
        
        # Опциональные вопросы
        if "urgency" not in self.extracted:
            return self.QUESTIONS["urgency"]
        
        if "photos" not in self.extracted and "photos_requested" not in self.extracted:
            self.extracted["photos_requested"] = True
            return self.QUESTIONS["photos"]
        
        return None  # Все вопросы заданы
    
    def is_complete(self) -> bool:
        """Проверка, собрана ли вся необходимая информация"""
        return all(field in self.extracted for field in self.required_fields)
    
    def extract_info_from_message(self, message: str, ai_analysis: Dict = None):
        """Извлечь информацию из сообщения клиента"""
        # Здесь будет AI-анализ сообщения
        # Пока простая логика
        if ai_analysis:
            self.extracted.update(ai_analysis)
        
        # Сохранить обновленные данные
        self.conversation.extracted_data = self.extracted


class MasterOnboardingConversation:
    """Специализированный класс для онбординга мастера"""
    
    QUESTIONS = {
        "name": "Как вас зовут?",
        "phone": "Укажите, пожалуйста, ваш номер телефона для связи",
        "city": "В каком городе вы работаете?",
        "specializations": "Какие услуги вы оказываете? (электрика, сантехника, бытовая техника, общие работы)",
        "experience": "Сколько лет опыта работы?",
        "schedule": "Когда вы готовы начать принимать заказы?",
    }
    
    def __init__(self, conversation: Conversation):
        self.conversation = conversation
        self.required_fields = ["name", "phone", "city", "specializations"]
        self.extracted = conversation.extracted_data
    
    def get_next_question(self) -> Optional[str]:
        """Получить следующий вопрос для мастера"""
        if "name" not in self.extracted:
            return self.QUESTIONS["name"]
        
        if "phone" not in self.extracted:
            return self.QUESTIONS["phone"]
        
        if "city" not in self.extracted:
            return self.QUESTIONS["city"]
        
        if "specializations" not in self.extracted:
            return self.QUESTIONS["specializations"]
        
        if "experience" not in self.extracted:
            return self.QUESTIONS["experience"]
        
        if "schedule" not in self.extracted:
            return self.QUESTIONS["schedule"]
        
        return None
    
    def is_complete(self) -> bool:
        """Проверка, собрана ли вся необходимая информация"""
        return all(field in self.extracted for field in self.required_fields)
