from typing import List, Tuple

class InlineKeyboard:
    def __init__(self):
        self.rows: List[List[Tuple[str, str]]] = []

    def add_row(self, *buttons: Tuple[str, str]):
        self.rows.append(list(buttons))

    def to_dict(self):
        """Konwertuje do formatu Telegrama"""
        return {
            "inline_keyboard": [
                [{"text": text, "callback_data": data} for text, data in row]
                for row in self.rows
            ]
        }

class ReplyKeyboard:
    def __init__(self):
        self.rows: List[List[str]] = []

    def add_row(self, *buttons: str):
        self.rows.append(list(buttons))

    def to_dict(self):
        return {"keyboard": self.rows, "resize_keyboard": True}
