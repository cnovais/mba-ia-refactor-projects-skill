import logging
import smtplib

from utils.helpers import utcnow

logger = logging.getLogger(__name__)


class NotificationService:
    """Sends task e-mails. SMTP settings and transport are injected by the composition root."""

    def __init__(self, host, port, user, password, smtp_factory=smtplib.SMTP, timeout=10):
        self.notifications = []
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._smtp_factory = smtp_factory
        self._timeout = timeout

    @property
    def enabled(self):
        return bool(self._host and self._user and self._password)

    def send_email(self, to, subject, body):
        if not self.enabled:
            logger.warning('SMTP não configurado; email para %s não enviado', to)
            return False
        try:
            with self._smtp_factory(self._host, self._port, timeout=self._timeout) as server:
                server.starttls()
                server.login(self._user, self._password)
                server.sendmail(self._user, to, f"Subject: {subject}\n\n{body}")
            logger.info('Email enviado para %s', to)
            return True
        except (smtplib.SMTPException, OSError):
            logger.exception('Erro ao enviar email para %s', to)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': utcnow(),
        })

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [notification for notification in self.notifications if notification['user_id'] == user_id]
