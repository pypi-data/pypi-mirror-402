import random
import secrets
import string
import uuid


def generate_difficult_password(*, difficult: int = 1):
    # динамический диапазон длины
    base = 32 + difficult * 16
    variance = 64 + difficult * 32
    target_len = random.randint(base, base + variance)

    # ТОЛЬКО английские буквы и цифры
    alphabet = string.ascii_letters + string.digits

    password = []

    # UUID-шум (hex = 0-9 + a-f)
    for _ in range(difficult * 2):
        password.append(uuid.uuid4().hex)

    # основная часть
    for _ in range(target_len):
        password.append(secrets.choice(alphabet))

    secrets.SystemRandom().shuffle(password)

    return "".join(password)


def __example():
    print(generate_difficult_password(difficult=2))


if __name__ == '__main__':
    __example()
