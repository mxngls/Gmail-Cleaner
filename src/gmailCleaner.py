import sys
import re

from gmailMethods import GmailMethod
from collections import Counter

from tqdm import tqdm


def main():
    """Main function to run the Gmail Cleaner."""
    gmail = GmailMethod()

    while True:
        print("""
1. Show the most common senders
2. Move messages from a specific sender to trash
3. Move messages from a specific sender to the spam folder
4. Move all messages from the spam to the trash folder
5. Move messages matching a specific label to trash
6. Add a label to emails matching a specifed sender
7. Permanently delete all messages in trash
8. Exit
        """)

        try:
            user_choice = int(input("Choose an option: "))

            if user_choice == 1:
                # Show the most common senders
                if not gmail.users:
                    gmail.batch_get(gmail.list_messages("me"))

                sender_counts = Counter(gmail.users).most_common()
                num_senders = int(input("How many senders do you want to display? "))

                print("You have:")
                gmail.total_from_users = 0

                for i, (sender, count) in enumerate(sender_counts[:num_senders]):
                    # Extract email from sender string
                    email_match = re.search(r"(?<=<)(.*)(?=>)", sender)
                    display_sender = email_match.group() if email_match else sender

                    gmail.total_from_users += count
                    print(f"- {count} e-mails from {display_sender}.")

                print(
                    f"In total you have {gmail.total_messages} e-mails. "
                    f"{gmail.total_from_users} of these are from the {num_senders} users you specified."
                )

            elif user_choice == 2:
                # Move messages from sender to trash
                sender = input("Choose sender whose messages you want to delete: ")
                messages = gmail.list_messages_matching_query("me", f"from:{sender}")

                if not messages:
                    print(f"No messages found from {sender}")
                    continue

                gmail.moved_to_trash = 0
                for message in tqdm(messages, desc=f"Deleting emails from {sender}"):
                    gmail.delete_message("me", message)

                print(
                    f"Process deleting e-mails from {sender} completed. "
                    f"All {gmail.moved_to_trash} e-mails have been moved to the trash."
                )

            elif user_choice == 3:
                # Move messages from sender to spam
                sender = input(
                    "Choose sender whose messages you want to move into spam: "
                )
                messages = gmail.list_messages_matching_query("me", f"from:{sender}")

                if not messages:
                    print(f"No messages found from {sender}")
                    continue

                gmail.moved_to_spam = 0
                for message in tqdm(messages, desc="Moving emails to spam"):
                    gmail.move_to_spam("me", message)

                print(f"Moved {gmail.moved_to_spam} e-mails to the spam folder.")

            elif user_choice == 4:
                # Move all spam to trash
                messages = gmail.list_messages_matching_label("me", "SPAM")

                if not messages:
                    print("No messages found in spam")
                    continue

                gmail.moved_to_trash = 0
                for message in tqdm(messages, desc="Moving spam to trash"):
                    gmail.delete_message("me", message)

                print(
                    f"Emptied spam. All {gmail.moved_to_trash} e-mails have been moved to trash."
                )

            elif user_choice == 5:
                # Move messages with label to trash
                if input("Do you know all your label IDs? (yes/no): ").lower() in [
                    "no",
                    "n",
                ]:
                    print("You have these labels:")
                    for label in gmail.list_labels("me"):
                        print(f"Label: {label['name']}; ID: {label['id']}")

                label_id = input(
                    "Messages matching what label ID do you want to delete? "
                )
                messages = gmail.list_messages_matching_label("me", label_id)

                if not messages:
                    print(f"No messages found with label ID {label_id}")
                    continue

                gmail.moved_to_trash = 0
                for message in tqdm(messages, desc="Moving labeled messages to trash"):
                    gmail.delete_message("me", message)

                print(f"All {gmail.moved_to_trash} e-mails have been moved to trash.")

            elif user_choice == 6:
                # Add label to emails from sender
                label_name = input("What is the name of the label you want to attach? ")
                sender = input(
                    "Choose sender whose messages you want to attach this label to: "
                )

                # Check if label exists, create if not
                labels = gmail.list_labels("me")
                if not gmail.label_check(labels, label_name):
                    label_info = gmail.create_label("me", label_name)
                    label_id = label_info["id"]
                    print(f"Created new label: {label_name}")
                else:
                    # Find the label ID
                    label_id = next(
                        label["id"] for label in labels if label["name"] == label_name
                    )

                messages = gmail.list_messages_matching_query("me", f"from:{sender}")

                if not messages:
                    print(f"No messages found from {sender}")
                    continue

                gmail.labels = 0
                gmail.attach_label("me", label_id, messages)
                print(f'Attached the label: "{label_name}" to {gmail.labels} e-mails.')

            elif user_choice == 7:
                # Permanently delete all trash
                messages = gmail.list_messages_matching_label("me", "TRASH")

                if not messages:
                    print("No messages found in trash")
                    continue

                confirm = input(
                    f"Found {len(messages)} messages in trash. Permanently delete them? (yes/no): "
                )
                if confirm.lower() != "yes":
                    print("Operation cancelled")
                    continue

                gmail.deleted = 0
                for message in tqdm(messages, desc="Permanently deleting messages"):
                    gmail.delete_permanent("me", message)

                print(
                    f"Emptied trash. All {gmail.deleted} e-mails have been permanently deleted."
                )

            elif user_choice == 8:
                # Exit
                print("Exiting Gmail Cleaner. Goodbye!")
                sys.exit(0)

            else:
                print("Invalid option! Please try again.")

        except ValueError:
            print("Invalid input! Please enter a number.")

        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
