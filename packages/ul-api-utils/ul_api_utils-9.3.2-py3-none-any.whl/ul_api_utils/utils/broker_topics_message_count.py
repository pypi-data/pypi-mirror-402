from typing import NamedTuple, List, Optional

from ul_unipipeline.errors import UniError
from ul_unipipeline.modules.uni import Uni


class DataStreamStats(NamedTuple):
    messages_count: int
    queue_name: str
    error_queue: bool
    error: Optional[str]


def get_data_streams_stats(uni: Uni) -> List[DataStreamStats]:
    stats = []
    error__error_messages_count = error__expect_messages_count = None
    for wd in uni.config.workers.values():
        try:
            broker = uni._mediator.get_broker(wd.broker.name)
        except UniError:
            pass
        else:
            try:
                expect_messages_count = broker.get_topic_approximate_messages_count(wd.topic)
            except UniError:
                expect_messages_count = -1
                error__expect_messages_count = "inactive"
            try:
                error_messages_count = broker.get_topic_approximate_messages_count(wd.error_topic)
            except UniError:
                error_messages_count = -1
                error__error_messages_count = "inactive"

            stats.append(DataStreamStats(
                messages_count=expect_messages_count,
                queue_name=wd.topic,
                error_queue=False,
                error=error__expect_messages_count,
            ))
            stats.append(DataStreamStats(
                messages_count=error_messages_count,
                queue_name=wd.error_topic,
                error_queue=True,
                error=error__error_messages_count,
            ))

    return stats
