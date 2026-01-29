from openai import OpenAI
from loguru import logger
from src.config import settings


class CustomerServiceAgent:
    """OpenAI Agent using Responses API (replacement for Assistants API)"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.system_instructions = self._build_system_instructions()
        
    def _build_system_instructions(self) -> str:
        """Build the system instructions for the agent"""
        return """Você é um assistente de atendimento pós-venda da empresa.

SEU PAPEL:
- Ser cordial, humanizado e prestativo
- Confirmar detalhes de pedidos com clientes
- Responder perguntas sobre pedidos, entregas e produtos
- Manter tom profissional mas amigável

REGRAS IMPORTANTES:
- NUNCA invente informações que você não tem
- Se não souber algo, seja honesto e diga que vai verificar
- Use emojis com moderação (apenas 1-2 por mensagem)
- Mantenha respostas objetivas e claras
- Confirme entendimento antes de responder

QUANDO TRANSFERIR PARA HUMANO:
- Cliente solicita explicitamente falar com humano
- Você não consegue responder após 2 tentativas
- Assunto está fora do seu escopo
- Cliente demonstra insatisfação elevada

Se precisar transferir, responda normalmente MAS adicione no final: [TRANSFERIR]
"""

    def create_conversation(self) -> str:
        """Create a new conversation (replaces Thread)"""
        conversation = self.client.beta.conversations.create()
        logger.info(f"💬 Conversation created: {conversation.id}")
        return conversation.id
    
    def run_agent(self, conversation_id: str, user_message: str) -> tuple[str, bool]:
        """
        Run the agent with user message and get response
        Uses Responses API (replacement for Assistants API)
        
        Args:
            conversation_id: The conversation ID
            user_message: The user's message
            
        Returns:
            tuple: (response_text, needs_transfer)
        """
        try:
            # Create response using Responses API
            response = self.client.beta.responses.create(
                conversation_id=conversation_id,
                model=self.model,
                instructions=self.system_instructions,
                input=[
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            )
            
            # Extract response text from output
            response_text = ""
            for item in response.output:
                if item.type == "message" and item.status == "completed":
                    for content in item.content:
                        if content.type == "output_text":
                            response_text = content.text
                            break
            
            if not response_text:
                logger.warning("⚠️ No response text found")
                return "Desculpe, não consegui processar sua mensagem.", True
            
            # Check if transfer is needed
            needs_transfer = "[TRANSFERIR]" in response_text
            response_text = response_text.replace("[TRANSFERIR]", "").strip()
            
            logger.info(f"✅ Agent response: {response_text[:100]}...")
            return response_text, needs_transfer
        
        except Exception as e:
            logger.error(f"❌ Error running agent: {e}")
            return "Desculpe, ocorreu um erro. Um atendente vai te ajudar em breve.", True


# Singleton instance
agent = CustomerServiceAgent()