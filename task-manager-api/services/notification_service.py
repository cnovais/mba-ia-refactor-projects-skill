import logging
import smtplib

logger = logging.getLogger("task_manager")


class NotificationService:
    """Sends task-related emails. SMTP connection details are injected instead of
    hardcoded, so this can be constructed with test doubles / disabled config.

    Methods take plain values (email/name/title/...) rather than Task/User ORM
    objects on purpose: this class is called from a background thread (see
    controllers/task_controller.py's `_notify_assignment_async`) so it must never
    touch a SQLAlchemy session — those are request/thread-scoped and would raise
    `DetachedInstanceError` (or silently race the main thread) if accessed after the
    request that created them has already returned.
    """

    def __init__(self, host, port, user, password):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.notifications = []

    def send_email(self, to, subject, body):
        if not self.user or not self.password:
            logger.warning("SMTP not configured — skipping email to %s: %s", to, subject)
            return False
        try:
            server = smtplib.SMTP(self.host, self.port)
            server.starttls()
            server.login(self.user, self.password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(self.user, to, message)
            server.quit()
            logger.info("Email enviado para %s", to)
            return True
        except Exception:
            logger.exception("Erro ao enviar email para %s", to)
            return False

    def notify_task_assigned(self, *, user_id, user_email, user_name, task_id, task_title, task_priority, task_status):
        subject = f"Nova task atribuída: {task_title}"
        body = (
            f"Olá {user_name},\n\nA task '{task_title}' foi atribuída a você.\n\n"
            f"Prioridade: {task_priority}\nStatus: {task_status}"
        )
        sent = self.send_email(user_email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user_id,
            'task_id': task_id,
            'sent': sent,
        })
        return sent

    def notify_task_overdue(self, *, user_email, user_name, task_title, due_date):
        subject = f"Task atrasada: {task_title}"
        body = f"Olá {user_name},\n\nA task '{task_title}' está atrasada!\n\nData limite: {due_date}"
        return self.send_email(user_email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n['user_id'] == user_id]
