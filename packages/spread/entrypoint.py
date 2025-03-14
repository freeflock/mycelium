import asyncio
import os
import traceback
from asyncio import sleep

from loguru import logger

from spread.operation.add_region_to_claim import AddRegionToClaim
from spread.operation.add_region_to_spore import AddRegionToSpore
from spread.operation.add_stop_to_nutrient import AddStopToNutrient
from spread.operation.collect_finding import CollectFinding
from spread.operation.determine_claim_relevance import DetermineClaimRelevance
from spread.operation.framework import OperationGroup
from spread.operation.fruit import Fruit
from spread.operation.isolate_claims import IsolateClaims
from spread.operation.spore import Spore

OPERATION_INSTANCE_COUNT = int(os.getenv("OPERATION_INSTANCE_COUNT"))
STOP_NODE_THRESHOLD = int(os.getenv("STOP_NODE_THRESHOLD"))


async def main():
    while True:
        try:
            operation_groups = [
                OperationGroup(OPERATION_INSTANCE_COUNT, Spore),
                OperationGroup(OPERATION_INSTANCE_COUNT, AddStopToNutrient, max_relevant_claims=STOP_NODE_THRESHOLD),
                OperationGroup(OPERATION_INSTANCE_COUNT, AddRegionToSpore),
                OperationGroup(OPERATION_INSTANCE_COUNT, CollectFinding),
                OperationGroup(OPERATION_INSTANCE_COUNT, IsolateClaims),
                OperationGroup(OPERATION_INSTANCE_COUNT, DetermineClaimRelevance),
                OperationGroup(OPERATION_INSTANCE_COUNT, AddRegionToClaim),
                OperationGroup(OPERATION_INSTANCE_COUNT, Fruit),
            ]
            async with asyncio.TaskGroup() as task_group:
                for operation_group in operation_groups:
                    task_group.create_task(operation_group.begin())
        except KeyboardInterrupt:
            raise
        except Exception as error:
            logger.error(f"(!) unhandled exception: {error}\n{traceback.format_exc()}")
            await sleep(3)


if __name__ == '__main__':
    asyncio.run(main())
