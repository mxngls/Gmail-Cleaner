import random
import time
from typing import Any, Dict, List, Optional, Tuple

from googleapiclient.errors import HttpError
from tqdm import tqdm

from client import GmailClient

# fmt: off
# https://developers.google.com/gmail/api/reference/quota#per-method_quota_usage
TRASH_BATCH_SIZE = 20   # messages.trash is 5 units
LIST_BATCH_SIZE = 20    # messages.list is 5 units
MODIFY_BATCH_SIZE = 20  # messages.modify is 5 units
DELETE_BATCH_SIZE = 10  # messages.delete is 10 units
SPAM_BATCH_SIZE = 20    # uses batchModify which is 5 units
LABEL_BATCH_SIZE = 20   # uses batchModify which is 5 units
GET_BATCH_SIZE = 20     # messages.get is 5 units
# fmt: on


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

    def list_messages(
        self,
        user_id: str,
        query: Optional[str] = None,
        only_newer_than: Optional[str] = None,
    ) -> Tuple[List[str], Optional[str]]:
        """
        Lists messages in the user's mailbox with filtering options.

        Args:
            user_id: The user's email address. Special value 'me' indicates the authenticated user.
            query: Optional Gmail search query to filter messages (e.g., "from:example@gmail.com")
            only_newer_than: Optional historyId to fetch only messages newer than this ID

        Returns:
            A tuple containing (list of message IDs, latest historyId)
        """
        try:
            messages = []
            latest_history_id = None

            # Handle incremental updates with history
            # NOTE: currently unused
            if only_newer_than:
                history_response = (
                    self.gmailclient.service.users()
                    .history()
                    .list(userId=user_id, startHistoryId=only_newer_than)
                    .execute()
                )

                if "history" in history_response:
                    pbar = tqdm(desc="Processing history changes", unit="pages")
                    pbar.update(1)

                    for history in history_response["history"]:
                        if "messagesAdded" in history:
                            for msg in history["messagesAdded"]:
                                messages.append(msg["message"]["id"])

                    latest_history_id = history_response.get("historyId")

                    while "nextPageToken" in history_response:
                        page_token = history_response["nextPageToken"]
                        history_response = (
                            self.gmailclient.service.users()
                            .history()
                            .list(
                                userId=user_id,
                                startHistoryId=only_newer_than,
                                pageToken=page_token,
                            )
                            .execute()
                        )

                        if "history" in history_response:
                            for history in history_response["history"]:
                                if "messagesAdded" in history:
                                    for msg in history["messagesAdded"]:
                                        messages.append(msg["message"]["id"])

                        pbar.update(1)
                        latest_history_id = history_response.get(
                            "historyId", latest_history_id
                        )

                    pbar.close()

                messages = list(set(messages))
                self.total_messages = len(messages)
                return messages, latest_history_id

            # Handle regular listing
            params = {}
            if query:
                params["q"] = query

            response = (
                self.gmailclient.service.users()
                .messages()
                .list(userId=user_id, **params)
                .execute()
            )

            if "messages" in response:
                pbar = tqdm(desc="Fetching message pages", unit="pages")
                pbar.update(1)

                messages.extend(message["id"] for message in response["messages"])
                self.total_messages += len(response["messages"])
                pbar.set_postfix({"emails": self.total_messages})

                if "messages" in response and response["messages"]:
                    msg_id = response["messages"][0]["id"]
                    msg = (
                        self.gmailclient.service.users()
                        .messages()
                        .get(userId=user_id, id=msg_id, format="minimal")
                        .execute()
                    )
                    latest_history_id = msg.get("historyId")

                while "nextPageToken" in response:
                    page_token = response["nextPageToken"]
                    params_with_page = params.copy()  # Create a copy to add page token

                    response = (
                        self.gmailclient.service.users()
                        .messages()
                        .list(userId=user_id, pageToken=page_token, **params_with_page)
                        .execute()
                    )

                    if "messages" in response:
                        messages.extend(
                            message["id"] for message in response["messages"]
                        )
                        self.total_messages += len(response["messages"])

                    pbar.update(1)
                    pbar.set_postfix({"emails": self.total_messages})

                pbar.close()

            return messages, latest_history_id

        except Exception as error:
            print(f"An error occurred at list_messages: {error}")
            return [], None

    def get_sender(self, request_id, response, exception):
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
            if response and "payload" in response and "headers" in response["payload"]:
                for header in response["payload"]["headers"]:
                    if header["name"] == "From":
                        self.users.append(header.get("value"))
                        break
            else:
                print(f"Missing expected fields in response for message {request_id}")
        except Exception as error:
            print(f"An error occurred at get_sender for message {request_id}: {error}")

    def _generic_callback(self, request_id, _response, exception, operation: str):
        """
        Generic callback for batch operations.

        Args:
            request_id: ID of the request
            response: Response from the API
            exception: Exception if request failed
            operation: The operation type being performed
        """
        if exception is not None:
            print(f"Error during {operation} for message {request_id}: {exception}")
            return False

        # Update appropriate counter based on operation
        if operation == "trash":
            self.moved_to_trash += 1
        elif operation == "spam":
            self.moved_to_spam += 1
        elif operation == "label":
            self.labels += 1

        return True

    def batch_process(self, items: List[str], operation: str, **kwargs):
        """
        Generic batch processing function for Gmail API operations with exponential backoff.

        Args:
            items: List of IDs or items to process
            operation: Operation type ('trash', 'spam', 'label', 'get')
            **kwargs: Additional arguments needed for specific operations
                - user_id: The user's email address (default 'me')
                - label_id: The label ID (for 'label' operation)

        Returns:
            Number of successfully processed items
        """
        if operation == "trash":
            batch_size = TRASH_BATCH_SIZE
        elif operation == "spam":
            batch_size = SPAM_BATCH_SIZE
        elif operation == "label":
            batch_size = LABEL_BATCH_SIZE
        elif operation == "get":
            batch_size = GET_BATCH_SIZE
        else:
            batch_size = 20

        user_id = kwargs.get("user_id", "me")
        processed_count = 0

        # Define operation-specific configurations
        operations = {
            "trash": {
                "process_batch": lambda batch: self.gmailclient.service.users()
                .messages()
                .batchModify(
                    userId=user_id, body={"addLabelIds": ["TRASH"], "ids": batch}
                )
                .execute(),
                "uses_batch_http": True,
                "desc": "Moving to trash",
                "counter": "moved_to_trash",
            },
            "spam": {
                "process_batch": lambda batch: self.gmailclient.service.users()
                .messages()
                .batchModify(
                    userId=user_id, body={"addLabelIds": ["SPAM"], "ids": batch}
                )
                .execute(),
                "uses_batch_http": True,
                "desc": "Moving to spam",
                "counter": "moved_to_spam",
            },
            "label": {
                "process_batch": lambda batch: self.gmailclient.service.users()
                .messages()
                .batchModify(
                    userId=user_id,
                    body={"addLabelIds": [kwargs.get("label_id")], "ids": batch},
                )
                .execute(),
                "uses_batch_http": True,
                "desc": "Applying label",
                "counter": "labels",
            },
            "get": {
                "create_request": lambda item_id: self.gmailclient.service.users()
                .messages()
                .get(userId=user_id, id=item_id, format="metadata"),
                "callback": self.get_sender,
                "uses_batch_http": False,
                "desc": "Getting messages",
            },
        }

        if operation not in operations:
            raise ValueError(f"Unsupported operation: {operation}")

        op_config = operations[operation]

        # Process in batches with progress tracking
        pbar = tqdm(
            range(0, len(items), batch_size),
            desc=op_config["desc"],
            unit="batch",
        )

        for start_idx in pbar:
            end_idx = min(start_idx + batch_size, len(items))
            batch_items = items[start_idx:end_idx]

            # Implement exponential backoff
            max_retries = 5
            retry_count = 0
            wait_time = 1  # Initial wait time in seconds

            while retry_count <= max_retries:
                try:
                    if op_config.get("uses_batch_http", True):
                        op_config["process_batch"](batch_items)
                        processed_count += len(batch_items)

                        counter_name = op_config.get("counter")
                        if counter_name and hasattr(self, counter_name):
                            setattr(
                                self,
                                counter_name,
                                getattr(self, counter_name) + len(batch_items),
                            )
                    else:
                        batch = self.gmailclient.service.new_batch_http_request(
                            callback=op_config.get("callback")
                        )

                        for item_id in batch_items:
                            batch.add(
                                op_config["create_request"](item_id), request_id=item_id
                            )

                        batch.execute()

                    # Success, break out of retry loop
                    break

                except HttpError as error:
                    if error.resp.status == 429 or (500 <= error.resp.status < 600):
                        retry_count += 1

                        if retry_count > max_retries:
                            print(
                                f"Maximum retries exceeded for batch starting at {start_idx}"
                            )
                            break

                        # Calculate wait time with jitter
                        jitter = random.uniform(0.5, 1.5)
                        sleep_time = wait_time * jitter

                        print(
                            f"Rate limit exceeded, retrying in {sleep_time:.2f} seconds (attempt {retry_count}/{max_retries})"
                        )
                        pbar.set_postfix(
                            {"status": f"Rate limited, retry {retry_count}"}
                        )

                        time.sleep(sleep_time)

                        # Exponential backoff
                        wait_time *= 2
                    else:
                        # If it's not a rate limit or server error, don't retry
                        print(
                            f"Error during {operation} (HTTP {error.resp.status}): {error}"
                        )
                        break
                except Exception as error:
                    print(
                        f"An error occurred during batch processing ({operation}): {error}"
                    )
                    break

        return processed_count

    def batch_get(self, messages: List[str], user_id: str = "me"):
        """
        Process messages in batches to extract sender information.

        Args:
            messages: List of message IDs to process
            user_id: The user's email address (default 'me')
        """
        return self.batch_process(messages, "get", user_id=user_id)

    def batch_delete(self, messages: List[str], user_id: str = "me"):
        """
        Process messages in batches to move them to trash.

        Args:
            messages: List of message IDs to move to trash
            user_id: The user's email address (default 'me')
        """
        return self.batch_process(messages, "trash", user_id=user_id)

    def batch_spam(self, messages: List[str], user_id: str = "me"):
        """
        Process messages in batches to move them to spam.

        Args:
            messages: List of message IDs to move to spam
            user_id: The user's email address (default 'me')
        """
        return self.batch_process(messages, "spam", user_id=user_id)

    def batch_label(self, messages: List[str], label_id: str, user_id: str = "me"):
        """
        Process messages in batches to apply a label.

        Args:
            messages: List of message IDs to label
            label_id: ID of the label to apply
            user_id: The user's email address (default 'me')

        Returns:
            Number of successfully labeled messages
        """
        return self.batch_process(messages, "label", user_id=user_id, label_id=label_id)

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
                pbar = tqdm(desc=f"Finding emails matching '{query}'", unit="pages")
                pbar.update(1)

                messages.extend(message["id"] for message in response["messages"])
                pbar.set_postfix({"found": len(messages)})

                while "nextPageToken" in response:
                    previous_count = len(messages)
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

                    pbar.update(1)
                    pbar.set_postfix({"found": len(messages)})

                    if len(messages) == previous_count:
                        break

                pbar.close()

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
                pbar = tqdm(
                    desc=f"Finding emails with label '{label_id}'", unit="pages"
                )
                pbar.update(1)

                messages.extend(message["id"] for message in response["messages"])
                pbar.set_postfix({"found": len(messages)})

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

                    pbar.update(1)
                    pbar.set_postfix({"found": len(messages)})

                pbar.close()

                if messages:
                    print(f"Found {len(messages)} emails with label '{label_id}'")

            return messages

        except Exception as error:
            print(f"An error occurred at list_messages_matching_label: {error}")
            return []

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
