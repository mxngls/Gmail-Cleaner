from typing import Any, Dict, List, Optional

from gmailClient import GmailClient

from tqdm import tqdm


class GmailMethod:
    """Provides methods for interacting with Gmail."""

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

    def list_messages(self, user_id: str) -> List[str]:
        """
        Lists all the messages in the user's mailbox.

        Args:
            user_id: The user's email address. Special value 'me' indicates the authenticated user.

        Returns:
            A list of message IDs
        """
        try:
            messages = []

            response = (
                self.gmailclient.service.users()
                .messages()
                .list(userId=user_id)
                .execute()
            )

            if "messages" in response:
                messages.extend(message["id"] for message in response["messages"])
                self.total_messages += len(response["messages"])

                # Process remaining pages
                while "nextPageToken" in response:
                    page_token = response["nextPageToken"]
                    response = (
                        self.gmailclient.service.users()
                        .messages()
                        .list(userId=user_id, pageToken=page_token)
                        .execute()
                    )

                    if "messages" in response:
                        messages.extend(
                            message["id"] for message in response["messages"]
                        )
                        self.total_messages += len(response["messages"])

            return messages

        except Exception as error:
            print(f"An error occurred at list_messages: {error}")
            return []

    def callback_add_to_messages(self, request_id, response, exception):
        """
        Callback function for batch requests that extracts sender information.

        Args:
            request_id: Unique ID of the request
            response: The returned Gmail message object
            exception: Exception object if an error occurred
        """
        if exception:
            print(f"An error occurred during batch processing: {exception}")
            return

        try:
            for element in response["payload"]["headers"]:
                if element["name"] == "From":
                    self.users.append(element.get("value"))
        except Exception as error:
            print(f"An error occurred at callback_add_to_messages: {error}")

    def batch_get(self, messages: List[str]):
        """
        Process messages in batches to extract sender information.

        Args:
            messages: List of message IDs to process
        """
        try:
            # Process in batches of 100
            for start_idx in tqdm(
                range(0, len(messages), 100), desc="Processing messages"
            ):
                batch = self.gmailclient.service.new_batch_http_request()
                end_idx = min(start_idx + 100, len(messages))

                for msg_id in messages[start_idx:end_idx]:
                    batch.add(
                        self.gmailclient.service.users()
                        .messages()
                        .get(userId="me", id=msg_id, fields="payload/headers"),
                        callback=self.callback_add_to_messages,
                    )

                batch.execute()

        except Exception as error:
            print(f"An error occurred at batch_get: {error}")

    def get_user(self, user_id: str, msg_id: str) -> Optional[str]:
        """
        Get the sender of a specific message.

        Args:
            user_id: The user's email address
            msg_id: The message ID

        Returns:
            The email address of the sender, or None if not found
        """
        try:
            response = (
                self.gmailclient.service.users()
                .messages()
                .get(userId=user_id, id=msg_id, fields="payload/headers")
                .execute()
            )

            for element in response["payload"]["headers"]:
                if element["name"] == "From":
                    return element.get("value")

            return None
        except Exception as error:
            print(f"An error occurred at get_user: {error}")
            return None

    def list_messages_matching_query(self, user_id: str, query: str = "") -> List[str]:
        """
        List message IDs matching a specific query.

        Args:
            user_id: The user's email address
            query: The search query (e.g., 'from:example@gmail.com')

        Returns:
            A list of message IDs
        """
        try:
            messages = []

            response = (
                self.gmailclient.service.users()
                .messages()
                .list(userId=user_id, q=query)
                .execute()
            )

            if "messages" in response:
                messages.extend(message["id"] for message in response["messages"])

                # Process remaining pages
                while "nextPageToken" in response:
                    page_token = response["nextPageToken"]
                    response = (
                        self.gmailclient.service.users()
                        .messages()
                        .list(userId=user_id, q=query, pageToken=page_token)
                        .execute()
                    )

                    if "messages" in response:
                        messages.extend(
                            message["id"] for message in response["messages"]
                        )

            return messages

        except Exception as error:
            print(f"An error occurred at list_messages_matching_query: {error}")
            return []

    def list_messages_matching_label(self, user_id: str, label_id: str) -> List[str]:
        """
        List message IDs with a specific label.

        Args:
            user_id: The user's email address
            label_id: The label ID

        Returns:
            A list of message IDs
        """
        try:
            messages = []

            response = (
                self.gmailclient.service.users()
                .messages()
                .list(userId=user_id, labelIds=label_id)
                .execute()
            )

            if "messages" in response:
                messages.extend(message["id"] for message in response["messages"])

                # Process remaining pages
                while "nextPageToken" in response:
                    page_token = response["nextPageToken"]
                    response = (
                        self.gmailclient.service.users()
                        .messages()
                        .list(userId=user_id, labelIds=label_id, pageToken=page_token)
                        .execute()
                    )

                    if "messages" in response:
                        messages.extend(
                            message["id"] for message in response["messages"]
                        )

            return messages

        except Exception as error:
            print(f"An error occurred at list_messages_matching_label: {error}")
            return []

    def delete_message(self, user_id: str, msg_id: str) -> None:
        """
        Move a message to trash.

        Args:
            user_id: The user's email address
            msg_id: The message ID
        """
        try:
            self.gmailclient.service.users().messages().trash(
                userId=user_id, id=msg_id
            ).execute()
            self.moved_to_trash += 1
        except Exception as error:
            print(f"An error occurred at delete_message: {error}")

    def move_to_spam(self, user_id: str, msg_id: str) -> None:
        """
        Move a message to spam.

        Args:
            user_id: The user's email address
            msg_id: The message ID
        """
        try:
            self.gmailclient.service.users().messages().batchModify(
                userId=user_id, body={"addLabelIds": ["SPAM"], "ids": [msg_id]}
            ).execute()
            self.moved_to_spam += 1
        except Exception as error:
            print(f"An error occurred at move_to_spam: {error}")

    def list_labels(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all available labels.

        Args:
            user_id: The user's email address

        Returns:
            A list of label objects
        """
        try:
            response = (
                self.gmailclient.service.users().labels().list(userId=user_id).execute()
            )
            return response.get("labels", [])
        except Exception as error:
            print(f"An error occurred at list_labels: {error}")
            return []

    def create_label(self, user_id: str, label_name: str) -> Dict[str, Any]:
        """
        Create a new label.

        Args:
            user_id: The user's email address
            label_name: The name for the new label

        Returns:
            The created label object
        """
        try:
            response = (
                self.gmailclient.service.users()
                .labels()
                .create(
                    userId=user_id,
                    body={
                        "name": label_name,
                        "messageListVisibility": "SHOW",
                        "labelListVisibility": "LABEL_SHOW",
                        "type": "USER",
                    },
                )
                .execute()
            )
            return response
        except Exception as error:
            print(f"An error occurred at create_label: {error}")
            return {}

    def label_check(self, labels: List[Dict[str, Any]], label_name: str) -> bool:
        """
        Check if a label exists.

        Args:
            labels: List of label objects
            label_name: The label name to check

        Returns:
            True if the label exists, False otherwise
        """
        return any(label["name"] == label_name for label in labels)

    def attach_label(self, user_id: str, label_id: str, message_ids: List[str]) -> None:
        """
        Attach a label to messages.

        Args:
            user_id: The user's email address
            label_id: The label ID
            message_ids: List of message IDs
        """
        try:
            self.gmailclient.service.users().messages().batchModify(
                userId=user_id, body={"addLabelIds": [label_id], "ids": message_ids}
            ).execute()

            self.labels += len(message_ids)
        except Exception as error:
            print(f"An error occurred at attach_label: {error}")
