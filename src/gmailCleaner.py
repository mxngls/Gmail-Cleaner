from gmailMethods import GmailMethod
from collections import Counter
import sys
import re
from tqdm import tqdm
from pprint import pprint

def main():

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

            user_choice = int(input('Choose an option: '))

            if user_choice == 1:
                '''
                1. Show the most common senders
                '''

                if len(gmail.users) == 0:
                    gmail.batch_get(gmail.list_messages('me'))
                
                gmail.users = Counter(gmail.users).items()
                gmail.users = [user for user in sorted(gmail.users, key = lambda user: user[1], reverse=True)]
                user_choice_users = int(input('How much senders do you want to get displayed?' + '\n'))

                print('You have:')

                for i in range(0, user_choice_users):
                    match = re.search("(?<=<)(.*)(?=>)" , gmail.users[i][0]).group()
                    if match is None:
                        gmail.total_from_users += int(gmail.users[i][1])
                        print(f'- {gmail.users[i][1]} e-mails from {gmail.users[i][0]}.')
                    else:
                        gmail.total_from_users += int(gmail.users[i][1])
                        print(f'- {gmail.users[i][1]} e-mails from {match}.')

                print(f'In total you have {gmail.total_messages} e-mails. {gmail.total_from_users} of these are from the {user_choice_users} users you specified.')

            elif user_choice == 2:	
                '''
                2. Move messages from a specific sender to trash
                '''
                user_choice_sender = str(input('Choose sender whose messages you want to delete.' + '\n'))

                for message in tqdm(gmail.list_messages_matching_query('me', 'from:' + user_choice_sender)):
                    gmail.delete_message('me', message)
                    gmail.moved_to_trash += 1
                print(f'Process deleting e-mails from {user_choice_sender} completed. All {gmail.moved_to_trash} e-mails have been moved to the trash.')
                gmail.moved_to_trash = 0

            elif user_choice == 3:
                '''
                3. Move messages from a specific sender to the spam folder
                '''
                user_choice_sender = str(input('Choose sender whose messages you want to move into spam.' + '\n'))

                for message in tqdm((gmail.list_messages_matching_query('me', 'from:' + user_choice_sender))):
                    gmail.move_to_spam('me', message)
                    gmail.moved_to_spam += 1
                print(f'Moved {gmail.moved_to_spam} e-mails to the spam folder.')
                gmail.moved_to_spam = 0

            elif user_choice == 4:
                '''
                4. Move messages matching from spam to trash
                '''
                for message in tqdm(gmail.list_messages_matching_label('me', 'SPAM')):	
                    gmail.delete_message('me', message)
                    gmail.moved_to_trash += 1
                print(f'Emptied spam. All {gmail.moved_to_trash} e-mails have been moved to trash.')
                gmail.moved_to_trash = 0

            elif user_choice == 5:	
                '''
                5. Move messages matching a specific label to trash
                '''
                if input("Do you know all your label-id's?" + '\n') == 'No' or 'no':
                    print('You got these labels:' + '\n')
                    for label in gmail.list_labels('me'):
                        print(f"Label: {label['name']}; Id: {label['id']}")
                user_choice_label = str(input('Messages matchig what label-id do you want to delete?' + '\n'))				

                for message in tqdm(gmail.list_messages_matching_label('me', user_choice_label)):	
                    gmail.delete_message('me', message)
                    gmail.moved_to_trash += 1
                print(f'Emptied spam. All {gmail.moved_to_trash} e-mails have been moved to trash.')
                gmail.moved_to_trash = 0

            elif user_choice == 6:
                '''
                6. Add a label to emails matching a specifed sender
                '''
                user_choice_label = str(input('What is the name of the label you want to attach?' + '\n'))				
                user_choice_sender = str(input('Choose sender whose messages you want to attach this label to:' + '\n'))

                if gmail.label_check(gmail.list_labels('me'), user_choice_label) is False:
                    label = gmail.create_label('me', user_choice_label)['id']
                else:
                    for el in gmail.list_labels('me'):
                        if el['name'] == user_choice_label:
                            label = el.get('id')

                messages = (gmail.list_messages_matching_query('me', 'from:' + user_choice_sender))
                gmail.attach_label('me', label, messages)
                gmail.labels = len(messages)
                print(f'Attached the label: "{user_choice_label}" to {gmail.labels} e-mails.')
                gmail.labels = 0

            elif user_choice == 7:
                '''
                7. Permanently delete all messages in trash
                '''
                for message in tqdm(gmail.list_messages_matching_label('me', 'TRASH')):
                    gmail.delete_permanent('me', message)
                    gmail.deleted += 1
                print(f'Emptied trash. All {gmail.deleted} e-mails have been deleted.')
                gmail.deleted = 0

            elif user_choice == 8:
                '''
                8. Exit
                '''
                sys.exit(1)

        except ValueError:
            print('Invalid input! Try again')

if __name__ == '__main__':
    main()




