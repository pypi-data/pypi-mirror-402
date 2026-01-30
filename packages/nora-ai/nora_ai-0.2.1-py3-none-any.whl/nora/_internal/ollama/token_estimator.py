"""
토큰 수 추정 유틸리티 (tiktoken 사용)
"""

from typing import Optional, List, Dict, Any


def estimate_tokens(text: str, model: Optional[str] = None) -> int:
    """
    tiktoken을 사용하여 토큰 수를 추정합니다.
    
    Args:
        text: 토큰 수를 추정할 텍스트
        model: 모델 이름 (선택적)
        
    Returns:
        추정된 토큰 수
    """
    try:
        import tiktoken
        
        # Ollama 모델은 대부분 GPT-3.5/4와 유사한 토크나이저 사용
        # 기본적으로 cl100k_base 사용 (GPT-3.5/4 인코딩)
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # fallback to gpt2 encoding
            encoding = tiktoken.get_encoding("gpt2")
        
        tokens = encoding.encode(text)
        return len(tokens)
    except ImportError:
        # tiktoken이 설치되지 않은 경우 대략적인 추정
        # 일반적으로 1 토큰 ≈ 4 문자 (영어 기준)
        return len(text) // 4
    except Exception:
        # 기타 오류 발생 시 0 반환
        return 0


def estimate_messages_tokens(messages: List[Dict[str, Any]]) -> int:
    """
    메시지 리스트의 토큰 수를 추정합니다.
    
    Args:
        messages: 메시지 리스트
        
    Returns:
        추정된 토큰 수
    """
    total = 0
    for message in messages:
        # role 토큰
        role = message.get("role", "")
        total += estimate_tokens(role)
        
        # content 토큰
        content = message.get("content", "")
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif isinstance(content, list):
            # multimodal content
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    total += estimate_tokens(item.get("text", ""))
        
        # 메시지 구조 오버헤드 (~4 토큰)
        total += 4
    
    # 시스템 메시지 오버헤드
    total += 3
    
    return total
