from _typeshed import Incomplete
from gllm_inference.em_invoker.em_invoker import BaseEMInvoker
from gllm_memory.chat_history_manager.chat_history_processor.chat_history_processor import BaseChatHistoryProcessor as BaseChatHistoryProcessor
from gllm_memory.chat_history_manager.schema import MessagePair as MessagePair
from typing import Callable

class SimilarityBasedChatHistoryProcessor(BaseChatHistoryProcessor):
    """A chat history processor that preprocesses chat history based on sentence similarity.

    Attributes:
        em_invoker (BaseEMInvoker): An instance of the BaseEMInvoker class to embed text.
        threshold (float): The threshold to filter out the chat history.
        similarity_func (Callable[[list[float], list[list[float]]], list[float]]): The function to calculate
            the similarity between embeddings. The function should take two arguments:
            a vector and a matrix of vectors. The function should return a list of similarity scores.
    """
    em_invoker: Incomplete
    threshold: Incomplete
    similarity_func: Incomplete
    def __init__(self, em_invoker: BaseEMInvoker, threshold: float = 0.8, similarity_func: Callable[[list[float], list[list[float]]], list[float]] = ...) -> None:
        """Initializes the SimilarityBasedChatHistoryProcessor class.

        This constructor method initializes an instance of the SimilarityBasedChatHistoryProcessor class, setting up
        the embedding model and threshold that will be used to preprocess chat history based on similarity to a query.

        Args:
            em_invoker (BaseEMInvoker): An instance of the BaseEMInvoker class that will be used to calculate the
                embeddings of the query and the chat history.
            threshold (float, optional): The threshold to filter out the chat history. Defaults to 0.8.
            similarity_func (Callable[[list[float], list[list[float]]], list[float]], optional): The function to
                calculate the similarity between embeddings. The function should take two arguments:
                a vector and a matrix of vectors. The function should return a list of similarity scores.
                Defaults to the `gllm_core.utils.similarity.cosine` similarity function.

        Raises:
            ValueError: If threshold is not between 0 and 1.
        """
    async def process(self, message_pairs: list[MessagePair], user_message: str) -> list[MessagePair]:
        """Filters the message pairs using embedding similarity.

        This method filters the message pairs using embedding similarity.

        Args:
            message_pairs (list[MessagePair]): The message pairs to filter.
            user_message (str): The user message.

        Returns:
            list[MessagePair]: The filtered message pairs.
        """
