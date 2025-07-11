from collections import UserDict
from datetime import datetime, timedelta
import pickle
import os

# ------------------ КЛАСИ ПОЛІВ ------------------

# Базовий клас для всіх полів (імені, телефону, дня народження)
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

# Клас для зберігання імені контакту
class Name(Field):
    pass

# Клас для зберігання телефонного номера з валідацією
class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain exactly 10 digits")
        super().__init__(value)

# Клас для зберігання дати народження з перевіркою формату
class Birthday(Field):
    def __init__(self, value):
        try:
            date = datetime.strptime(value, "%d.%m.%Y").date()
            super().__init__(date)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

# ------------------ КЛАС ЗАПИСУ ------------------

# Клас для представлення одного запису контакту
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        self.phones = [p for p in self.phones if p.value != phone]

    def edit_phone(self, old_phone, new_phone):
        for i, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[i] = Phone(new_phone)
                return
        raise ValueError("Old phone not found")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        raise ValueError("Phone not found")

    def add_birthday(self, bday):
        self.birthday = Birthday(bday)

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones)
        bday = f", birthday: {self.birthday.value.strftime('%d.%m.%Y')}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones}{bday}"

# ------------------ КЛАС АДРЕСНОЇ КНИГИ ------------------

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    # Отримання списку днів народження, що припадають на наступний тиждень
    def get_upcoming_birthdays(self):
        upcoming = []
        today = datetime.today().date()
        next_week = today + timedelta(days=7)

        for record in self.data.values():
            if record.birthday:
                bday = record.birthday.value
                bday_this_year = bday.replace(year=today.year)
                if bday_this_year < today:
                    bday_this_year = bday.replace(year=today.year + 1)
                if today <= bday_this_year <= next_week:
                    upcoming.append(f"{record.name.value}: {bday_this_year.strftime('%d.%m.%Y')}")
        return upcoming

# ------------------ ДЕКОРАТОР ДЛЯ ОБРОБКИ ПОМИЛОК ------------------

def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Contact not found."
        except ValueError:
            return "Give me valid name, phone or date, please."
        except IndexError:
            return "Not enough arguments."
    return wrapper

# ------------------ ФУНКЦІЇ-КОМАНДИ ------------------

@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return "Phone number updated."
    return "Contact not found."

@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record:
        return ", ".join(p.value for p in record.phones)
    return "Contact not found."

def show_all(book: AddressBook):
    if not book.data:
        return "No contacts found."
    return '\n'.join(str(record) for record in book.data.values())

@input_error
def add_birthday(args, book: AddressBook):
    name, bday = args
    record = book.find(name)
    if not record:
        record = Record(name)
        book.add_record(record)
    record.add_birthday(bday)
    return f"Birthday added for {name}."

@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday is on {record.birthday.value.strftime('%d.%m.%Y')}"
    return "Birthday not found."

@input_error
def birthdays(args, book: AddressBook):
    return '\n'.join(book.get_upcoming_birthdays()) or "No upcoming birthdays."

# ------------------ ЗБЕРЕЖЕННЯ/ЗАВАНТАЖЕННЯ ------------------

# Зберігання адресної книги у файл
def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

# Завантаження адресної книги з файлу або створення нової, якщо файл не знайдено
def load_data(filename="addressbook.pkl"):
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            return pickle.load(f)
    return AddressBook()

# ------------------ ПАРСЕР КОМАНД ------------------

# Розділяє введену команду на ключове слово та аргументи
def parse_input(user_input):
    parts = user_input.strip().split()
    if not parts:
        return "", []
    command = parts[0].lower()
    args = parts[1:]
    return command, args

# ------------------ ГОЛОВНА ФУНКЦІЯ ------------------

# Основний цикл бота
def main():
    book = load_data()  # Завантаження збереженої адресної книги
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)  # Збереження адресної книги перед виходом
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(show_all(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()

