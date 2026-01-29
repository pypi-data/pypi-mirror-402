from enum import Enum


class ResourceStatus(Enum):
    Running = (0,)
    Stopped = (1,)
    Restarting = (2,)
    Mixed = (3,)
    Unknown = 100

    @staticmethod
    def from_str(status: str):
        status_lower = status.lower()

        if status_lower == "running":
            return ResourceStatus.Running
        elif status_lower == "stopped":
            return ResourceStatus.Stopped
        elif status_lower == "restarting":
            return ResourceStatus.Restarting
        elif status_lower == "mixed":
            return ResourceStatus.Mixed
        else:
            return ResourceStatus.Unknown


class ResourceClient:
    async def close(self):
        raise NotImplementedError()

    async def status(self) -> ResourceStatus:
        raise NotImplementedError()

    async def get_log_level(self) -> str:
        raise NotImplementedError()

    async def set_log_level(self, log_level: str):
        raise NotImplementedError()

    async def get_quick_info(self):
        raise NotImplementedError()

    async def get_api_url(self) -> str:
        raise NotImplementedError()
