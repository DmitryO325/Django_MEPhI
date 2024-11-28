from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

import datetime

from .models import Question


class QuestionModelTests(TestCase):
    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() возвращает False для вопросов с датой и временем публикации в будущем.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() возвращает False для вопросов опубликованных более суток назад.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)


    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() возвращает True для вопросов опубликованных менее суток назад.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)


def create_question(question_text, days):
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        Отображение сообщения при отсутствии вопросов
        """
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Вопросы не найдены.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_past_question(self):
        """
        Вопросы с pub_date в прошлом показываются на стартовой странице
        """
        question = create_question(question_text="Вопрос из прошлого.", days=-30)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question],
        )

    def test_future_question(self):
        """
        Вопросы с pub_date в будущем не показываются на стартовой странице.
        """
        create_question(question_text="Вопрос из будущего.", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "Вопросы не найдены.")
        self.assertQuerySetEqual(response.context["latest_question_list"], [])

    def test_future_question_and_past_question(self):
        """
        Если есть прошлые и будущие вопросы одновременно, показываются прошлые
        """
        question = create_question(question_text="Прошлый вопрос.", days=-30)
        create_question(question_text="Будущий вопрос.", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question],
        )

    def test_two_past_questions(self):
        """
        На стартовой странице могут показываться несколько вопросов
        """
        question1 = create_question(question_text="Прошлый вопрос 1.", days=-30)
        question2 = create_question(question_text="Прошлый вопрос 2.", days=-5)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question2, question1],
        )


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        DetailView неопубликованного вопроса возвращает 404.
        """
        future_question = create_question(question_text="Будущий вопрос.", days=5)
        url = reverse("polls:detail", args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        DetailView опубликованного вопроса содержит его текст
        """
        past_question = create_question(question_text="Past Question.", days=-5)
        url = reverse("polls:detail", args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)
