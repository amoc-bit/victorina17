from django.db import models
from django.contrib.auth.models import AbstractUser

from django.db.models import F, Sum, IntegerField
from django.db.models.options import Options

from django.utils import timezone

# ver 2.2.0 готово не проверено

# pylint: disable=no-member

class User(AbstractUser):
    """Расширенная модель пользователя с ролью и связью с командой."""

    class Role(models.TextChoices):
        CHIEF = "CHIEF", "Администратор"
        PLAYER = "PLAYER", "Игрок"
        OWNER = "OWNER", "Владелец"

    role = models.CharField(
        max_length=10, choices=Role.choices, default=Role.PLAYER, verbose_name="Роль"
    )
    telegram_id = models.BigIntegerField(unique=True, verbose_name="ID в Telegram")

    team = models.ForeignKey(
        "Team", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Команда"
    )
    group = models.CharField(max_length=100, verbose_name="Название группы")
    last_activity = models.DateTimeField(
        default=timezone.now, verbose_name="Последняя активность в боте"
    )
    # Исправление конфликта related_name
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="группы",
        blank=True,
        related_name="quiz_user_set",  # Добавьте это
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="права пользователя",
        blank=True,
        related_name="quiz_user_set",  # Добавьте это
        related_query_name="user",
    )
      

    def __str__(self):
        return f"{self.username} ({self.role})"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._meta.get_field("username").verbose_name = "Имя пользователя"

    # ...


class Team(models.Model):
    """Модель команды, создается администратором."""

    name = models.CharField(max_length=100, verbose_name="Название команды")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_teams",
        verbose_name="Создатель",
    )

    def __str__(self):
        return str(self.name)


class Question(models.Model):
    """Вопрос, созданный игроком. Администратор проверяет его перед использованием."""

    text = models.TextField(verbose_name="Текст вопроса")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Автор вопроса",
    )
    is_approved = models.BooleanField(
        default=False, verbose_name="Одобрен администратором"
    )
    correct_answer = models.CharField(max_length=255, verbose_name="Правильный ответ")
    """вес вопроса"""
    points = models.PositiveIntegerField(default=1, verbose_name="Вес вопроса")

    def __init__(self, text: str, created_by):
        self.text: str = text
        self.created_by = created_by

    def __str__(self):

        return f"Вопрос от {self.created_by.username}: {self.text[:50]}..."


class Answer(models.Model):
    """Ответ игрока на вопрос. Оценивается администратором."""

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Вопрос",
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="answers", verbose_name="Игрок"
    )
    text = models.CharField(max_length=255, verbose_name="Ответ игрока")
    is_correct = models.BooleanField(default=False, verbose_name="Правильность ответа")
    admin_score = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Оценка администратора"
    )
    """вес вопроса"""
    points = models.IntegerField(
        verbose_name="Баллы вопроса", help_text="Копия баллов из связанного вопроса"
    )
    """автоматическое  копирование аналогичного поля из class Question при создании"""

    def save(self, *args, **kwargs):
        if not self.pk:  # Только при создании
            self.points = self.question.points
        super().save(*args, **kwargs)

    def __init__(self, text: str):
        self.text: str = text

    def __str__(self):
        return f"Ответ {self.user.username} на вопрос {self.question.id}: {self.text[:20]}..."


class GameSession(models.Model):
    """Сессия игры с возможными статусами."""

    class Status(models.TextChoices):
        WAITING = "WAITING", "Ожидание"
        ACTIVE = "ACTIVE", "Активна"
        FINISHED = "FINISHED", "Завершена"

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.WAITING,
        verbose_name="Статус сессии",
    )
    """Сессия игры, связывает вопросы, ответы и команды."""
    teams = models.ManyToManyField(Team, verbose_name="Команды")
    questions = models.ManyToManyField(Question, verbose_name="Вопросы")
    start_time = models.DateTimeField(auto_now_add=True, verbose_name="Время начала")
    end_time = models.DateTimeField(
        null=True, blank=True, verbose_name="Время окончания"
    )

    def __str__(self):
        return f"Игра от {self.start_time} ({self.get_status_display()})"

    def start_session(self):
        """Переводит сессию в статус 'Активна'."""
        self.status = self.Status.ACTIVE
        self.save()

    def finish_session(self):
        """Завершает сессию и фиксирует время окончания."""
        self.status = self.Status.FINISHED
        self.end_time = timezone.now()
        self.save()

        # Все вычисления в одном запросе

    def calculate_scores(self):
        """Подсчет итоговых баллов для команд (только для завершённых сессий)."""
        if self.status != self.Status.FINISHED:
            raise ValueError("Подсчёт очков доступен только для завершённых сессий")

        scores = {}
        for team in self.teams.all():
            team_answers = Answer.objects.filter(
                user__team=team, question__in=self.questions.all()
            ).select_related(
                "question"
            )  # Оптимизация: избегаем N+1 запросов

            total = sum(
                (answer.admin_score if answer.admin_score else 0)
                * (answer.question.points if answer.question.points else 0)
                for answer in team_answers
            )
            scores[team.name] = total

        return scores


# pylint: disable=no-member
