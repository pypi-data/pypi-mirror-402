"""Email-related Celery tasks"""

from yitool.yi_celery import yi_celery


@yi_celery.task(name="send_email", bind=True, retry_backoff=True, retry_kwargs={"max_retries": 3})
async def send_email_task(self, to: str, subject: str, body: str, is_html: bool = False):
    """发送邮件异步任务

    模拟发送邮件，支持HTML邮件。

    Args:
        self: 任务实例
        to: 收件人邮箱地址
        subject: 邮件主题
        body: 邮件正文
        is_html: 是否为HTML邮件，默认为False

    Returns:
        dict: 包含发送结果的字典
    """
    try:
        # 将单个收件人转换为列表
        recipients = [to] if isinstance(to, str) else to

        # 模拟发送邮件（实际项目中应替换为真实的邮件服务调用）
        # 这里简单返回成功，实际使用时需要集成真实的邮件服务
        result = True

        return {
            "status": "success" if result else "failed",
            "to": recipients,
            "subject": subject,
            "is_html": is_html,
            "message": "Email sent successfully!" if result else "Failed to send email!"
        }
    except Exception as e:
        # 记录错误日志
        self.logger.error(f"Error sending email: {str(e)}")
        # 任务失败，自动重试
        self.retry(exc=e)


@yi_celery.task(name="send_batch_emails", bind=True, retry_backoff=True, retry_kwargs={"max_retries": 3})
async def send_batch_emails_task(self, emails: list):
    """批量发送邮件异步任务

    批量发送邮件，每个邮件包含收件人、主题和正文。

    Args:
        self: 任务实例
        emails: 邮件列表，每个邮件是一个字典，包含to, subject, body, is_html字段

    Returns:
        dict: 包含批量发送结果的字典
    """
    try:
        results = []

        # 逐个发送邮件
        for email in emails:
            # 模拟发送邮件（实际项目中应替换为真实的邮件服务调用）
            result = True

            results.append({
                "to": email["to"],
                "status": "success" if result else "failed"
            })

        # 计算成功和失败的数量
        success_count = sum(1 for r in results if r["status"] == "success")
        failed_count = sum(1 for r in results if r["status"] == "failed")

        return {
            "status": "completed",
            "total": len(emails),
            "success": success_count,
            "failed": failed_count,
            "results": results,
            "message": f"Batch email sending completed: {success_count} succeeded, {failed_count} failed"
        }
    except Exception as e:
        # 记录错误日志
        self.logger.error(f"Error sending batch emails: {str(e)}")
        # 任务失败，自动重试
        self.retry(exc=e)
