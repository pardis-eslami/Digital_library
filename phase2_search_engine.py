import random
import re
from pathlib import Path

import pandas as pd


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


def normalize_text(text):
    """
    This function makes Persian/Arabic text easier to search.
    Example:
    ك -> ک
    ي -> ی
    extra spaces -> single space
    """
    if pd.isna(text):
        return ""

    text = str(text)

    replacements = {
        "ي": "ی",
        "ك": "ک",
        "ۀ": "ه",
        "ة": "ه",
        "ؤ": "و",
        "إ": "ا",
        "أ": "ا",
        "آ": "ا",
        "\u200c": " ",  # zero width non-joiner
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"

    for p_digit, e_digit in zip(persian_digits, english_digits):
        text = text.replace(p_digit, e_digit)

    text = text.casefold()
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


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

    df = df[df["عنوان کتاب"].str.strip() != ""]

    # Helper columns for better searching
    df["_search_title"] = df["عنوان کتاب"].apply(normalize_text)
    df["_search_author"] = df["نویسنده / مؤلف"].apply(normalize_text)
    df["_search_category"] = df["دسته‌بندی"].apply(normalize_text)
    df["_search_translator"] = df["بهترین ترجمه در ایران"].apply(normalize_text)
    df["_search_publisher"] = df["ناشر"].apply(normalize_text)

    return df


def safe_value(value):
    if pd.isna(value) or str(value).strip() == "":
        return "نامشخص"

    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value)

    return str(value)


def format_book(book):
    return (
        f"📚 عنوان کتاب: {safe_value(book['عنوان کتاب'])}\n"
        f"✍️ نویسنده / مؤلف: {safe_value(book['نویسنده / مؤلف'])}\n"
        f"🏷 دسته‌بندی: {safe_value(book['دسته‌بندی'])}\n"
        f"🌐 بهترین ترجمه در ایران: {safe_value(book['بهترین ترجمه در ایران'])}\n"
        f"🏢 ناشر: {safe_value(book['ناشر'])}\n"
        f"📅 سال نشر اصلی: {safe_value(book['سال نشر اصلی'])}\n"
        f"🖨 تعداد چاپ: {safe_value(book['تعداد چاپ'])}\n"
        f"📄 تعداد صفحات: {safe_value(book['تعداد صفحات'])}\n"
        f"⭐ امتیاز: {safe_value(book['امتیاز'])}"
    )


def format_books_list(results, title="نتایج جست‌وجو"):
    if results.empty:
        return "❌ هیچ کتابی پیدا نشد."

    message_parts = [f"{title}\n"]

    for index, (_, book) in enumerate(results.iterrows(), start=1):
        message_parts.append(f"نتیجه {index}:")
        message_parts.append(format_book(book))
        message_parts.append("-" * 30)

    return "\n".join(message_parts)


def search_books(df, query, search_column, limit=5):
    query = normalize_text(query)

    if not query:
        return pd.DataFrame()

    results = df[df[search_column].str.contains(query, na=False, regex=False)]

    return results.head(limit)


def get_best_rated_rows(results):
    """
    Used for title search.

    If several publishers/editions of the same title exist,
    this function keeps only the ones with the highest rating.

    If two or more editions have the same highest rating,
    all of them will be returned.
    """
    if results.empty:
        return results

    max_rating = results["امتیاز"].max()

    if pd.isna(max_rating):
        return results.head(1)

    best_results = results[results["امتیاز"] == max_rating].copy()

    best_results = best_results.sort_values(
        by=["عنوان کتاب", "ناشر"],
        ascending=[True, True],
        na_position="last",
    )

    return best_results


def keep_best_edition_per_title(results, limit=5):
    """
    Used for author search.

    If one book title has several publishers/editions,
    this function keeps only one edition:
    the one with the highest rating.
    """
    if results.empty:
        return results

    sorted_results = results.sort_values(
        by=["_search_title", "امتیاز", "تعداد چاپ", "ناشر"],
        ascending=[True, False, False, True],
        na_position="last",
    )

    best_per_title = sorted_results.drop_duplicates(
        subset=["_search_title"],
        keep="first",
    )

    best_per_title = best_per_title.sort_values(
        by=["امتیاز", "عنوان کتاب"],
        ascending=[False, True],
        na_position="last",
    )

    return best_per_title.head(limit)


