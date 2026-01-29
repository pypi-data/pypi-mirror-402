from _typeshed import Incomplete
from gllm_inference.request_processor import LMRequestProcessor, UsesLM
from gllm_memory.chat_history_manager.chat_history_processor.chat_history_processor import BaseChatHistoryProcessor as BaseChatHistoryProcessor
from gllm_memory.chat_history_manager.schema import MessagePair as MessagePair
from typing import Callable

DEFAULT_LM_OUTPUT_KEY: str

class LMBasedChatHistoryProcessor(BaseChatHistoryProcessor, UsesLM):
    '''A chat history processor which uses a language model.

    This class provides a chat history processor which uses a language model to perform the
    post-processing of chat histories by selecting relevant message pairs.

    This approach prevents hallucination by constraining the LM to select only from existing
    message pairs, rather than generating new content. It also ensures that user messages
    and their corresponding assistant responses are kept together, preserving the conversational flow.

    Attributes:
        lm_request_processor (LMRequestProcessor): The request processor that handles requests to the language model.
        lm_output_key (str): The key in the language model\'s output that contains the selected pair IDs.
            Defaults to DEFAULT_LM_OUTPUT_KEY.
        batch_size (int): The number of message pairs to process at a time.
        formatter_fn (Callable[[list[MessagePair]], str]): A function that formats message pairs to a string.
            If None, _format_message_pairs_as_string will be used.

    Notes:
        When defining the `lm_request_processor`, you must carefully consider the input and output formats:

        The `lm_request_processor` must be configured to:
           1. Take the following keys as input:
              1. `message_pairs`: The evaluated message pairs from the chat history.
              2. `user_message`: Latest user message to be compared with the message pairs.
           2. Return a JSON object with the IDs of relevant message pairs.

        The `message_pairs` to be sent to the language model will be formatted using the `formatter_fn`.
        If `formatter_fn` is not given, the default format will be used. The default format is as follows:
           ```
           <Pair>
           id: <pair_id_1>
           user: <user_message_1>
           assistant: <assistant_response_1>
           </Pair>

           <Pair>
           id: <pair_id_2>
           user: <user_message_2>
           assistant: <assistant_response_2>
           </Pair>
           ```

        The expected output from the `lm_request_processor`:
           ```
           {
               "relevant_pair_ids": ["<pair_id_1>", "<pair_id_3>"]
           }
           ```
        Where "relevant_pair_ids" is the value specified by `lm_output_key`.
    '''
    lm_request_processor: Incomplete
    lm_output_key: Incomplete
    batch_size: Incomplete
    formatter_fn: Incomplete
    def __init__(self, lm_request_processor: LMRequestProcessor, lm_output_key: str = ..., batch_size: int = 5, formatter_fn: Callable[[list[MessagePair]], str] | None = None) -> None:
        """Initializes a new instance of the LMBasedChatHistoryProcessor class.

        Args:
            lm_request_processor (LMRequestProcessor): The request processor that
                handles requests to the language model.
            lm_output_key (str, optional): The key in the language model's output that contains the message IDs.
                Defaults to DEFAULT_LM_OUTPUT_KEY.
            batch_size (int, optional): The number of message pairs to process at a time. Defaults to 5.
            formatter_fn (Callable[[str, MessagePair], str] | None, optional): A function to format a message pair
                into string. Defaults to None. If None, defaults to `_format_message_pairs`.
        """
    async def process(self, message_pairs: list[MessagePair], user_message: str) -> list[MessagePair]:
        """Filters the message pairs using a language model.

        This method filters the message pairs using a language model.

        Args:
            message_pairs (list[MessagePair]): The message pairs to filter.
            user_message (str): The user message.

        Returns:
            list[MessagePair]: The filtered message pairs.
        """
