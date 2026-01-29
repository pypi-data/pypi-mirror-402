# arpakit

import pyminizip


def make_zip_with_passwd(
        *,
        input_filepath: str,
        output_filename: str = "archive.zip",
        passwd: str = "123"
) -> str:
    pyminizip.compress(
        input_filepath,  # исходный файл
        None,
        output_filename,  # архив
        passwd,  # пароль
        5  # уровень сжатия (1–9)
    )
    return output_filename