def keep_best_editions_for_each_title_with_ties(results, limit=5):
    """
    Used for partial title search.

    Example:
    If the user searches a general word and several titles match,
    we keep the best-rated edition of each title.
    But if a title has several editions with the same highest rating,
    all tied editions are shown.
    """
    if results.empty:
        return results

    selected_groups = []
    selected_title_count = 0

    sorted_results = results.sort_values(
        by=["امتیاز", "عنوان کتاب", "ناشر"],
        ascending=[False, True, True],
        na_position="last",
    )

    seen_titles = []

    for title in sorted_results["_search_title"]:
        if title not in seen_titles:
            seen_titles.append(title)

    for title in seen_titles:
        if selected_title_count >= limit:
            break

        title_group = results[results["_search_title"] == title].copy()
        best_rows = get_best_rated_rows(title_group)

        if not best_rows.empty:
            selected_groups.append(best_rows)
            selected_title_count += 1

    if not selected_groups:
        return pd.DataFrame(columns=results.columns)

    final_results = pd.concat(selected_groups)

    final_results = final_results.sort_values(
        by=["امتیاز", "عنوان کتاب", "ناشر"],
        ascending=[False, True, True],
        na_position="last",
    )

    return final_results


def search_by_title(df, query, limit=5):
    query_normalized = normalize_text(query)

    if not query_normalized:
        return pd.DataFrame()

    # First, try exact title match.
    exact_results = df[df["_search_title"] == query_normalized].copy()

    if not exact_results.empty:
        return get_best_rated_rows(exact_results)

    # If exact title is not found, use contains search.
    partial_results = df[
        df["_search_title"].str.contains(
            query_normalized,
            na=False,
            regex=False,
        )
    ].copy()

    if partial_results.empty:
        return partial_results

    return keep_best_editions_for_each_title_with_ties(
        partial_results,
        limit=limit,
    )


def search_by_author(df, query, limit=5):
    query_normalized = normalize_text(query)

    if not query_normalized:
        return pd.DataFrame()

    results = df[
        df["_search_author"].str.contains(
            query_normalized,
            na=False,
            regex=False,
        )
    ].copy()

    if results.empty:
        return results

    return keep_best_edition_per_title(results, limit=limit)


def search_by_category(df, query, limit=5):
    return search_books(df, query, "_search_category", limit)


def search_by_translator(df, query, limit=5):
    return search_books(df, query, "_search_translator", limit)


def search_by_publisher(df, query, limit=5):
    return search_books(df, query, "_search_publisher", limit)


def get_top_books(df, limit=5):
    results = df.dropna(subset=["امتیاز"]).sort_values(
        by="امتیاز",
        ascending=False,
    )

    return results.head(limit)


def get_random_book(df):
    random_index = random.randint(0, len(df) - 1)
    return df.iloc[random_index]


def show_test_menu():
    print("Book Search Engine Test")
    print("-" * 40)
    print("1. Search by title")
    print("2. Search by author")
    print("3. Search by category")
    print("4. Search by translator")
    print("5. Show top books")
    print("6. Random book")
    print("0. Exit")
    print("-" * 40)


def run_test_program():
    df = load_books_dataset()

    print("Dataset loaded successfully.")
    print(f"Number of books: {len(df)}")

    while True:
        show_test_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            query = input("Enter book title: ")
            results = search_by_title(df, query)
            print(format_books_list(results, "🔍 نتایج جست‌وجو بر اساس عنوان"))

        elif choice == "2":
            query = input("Enter author name: ")
            results = search_by_author(df, query)
            print(format_books_list(results, "✍️ نتایج جست‌وجو بر اساس نویسنده / مؤلف"))

        elif choice == "3":
            query = input("Enter category: ")
            results = search_by_category(df, query)
            print(format_books_list(results, "🏷 نتایج جست‌وجو بر اساس دسته‌بندی"))

        elif choice == "4":
            query = input("Enter translator name: ")
            results = search_by_translator(df, query)
            print(format_books_list(results, "🌐 نتایج جست‌وجو بر اساس مترجم"))

        elif choice == "5":
            results = get_top_books(df)
            print(format_books_list(results, "⭐ کتاب‌های برتر بر اساس امتیاز"))

        elif choice == "6":
            book = get_random_book(df)
            print("🎲 پیشنهاد تصادفی کتاب:\n")
            print(format_book(book))

        elif choice == "0":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Please try again.")

        print("\n")


if __name__ == "__main__":
    run_test_program()