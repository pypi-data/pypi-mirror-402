# from .extractors import extract_text
# from .api import call_ai


# def clean_ai_output(text: str) -> str:
#     blacklist = [
#         "as an ai",
#         "i am sorry",
#         "cannot access",
#         "upload the file",
#         "the user is asking",
#         "i will now",
#         "limitations",
#     ]

#     lines = text.splitlines()
#     clean = [
#         line for line in lines
#         if not any(b in line.lower() for b in blacklist)
#     ]

#     return "\n".join(clean).strip()


# def handle_extract(cmd: str):
#     path = cmd.replace("extract", "", 1).strip().strip('"')
#     text, error = extract_text(path)

#     if error:
#         print(f"❌ {error}")
#         return

#     print("\n📄 Extracted Content:\n")
#     print(text[:2000])


# def handle_summarize(cmd: str):
#     path = cmd.replace("summarize", "", 1).strip().strip('"')
#     text, error = extract_text(path)

#     if error:
#         print(f"❌ {error}")
#         return

#     prompt = (
#         "Summarize the following content in 5 bullet points. "
#         "No explanations, no disclaimers.\n\n"
#         f"{text[:8000]}"
#     )

#     summary = call_ai(prompt)
#     print("\n📝 Summary:\n")
#     print(clean_ai_output(summary))


# def handle_question(question: str):
#     prompt = (
#         "Answer concisely in 2–3 lines. "
#         "No meta commentary.\n\n"
#         f"{question}"
#     )

#     ans = call_ai(prompt)
#     print("\n🤖 Answer:\n")
#     print(clean_ai_output(ans))


# def main():
#     print("AI Assistant CLI")

#     while True:
#         user_input = input("Ask something (or exit): ").strip()

#         if user_input.lower() in ("exit", "quit"):
#             break

#         if user_input.lower().startswith("extract "):
#             handle_extract(user_input)
#             continue

#         if user_input.lower().startswith("summarize "):
#             handle_summarize(user_input)
#             continue

#         handle_question(user_input)


# if __name__ == "__main__":
#     main()
from .extractors import extract_text
from .api import call_ai, set_api_key as api_set_key


def clean_ai_output(text: str) -> str:
    blacklist = [
        "as an ai",
        "i am sorry",
        "cannot access",
        "upload the file",
        "the user is asking",
        "i will now",
        "limitations",
    ]

    lines = text.splitlines()
    clean = [
        line for line in lines
        if not any(b in line.lower() for b in blacklist)
    ]

    return "\n".join(clean).strip()


def handle_extract(cmd: str):
    path = cmd.replace("extract", "", 1).strip().strip('"')
    text, error = extract_text(path)

    if error:
        print(f"❌ {error}")
        return

    print("\n📄 Extracted Content:\n")
    print(text[:2000])


def handle_summarize(cmd: str):
    path = cmd.replace("summarize", "", 1).strip().strip('"')
    text, error = extract_text(path)

    if error:
        print(f"❌ {error}")
        return

    prompt = (
        "Summarize the following content in 5 bullet points. "
        "No explanations, no disclaimers.\n\n"
        f"{text[:8000]}"
    )

    summary = call_ai(prompt)
    print("\n📝 Summary:\n")
    print(clean_ai_output(summary))


def handle_question(question: str):
    prompt = (
        "Answer concisely in 2–3 lines. "
        "No meta commentary.\n\n"
        f"{question}"
    )

    ans = call_ai(prompt)
    print("\n🤖 Answer:\n")
    print(clean_ai_output(ans))


def main():
    print("AI Assistant CLI\n")

    # Ask for API key first
    while True:
        api_key = input("Please enter your API key to start: ").strip()
        if api_key:
            api_set_key(api_key)
            print("✅ API key set successfully!\n")
            break
        else:
            print("❌ API key cannot be empty. Try again.")

    # Start the conversation
    while True:
        user_input = input("Ask something (or type 'exit' to quit): ").strip()

        if user_input.lower() in ("exit", "quit"):
            break

        if user_input.lower().startswith("extract "):
            handle_extract(user_input)
            continue

        if user_input.lower().startswith("summarize "):
            handle_summarize(user_input)
            continue

        handle_question(user_input)


if __name__ == "__main__":
    main()
