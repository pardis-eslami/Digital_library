import sys
import pandas as pd
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


DATASET_PATH = Path("book_dataset_6000.xlsx")
SHEET_NAME = "کتاب‌شناسی جامع"

REQUIRED_COLUMNS = [
    "ردیف",
    "دسته‌بندی",
    "عنوان کتاب",
    "نویسنده / مؤلف",
    "سال نشر اصلی",
    "بهترین ترجمه در ایران",
    "ناشر",
    "تعداد چاپ",
    "تعداد صفحات",
    "امتیاز",
]


def load_books_dataset():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset file not found: {DATASET_PATH}")

    df = pd.read_excel(DATASET_PATH, sheet_name=SHEET_NAME)

    df.columns = df.columns.astype(str).str.strip()

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns in dataset: {missing_columns}")

    df = df[REQUIRED_COLUMNS].copy()

    text_columns = [
        "دسته‌بندی",
        "عنوان کتاب",
        "نویسنده / مؤلف",
        "بهترین ترجمه در ایران",
        "ناشر",
    ]

    for col in text_columns:
        df[col] = df[col].fillna("").astype(str).str.strip()

    numeric_columns = [
        "ردیف",
        "سال نشر اصلی",
        "تعداد چاپ",
        "تعداد صفحات",
        "امتیاز",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["عنوان کتاب"])

    return df


def show_dataset_report(df):
    report_lines = []

    report_lines.append("Dataset loaded successfully.")
    report_lines.append("-" * 50)
    report_lines.append(f"Number of books: {len(df)}")
    report_lines.append(f"Number of columns: {len(df.columns)}")
    report_lines.append("-" * 50)

    report_lines.append("Columns:")
    for col in df.columns:
        report_lines.append(f"- {col}")

    report_lines.append("-" * 50)
    report_lines.append("First 5 books:")
    report_lines.append(df.head(5).to_string(index=False))

    report_lines.append("-" * 50)
    report_lines.append("Number of books in each category:")
    report_lines.append(df["دسته‌بندی"].value_counts().to_string())

    report_text = "\n".join(report_lines)

    print(report_text)

    with open("dataset_report.txt", "w", encoding="utf-8-sig") as file:
        file.write(report_text)

    print("\nReport saved as dataset_report.txt")


if __name__ == "__main__":
    books_df = load_books_dataset()
    show_dataset_report(books_df)
    