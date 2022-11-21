from abc import ABC
from abc import abstractmethod


class QuestionStrategy(ABC):
    @abstractmethod
    def follow_up_question(self, context) -> str:
        pass


class ElaborateQuestionStrategy(QuestionStrategy):
    def follow_up_question(self, context) -> str:
        return "Can you elaborate?"