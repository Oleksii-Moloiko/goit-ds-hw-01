
from collections import UserDict
from datetime import datetime, date, timedelta
from typing import Callable
import pickle

FILENAME = "addressbook.pkl"

def save_data(book, filename=FILENAME):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename=FILENAME):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


# ---------- FIELDS ----------
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        value = str(value)
        if not (value.isdigit() and len(value) == 10):
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        # value має бути рядок формату DD.MM.YYYY
        try:
            datetime.strptime(value, "%d.%m.%Y")  # тільки перевірка формату/коректності
            self.value = value
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


# ---------- RECORD ----------
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None  # Birthday або None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        phone = str(phone)
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return
        raise ValueError("Phone not found.")

    def edit_phone(self, old_phone, new_phone):
        old_phone = str(old_phone)
        for i, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[i] = Phone(new_phone)
                return
        raise ValueError("Old phone not found.")

    def find_phone(self, phone):
        phone = str(phone)
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday_str: str):
        self.birthday = Birthday(birthday_str)

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones) if self.phones else "No phones"
        bday = self.birthday.value if self.birthday else "No birthday"
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {bday}"


# ---------- ADDRESS BOOK ----------
class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name: str):
        return self.data.get(name)

    def delete(self, name: str):
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError("Contact not found.")

    def get_upcoming_birthdays(self, days: int = 7):
        """
        Повертає список словників:
        [{"name": "...", "birthday": "DD.MM.YYYY"}, ...]
        де birthday = дата привітання (з переносом з вихідних на понеділок)
        """
        upcoming = []
        today = date.today()

        for record in self.data.values():
            if record.birthday is None:
                continue

            # Birthday.value — рядок DD.MM.YYYY -> date
            bday_date = datetime.strptime(record.birthday.value, "%d.%m.%Y").date()
            bday_this_year = bday_date.replace(year=today.year)

            # якщо вже минув ДН цього року — беремо наступний рік
            if bday_this_year < today:
                bday_this_year = bday_this_year.replace(year=today.year + 1)

            delta_days = (bday_this_year - today).days

            # вперед на 7 днів включно з сьогодні
            if 0 <= delta_days <= days:
                congrat_date = bday_this_year

                # перенос якщо вихідний
                if congrat_date.weekday() == 5:       # Saturday
                    congrat_date += timedelta(days=2)
                elif congrat_date.weekday() == 6:     # Sunday
                    congrat_date += timedelta(days=1)

                upcoming.append({
                    "name": record.name.value,
                    "birthday": congrat_date.strftime("%d.%m.%Y")
                })

        return upcoming


# ---------- DECORATOR ----------
def input_error(func: Callable):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IndexError:
            return "Not enough arguments."
        except KeyError as e:
            return str(e) if str(e) else "Contact not found."
        except ValueError as e:
            return str(e)
    return inner


# ---------- COMMAND HANDLERS ----------
def parse_input(user_input: str):
    parts = user_input.split()
    cmd = parts[0].lower() if parts else ""
    args = parts[1:]
    return cmd, args


@input_error
def add_contact(args, book: AddressBook):
    name, phone = args[0], args[1]
    record = book.find(name)

    if record is None:
        record = Record(name)
        book.add_record(record)
        record.add_phone(phone)
        return "Contact added."
    else:
        record.add_phone(phone)
        return "Contact updated."


@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone = args[0], args[1], args[2]
    record = book.find(name)
    if record is None:
        raise KeyError("Contact not found.")
    record.edit_phone(old_phone, new_phone)
    return "Phone changed."


@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError("Contact not found.")
    if not record.phones:
        return "No phones for this contact."
    return "; ".join(p.value for p in record.phones)


@input_error
def show_all(book: AddressBook):
    if not book.data:
        return "AddressBook is empty."
    return "\n".join(str(record) for record in book.data.values())



@input_error
def add_birthday(args, book: AddressBook):
    name, birthday_str = args[0], args[1]
    record = book.find(name)
    if record is None:
        raise KeyError("Contact not found.")
    record.add_birthday(birthday_str)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError("Contact not found.")
    if record.birthday is None:
        return "Birthday is not set."
    return record.birthday.value


@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next 7 days."

    lines = []
    for item in upcoming:
        lines.append(f"{item['name']}: {item['birthday']}")
    return "\n".join(lines)


# ---------- MAIN ----------
def main():
    book = load_data()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ").strip()
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
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