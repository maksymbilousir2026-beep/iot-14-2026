import json
import logging
import os
from functools import wraps


class FileHandlerError(Exception):
    pass


class FileNotFound(FileHandlerError):
    pass


class FileCorrupted(FileHandlerError):
    pass


def logged(exception, mode="console", log_file="file_events.log"):

    if mode not in ("console", "file"):
        raise ValueError('mode має бути "console" або "file"')

    logger = logging.getLogger(f"logged.{mode}.{log_file if mode == 'file' else ''}")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = (logging.StreamHandler() if mode == "console"
                   else logging.FileHandler(log_file, encoding="utf-8"))
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(handler)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                logger.info("Операція '%s' виконана успішно", func.__name__)
                return result
            except exception as e:
                logger.error("Помилка в '%s': %s: %s",
                             func.__name__, type(e).__name__, e)
                raise
        return wrapper
    return decorator


class JsonFileHandler:
    def __init__(self, path, filename):
        self.filepath = os.path.join(path, filename)
        self._check_exists()

    @logged(FileNotFound, mode="file")
    def _check_exists(self):
        if not os.path.isfile(self.filepath):
            raise FileNotFound(f"Файл не знайдено: {self.filepath}")

    @logged(FileCorrupted, mode="console")
    def read(self):
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return json.loads(content) if content.strip() else None
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            raise FileCorrupted(f"Не вдалося прочитати файл: {e}") from e

    @logged(FileCorrupted, mode="console")
    def write(self, data):
        try:
            text = json.dumps(data, ensure_ascii=False, indent=4)
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write(text)
        except (OSError, TypeError, ValueError) as e:
            raise FileCorrupted(f"Не вдалося записати у файл: {e}") from e

    @logged(FileCorrupted, mode="console")
    def append(self, data):

        current = self.read()

        if current is None:
            new_content = data
        elif isinstance(current, list):
            new_content = current + (data if isinstance(data, list) else [data])
        elif isinstance(current, dict) and isinstance(data, dict):
            new_content = {**current, **data}
        else:
            raise TypeError(
                f"Не можна дописати {type(data).__name__} "
                f"до {type(current).__name__}")

        self.write(new_content)


if __name__ == "__main__":
    path, name = ".", "data.json"

    try:
        JsonFileHandler(path, name)
    except FileNotFound:
        open(os.path.join(path, name), "w").close()

    handler = JsonFileHandler(path, name)
    handler.write([{"імʼя": "Олена", "вік": 28}])
    handler.append({"імʼя": "Іван", "вік": 35})
    print(handler.read())