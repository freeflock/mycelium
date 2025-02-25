import asyncio
import traceback
from asyncio import sleep
from uuid import uuid4

from loguru import logger

from spread.operation.add_region_to_claim import add_region_to_claim
from spread.operation.add_region_to_spore import add_region_to_spore
from spread.operation.collect_finding import collect_finding
from spread.operation.determine_claim_relevance import determine_claim_relevance
from spread.operation.framework import loop_operation
from spread.operation.isolate_claims import isolate_claims
from spread.operation.spore import spore


async def main():
    engagement_handle = str(uuid4())
    while True:
        try:
            async with asyncio.TaskGroup() as task_group:
                task_group.create_task(loop_operation(spore, engagement_handle)),
                task_group.create_task(loop_operation(add_region_to_spore, engagement_handle)),
                task_group.create_task(loop_operation(collect_finding, engagement_handle)),
                task_group.create_task(loop_operation(isolate_claims, engagement_handle)),
                task_group.create_task(loop_operation(determine_claim_relevance, engagement_handle)),
                task_group.create_task(loop_operation(add_region_to_claim, engagement_handle))
        except KeyboardInterrupt:
            raise
        except Exception as error:
            logger.error(f"(!) unhandled exception: {error}\n{traceback.format_exc()}")
            await sleep(3)


if __name__ == '__main__':
    asyncio.run(main())
