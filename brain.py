from openai import OpenAI
from dotenv import load_dotenv
import os
import logging
import sys

# Add the project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables from .env file (for local dev)
# On Vercel, environment variables are already set in the environment
load_dotenv()

# Get API key from environment (Vercel sets this automatically)
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

client = OpenAI(
    api_key=openai_api_key
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Promotional/spam content patterns to filter
PROMOTIONAL_PATTERNS = [
    r"subscribe",
    r"đăng\s*ký",
    r"kênh\s+\w+",
    r"theo\s+dõi",
    r"follow\s+(me|channel)",
    r"like\s+and\s+subscribe",
    r"nhấn\s+(like|đăng\s*ký)",
    r"clip\s+(hay|interesting)",
    r"xem\s+(hết|full)",
    r"link\s+(bio|description)",
    r"donate",
    r"Ủng hộ",
    r"mua\s+xe",
    r"quảng\s*cáo",
    r"khuyến\s*mãi",
    r"giảm\s*giá",
    r"trúng\s*thưởng",
    r"click\s*here",
    r"click\s*link",
]

# Compile regex patterns for efficiency
import re
_promotional_regex = re.compile(
    "|".join(PROMOTIONAL_PATTERNS),
    re.IGNORECASE | re.VERBOSE
)

def _is_promotional_content(text: str) -> bool:
    """
    Check if the text appears to be promotional/spam content
    rather than a genuine user query.
    """
    if not text or len(text.strip()) < 5:
        return True
    
    # Check against promotional patterns
    if _promotional_regex.search(text):
        logger.info(f"Filtered promotional content: {text[:50]}...")
        return True
    
    return False

# Initialize knowledge retriever
_knowledge_loaded = False

def _load_knowledge():
    """Load knowledge base on first use."""
    global _knowledge_loaded
    if _knowledge_loaded:
        return
    
    try:
        # Import with correct relative path
        from backend.knowledge.retriever import retriever
        success = retriever.load_knowledge()
        if success:
            logger.info(f"Knowledge base loaded with {len(retriever.documents)} documents")
            _knowledge_loaded = True
        else:
            # Loading failed, don't mark as loaded to allow retry
            logger.warning("Knowledge base load returned False, will retry")
    except Exception as e:
        logger.warning(f"Failed to load knowledge base: {e}")
        import traceback
        traceback.print_exc()
        # Don't set _knowledge_loaded to True so it can retry


def get_reply(text):
    """
    Get AI reply using knowledge-augmented generation.
    First searches knowledge base, then falls back to OpenAI.
    """
    # Filter out promotional/spam content
    if _is_promotional_content(text):
        return "Xin lỗi, tôi không nghe rõ. Bạn có thể nói lại không?"
    
    # Load knowledge if not loaded
    _load_knowledge()
    
    try:
        from backend.knowledge.retriever import retriever
        
        # Debug: Check knowledge base status
        logger.info(f"Knowledge base loaded: {retriever.has_knowledge()}")
        logger.info(f"Number of documents: {len(retriever.documents)}")
        
        # Check if knowledge base has content
        if retriever.has_knowledge():
            # Search for relevant context with lower similarity threshold
            context, found = retriever.get_answer_context(text, max_chars=3000)
            
            logger.info(f"Search result for '{text[:30]}...': found={found}, context_len={len(context)}")
            
            if context:
                logger.info(f"Found relevant knowledge for: {text[:50]}...")
                logger.info(f"Context preview: {context[:200]}...")
                
                # Use knowledge-augmented response
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": 
                         "Bạn là một trợ lý ảo anime dễ thương tên là Đoàn Viên. "
                         "Hãy trả lời bằng tiếng Việt tự nhiên, ngắn gọn, dễ hiểu. "
                         "Sử dụng THÔNG TIN TÀI LIỆU được cung cấp để trả lời câu hỏi. "
                         "Nếu thông tin trong tài liệu không đủ, hãy nói rằng bạn không có thông tin đó và gợi ý liên hệ cơ quan chức năng."},
                        {"role": "system", "content": f"THÔNG TIN TÀI LIỆU:\n{context}"},
                        {"role": "user", "content": text}
                    ]
                )
                
                return response.choices[0].message.content
            else:
                logger.info(f"No relevant context found in knowledge base for: {text[:50]}...")
    except Exception as e:
        logger.warning(f"Knowledge search failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Fallback to standard OpenAI response
    logger.info(f"Using OpenAI fallback for: {text[:50]}...")
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": 
             "Bạn là một trợ lý ảo anime dễ thương. "
             "Hãy trả lời bằng tiếng Việt tự nhiên, ngắn gọn, dễ hiểu."},
            {"role": "user", "content": text}
        ]
    )

    return response.choices[0].message.content


def reload_knowledge(force: bool = False):
    """Manually reload knowledge base."""
    global _knowledge_loaded
    _knowledge_loaded = False
    
    try:
        from backend.knowledge.retriever import retriever
        retriever.load_knowledge(force_reload=force)
        logger.info("Knowledge base reloaded")
        return True
    except Exception as e:
        logger.error(f"Failed to reload knowledge: {e}")
        return False
