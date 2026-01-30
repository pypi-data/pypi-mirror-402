"""Celery tasks API routes"""

from fastapi import APIRouter, HTTPException

from yitool.yi_celery import yi_celery
from yitool.yi_celery.email_tasks import send_email_task as email_task

# 创建路由实例
router = APIRouter(
    prefix="/api/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态

    根据任务ID查询任务状态和结果。

    Args:
        task_id: 任务ID

    Returns:
        dict: 包含任务状态和结果的字典

    Raises:
        HTTPException: 如果任务不存在或查询失败
    """
    try:
        # 获取任务结果
        task_result = yi_celery.AsyncResult(task_id)

        # 准备响应数据
        response = {
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result if task_result.status == "SUCCESS" else None,
            "error": str(task_result.result) if task_result.status == "FAILURE" else None,
        }

        # 如果任务正在执行中，添加进度信息
        if task_result.status == "PROGRESS" and isinstance(task_result.result, dict):
            response.update({
                "progress": task_result.result.get("current", 0),
                "total": task_result.result.get("total", 0),
                "percentage": round(
                   (task_result.result.get("current", 0) / task_result.result.get("total", 1)) * 100, 2
               )
            })

        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting task status: {str(e)}"
        ) from e


@router.post("/email")
async def send_email(to: str, subject: str, body: str, is_html: bool = False):
    """发送邮件异步任务

    创建一个发送邮件的异步任务。

    Args:
        to: 收件人邮箱地址
        subject: 邮件主题
        body: 邮件正文
        is_html: 是否为HTML邮件，默认为False

    Returns:
        dict: 包含任务ID和状态的字典
    """
    # 调用异步任务
    task_result = email_task.delay(to, subject, body, is_html)

    return {
        "task_id": task_result.id,
        "status": "queued",
        "message": "Email task has been created!",
        "task_url": f"/api/tasks/{task_result.id}"
    }
