
from fastapi import Cookie, Request

from .manager import YiSessionManager, yi_session_manager


async def yi_get_session(
    session_id: str | None = Cookie(None, alias="session_id"),
) -> dict[str, any]:
    """
    获取当前会话数据
    
    Args:
        session_id: 会话ID，从Cookie中获取
    
    Returns:
        Dict[str, any]: 会话数据
    """
    if not session_id:
        # 如果没有会话ID，创建新会话
        await yi_session_manager.create_session()
        # 需要在中间件中设置Cookie，这里只返回空会话数据
        return {}

    # 获取会话数据
    session_data = await yi_session_manager.get_session_data(session_id)
    if not session_data:
        # 如果会话不存在，创建新会话
        await yi_session_manager.create_session()
        return {}

    return session_data


async def yi_get_session_id(
    request: Request,
    session_id: str | None = Cookie(None, alias="session_id"),
) -> str | None:
    """
    获取当前会话ID
    
    Args:
        request: 请求对象，用于从状态中获取会话ID
        session_id: 会话ID，从Cookie中获取
    
    Returns:
        Optional[str]: 会话ID
    """
    # 优先从请求状态中获取会话ID（由中间件设置）
    if hasattr(request.state, "session_id"):
        return request.state.session_id
    return session_id


async def yi_get_session_manager() -> YiSessionManager:
    """
    获取会话管理器
    
    Returns:
        SessionManager: 会话管理器
    """
    return yi_session_manager
