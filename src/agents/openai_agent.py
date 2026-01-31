from agents import Agent, Runner
from loguru import logger
from src.config import settings
from src.agents.agent_config import (
    AGENT_INSTRUCTIONS,
    AGENT_MODEL,
    AGENT_NAME
)


class PersonalAssistantAgent:
    """Personal Assistant Agent using OpenAI Agents SDK"""
    
    def __init__(self):
        # Create agent
        self.agent = Agent(
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            model=AGENT_MODEL
        )
        
        logger.info(f"🤖 {AGENT_NAME} initialized with model {AGENT_MODEL}")
    
    async def run_agent(self, session_id: str, user_message: str) -> tuple[str, bool]:
        """
        Run the agent with user message and get response
        
        Args:
            session_id: The session ID (managed by openai-agents automatically)
            user_message: The user's message
            
        Returns:
            tuple: (response_text, needs_transfer)
        """
        try:
            result = await Runner.run(
                self.agent,
                input=user_message,
                session_id=session_id
            )
            
            # Extract response
            response_text = result.final_output
            
            if not response_text:
                logger.warning("⚠️ Empty response from agent")
                return "Desculpe, não consegui processar sua mensagem. Pode reformular?", False
            
            # Check if transfer is needed
            needs_transfer = "[TRANSFERIR]" in response_text
            response_text = response_text.replace("[TRANSFERIR]", "").strip()
            
            logger.info(f"✅ Agent response generated ({len(response_text)} chars)")
            if needs_transfer:
                logger.warning(f"⚠️ Transfer flag detected in response")
            
            return response_text, needs_transfer
        
        except Exception as e:
            logger.error(f"❌ Error running agent: {e}")
            return "Desculpe, tive um problema técnico. Vou transferir você para um atendente.", True
    
    def get_stats(self) -> dict:
        """Get agent statistics"""
        return {
            "name": self.agent.name,
            "model": self.agent.model
        }


agent = PersonalAssistantAgent()