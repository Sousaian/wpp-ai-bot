from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger

from src.config import settings
from src.agents.openai_agent import agent
from src.services.evolution_client import evolution_client
from src.services.session_manager import session_manager


# Configurar logger
logger.add("logs/app.log", rotation="1 day", retention="7 days", level="INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    logger.info("🚀 Starting application...")
    
    # Setup ngrok if enabled
    if settings.use_ngrok:
        from pyngrok import ngrok, conf
        # Configure ngrok
        conf.get_default().auth_token = settings.ngrok_auth_token
        conf.get_default().region = "us"  # ou "sa" para South America
        
        public_url = ngrok.connect(settings.app_port)
        logger.info(f"🌐 ngrok tunnel: {public_url}")
        logger.info(f"📍 Webhook URL: {public_url}/webhook")
    
    yield
    
    logger.info("👋 Shutting down application...")


app = FastAPI(
    title="MVP Atendimento Pós-Venda IA",
    description="Sistema de atendimento automatizado via WhatsApp",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "MVP Atendimento IA",
        "version": "0.1.0"
    }


@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Webhook endpoint to receive messages from Evolution API
    """
    try:
        # Parse incoming data
        data = await request.json()
        
        logger.info(f"📥 Webhook received: {data}")
        
        # Extract message info
        event = data.get("event")
        
        if event == "messages.upsert":
            # New message received
            message_data = data.get("data", {})
            
            # Extract key fields
            phone = message_data.get("key", {}).get("remoteJid", "").replace("@s.whatsapp.net", "")
            message_content = message_data.get("message", {})
            
            # Get text content
            text = None
            if "conversation" in message_content:
                text = message_content["conversation"]
            elif "extendedTextMessage" in message_content:
                text = message_content["extendedTextMessage"].get("text")
            
            if not text:
                logger.warning("⚠️ No text content found in message")
                return {"status": "ignored", "reason": "no_text"}
            
            # Check if message is from us (ignore own messages)
            if message_data.get("key", {}).get("fromMe"):
                logger.info("↩️ Ignoring own message")
                return {"status": "ignored", "reason": "own_message"}
            
            logger.info(f"💬 Message from {phone}: {text}")
            
            # Get or create session
            session = session_manager.get_session(phone)
            
            if not session:
                # Create new conversation
                conversation_id = agent.create_conversation()
                session = session_manager.create_session(phone, conversation_id)
            
            conversation_id = session["conversation_id"]
            
            # Check if bot should handle
            if not session_manager.is_bot_handler(phone):
                logger.info(f"👤 Message forwarded to human handler for {phone[:8]}...")
                return {"status": "forwarded_to_human", "phone": phone}
            
            # Process with OpenAI Agent
            try:
                response_text, needs_transfer = agent.run_agent(conversation_id, text)
                
                # Update session
                session_manager.increment_message_count(phone)
                
                # Check if needs transfer to human
                if needs_transfer:
                    session_manager.set_handler(phone, "human")
                    logger.warning(f"⚠️ Transfer to human requested for {phone[:8]}...")
                
                # Send response via Evolution
                await evolution_client.send_text_message(phone, response_text)
                
                logger.info(f"✅ Response sent to {phone[:8]}...")
                
                return {
                    "status": "success",
                    "phone": phone,
                    "needs_transfer": needs_transfer
                }
            
            except Exception as e:
                logger.error(f"❌ Error processing message: {e}")
                # Send error message to user
                error_msg = "Desculpe, estou com problemas técnicos no momento. Um atendente vai te ajudar em breve."
                await evolution_client.send_text_message(phone, error_msg)
                session_manager.set_handler(phone, "human")
                
                return {
                    "status": "error",
                    "phone": phone,
                    "error": str(e)
                }
        
        else:
            logger.info(f"ℹ️ Event type '{event}' - no action needed")
            return {"status": "ignored", "event": event}
    
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check for monitoring"""
    return {"status": "healthy"}


@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    sessions = session_manager.get_all_sessions()
    return {
        "total": len(sessions),
        "sessions": sessions
    }


@app.post("/sessions/{phone}/transfer")
async def transfer_to_human(phone: str):
    """Transfer session to human handler"""
    session = session_manager.get_session(phone)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_manager.set_handler(phone, "human")
    return {"status": "transferred", "phone": phone}


@app.post("/sessions/{phone}/resume")
async def resume_bot_handler(phone: str):
    """Resume bot handler for session"""
    session = session_manager.get_session(phone)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_manager.set_handler(phone, "bot")
    return {"status": "resumed", "phone": phone}


@app.delete("/sessions/{phone}")
async def delete_session(phone: str):
    """Delete a session"""
    session_manager.delete_session(phone)
    return {"status": "deleted", "phone": phone}


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )