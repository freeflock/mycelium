import asyncio
import os
import traceback
from asyncio import sleep
from math import ceil

from freeflock_contraptions.framework import OperationGroup
from loguru import logger

from spread.operation.add_region_to_claim import AddRegionToClaim
from spread.operation.add_region_to_spore import AddRegionToSpore
from spread.operation.add_spore_to_nutrient_with_dead_ends import AddSporeToNutrientWithDeadEnds
from spread.operation.add_stop_to_nutrient import AddStopToNutrient
from spread.operation.collect_finding import CollectFinding
from spread.operation.determine_claim_relevance import DetermineClaimRelevance
from spread.operation.fruit import Fruit
from spread.operation.isolate_claims import IsolateClaims
from spread.operation.spore import Spore

OPERATION_INSTANCE_COUNT = int(os.getenv("OPERATION_INSTANCE_COUNT"))
STOP_NODE_THRESHOLD = int(os.getenv("STOP_NODE_THRESHOLD"))


async def main():
    while True:
        try:
            spore_operation_count = ceil(OPERATION_INSTANCE_COUNT * 0.1)
            add_stop_operation_count = ceil(OPERATION_INSTANCE_COUNT * 0.5)
            claim_relevance_operation_count = ceil(OPERATION_INSTANCE_COUNT * 5)
            fruit_operation_count = ceil(OPERATION_INSTANCE_COUNT * 0.5)
            operation_groups = [
                OperationGroup(spore_operation_count, Spore),
                OperationGroup(spore_operation_count, AddSporeToNutrientWithDeadEnds),
                OperationGroup(add_stop_operation_count, AddStopToNutrient, max_relevant_claims=STOP_NODE_THRESHOLD),
                OperationGroup(OPERATION_INSTANCE_COUNT, AddRegionToSpore),
                OperationGroup(OPERATION_INSTANCE_COUNT, CollectFinding),
                OperationGroup(OPERATION_INSTANCE_COUNT, IsolateClaims),
                OperationGroup(claim_relevance_operation_count, DetermineClaimRelevance),
                OperationGroup(OPERATION_INSTANCE_COUNT, AddRegionToClaim),
                OperationGroup(fruit_operation_count, Fruit),
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
