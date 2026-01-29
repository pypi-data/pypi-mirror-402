import random

def main():
    print("😊 Welcome to HappyCLI! 😊")

    while True:
        print("\nPick one:")
        print("1) Guessing Game")
        print("2) Joke")
        print("3) Fun Fact")
        print("4) Exit")

        choice = input("> ")

        if choice == "1":
            secret = random.randint(1, 5)
            guess = input("Guess a number 1–5: ")
            if guess.isdigit() and int(guess) == secret:
                print("🎉 Correct!")
            else:
                print("Nope! It was", secret)

        elif choice == "2":
            jokes = [
                "Why did the computer go to bed? It was tired!",
                "Why did the banana go to school? To get smarter!",
                "Why did the math book cry? Too many problems!"
            ]
            print(random.choice(jokes))

        elif choice == "3":
            facts = [
                "Dolphins have names for each other!",
                "Octopuses have three hearts!",
                "Bananas are berries!"
            ]
            print(random.choice(facts))

        elif choice == "4":
            print("Bye! 👋")
            break
        else:
            print("Pick 1, 2, 3, or 4!")
