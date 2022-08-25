from gmailClient import GmailClient
from tqdm import tqdm
import sys


class GmailMethod:
	def __init__(self):
		self.gmailclient = GmailClient()
		self.users = []	
		self.users_query = []
		self.total_from_users = 0
		self.messages = []
		self.total_messages = 0
		self.moved_to_trash = 0
		self.moved_to_spam = 0
		self.deleted = 0
		self.labels = 0

	def list_messages(self, user_id):
		'''
		Lists all the messages in the user's mailbox.

		Args:
			userId: string, The user's email address. The special value
			`me` can be used to indicate the authenticated user. (required)

		Returns:
  			A list with gmail message objects
		'''
		try:
			messages = []

			response = self.gmailclient.service.users().messages().list(userId="me").execute()
			if 'messages' in response:
				for message in response['messages']:
					self.total_messages += 1
					messages.append(message['id'])

				while 'nextPageToken' in response:
					page_token = response['nextPageToken']
					response = self.gmailclient.service.users().messages().list(
						userId="me", pageToken=page_token).execute()
					for message in response['messages']:
						self.total_messages += 1
						messages.append(message['id'])

			return messages

		except Exception as error:
			print(f'An error occurred at list_messages: {error}')

	def callback_add_to_messages(self, request_id, response, exception):
		'''
		Adds the sender of the returned gmail message object of the get method to the list of messages

		Args:
			response: The returned gmail message object.
			request_id: The unique id of the request. and the second is the deserialized response object.
			exception: An apiclient.errors.HttpError exception object if an HTTP
            error occurred while processing the request, or None if no error occurred.
		'''
		try:
			for element in response['payload']['headers']:
				if element['name'] == 'From':
					self.users.append(element.get('value'))

		except Exception as error:
			print(f'An error occurred at callback_add_to_messages: {error}')

	def batch_get(self, messages):
		'''
		Batches single GET requests into one and calls a specified callback function for each.

			Args:
			response: The returned gmail message object.
			request_id: The unique id of the request. and the second is the deserialized response object.
			exception: An apiclient.errors.HttpError exception object if an HTTP
            error occurred while processing the request, or None if no error occurred.
		'''
		try:
			for n in tqdm(range(0, len(messages), 100), file=sys.stderr):

				batch = self.gmailclient.service.new_batch_http_request()
				batch_size = 100

				if len(messages) < batch_size:
					batch_size = len(messages) - 1

				for x in (range(0, batch_size)):
					if x > len(messages):
						break
					batch.add(self.gmailclient.service.users().messages().get(
					    userId="me", id=messages[x], fields='payload/headers'), callback=self.callback_add_to_messages)
				
				messages = messages[99:len(messages)-1]

				batch.execute()
				
		except Exception as error:
			print(f'An error occurred at batch_get: {error}')

	def get_user(self, user_id, msg_id):
		'''
		!NOT IN USE!
		Gets the specified message.

		Args:
			userId: string, The user's email address. The special value
			`me` can be used to indicate the authenticated user. (required)
			id: string, The ID of the message to retrieve.
			fields: string, Specify the fields of the nested response to request. (required)

		Returns:
  			The sender of the response
		'''
		try:
			response = self.gmailclient.service.users().messages().get(
			    userId="me", id=msg_id, fields='payload/headers').execute()
			for element in response['payload']['headers']:
				if element['name'] == "From":
					return element.get("value")

		except Exception as error:
			print(f'An error occurred at get_user: {error}')

	def list_messages_matching_query(self, user_id, query=''):
		'''
		Lists all the messages in the user's mailbox matching the specifed query.

		Args:
			userId: string, The user's email address. The special value
			`me` can be used to indicate the authenticated user. (required)
			query: string, return messages matching the specified query. (required)

		Returns:
  			A list with gmail message objects
		'''
		try:
			messages = []

			response = self.gmailclient.service.users().messages().list(
			    userId="me", q=query).execute()
			if 'messages' in response:
				for message in response['messages']:
					messages.append(message['id'])

			while 'nextPageToken' in response:
				page_token = response['nextPageToken']
				response = self.gmailclient.service.users().messages().list(
				    userId="me", q=query, pageToken=page_token).execute()
				for message in response['messages']:
					messages.append(message['id'])

			return messages

		except Exception as error:
			print(f'An error occurred at list_messages_matching_query: {error}')

	def list_messages_matching_label(self, user_id, label_Id):
		'''
		Lists all the messages in the user's mailbox matching the specifed label

		Args:
			userId: string, The user's email address. The special value
			`me` can be used to indicate the authenticated user. (required)
			query: string, return messages matching the specified query. (required)

		Returns:
  			A list with gmail message objects
		'''
		try:

			messages = []

			response = self.gmailclient.service.users().messages().list(
			    userId="me", labelIds=label_Id).execute()
			if 'messages' in response:
				for message in response['messages']:
					messages.append(message['id'])

			while 'nextPageToken' in response:
				page_token = response['nextPageToken']
				response = self.google_client.service.users().messages().list(
				    userId="me", labelIds=label_Id, pageToken=page_token).execute()
				if 'messages' in response:
					for message in response['messages']:
						messages.append(message['id'])

			return messages

		except Exception as error:
			print(f'An error occurred at list_messages_matching_label: {error}')

	def delete_message(self, user_id, msg_id):
		'''
		Moves the specified message to the trash.
		Args:
			userId: string, The user's email address. The special value
			`me` can be used to indicate the authenticated user. (required)
			msg_id: string, The ID of the message to delete. (required)
		'''
		try:
			response = self.gmailclient.service.users().messages().trash(userId="me", id=msg_id).execute()

		except Exception as error:
			print(f'An error occurred at delete_message: {error}')

	def delete_permanent(self, user_id, msg_id):
		'''
		Immediately and permanently deletes the specified message. This operation cannot be undone.		
		Args:
			userId: string, The user's email address. The special value 
			`me` can be used to indicate the authenticated user. (required)
			msg_id: string, The ID of the message to delete. (required)
		'''
		try:
			response = self.gmailclient.service.users().messages().delete(userId="me", id=msg_id).execute()
			return response

		except Exception as error:
			print(f'An error occurred at delete_permanent: {error}')

	def create_label(self, user_id, label_name):
		'''
		Creates a new label.
		Args:
			userId: string, The user's email address. The special value 
			`me` can be used to indicate the authenticated user. (required)
			body: object, The request body. (required)
		Returns: An object whose body contains an instance of label.
		'''
		try:
			response = self.gmailclient.service.users().labels().create(body={
				"name": label_name,
				"messageListVisibility": "SHOW",
				"labelListVisibility": "LABEL_SHOW",
				"type": "USER"
				}, userId="me").execute()
			return response

		except Exception as error:
			print(f'An error occurred at create_label: {error}')

	def move_to_spam(self, user_id, message_ids):
		'''
		Adds the specfied message to spam.
		Args:
			userId: string, The user's email address. The special value 
			`me` can be used to indicate the authenticated user. (required)
			message_ids: list, A list of message(-id's) which should be marked as spam. (required)
		'''
		try:
			response = self.gmailclient.service.users().messages().batchModify(
				userId = 'me',
				body = {'addLabelIds': ['SPAM'],
						'ids': [message_ids]}).execute()

			return response

		except Exception as error:
			print(f'An error occurred at move_to_spam: {error}')

	def list_labels(self, user_id):
		'''
		Create a list with all the users labels.
		Args:
			userId: string, The user's email address. The special value 
			`me` can be used to indicate the authenticated user. (required)
		'''
		try:
			response = self.gmailclient.service.users().labels().list(userId="me").execute()
			labels = response.get('labels', [])
			return labels

		except Exception as error:
			print(f'An error occurred at list_labels: {error}')

	def label_check(self, labels, label_name):
		'''
		Check if the given label exists.
		Args:
			labels: list. A list of all the users labels. (required)
			label_name: string. The name of the label whose existence is to be checked. (required)

		Returns:
			boolean.
		'''
		try:
			for label in labels:
				if label['name'] == label_name:
					return True

		except Exception as error:
			print(f'An error occurred at label_check: {error}')

	def attach_label(self, user_id, label_Id, message_ids):
		'''
		Attach a label to a message.
		Args:
			userId: string, The user's email address. The special value 
			`me` can be used to indicate the authenticated user. (required)
			label_name: string. The name of the label that is to be attached.
			message_ids: list. A list of message id's.
		'''
		try:
			response = self.gmailclient.service.users().messages().batchModify(
				userId = 'me',
				body = {'addLabelIds': [label_Id],
						'ids': [message_ids]}).execute()

		except Exception as error:
			print(f'An error occurred at attach_label: {error}')




