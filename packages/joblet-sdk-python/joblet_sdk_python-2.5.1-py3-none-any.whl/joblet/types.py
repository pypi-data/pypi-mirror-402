"""Type definitions for Joblet SDK.

This module contains TypedDict classes that provide strong typing for
API responses and data structures used throughout the SDK.
"""

from typing import Any, Dict, List

# Use typing_extensions for Python 3.9 compatibility
try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


class JobResponse(TypedDict):
    """Response from running a job."""

    job_uuid: str
    status: str
    command: str
    args: List[str]
    max_cpu: int
    cpu_cores: str
    max_memory: int
    max_iobps: int
    start_time: str
    end_time: str
    exit_code: int
    scheduled_time: str


class JobStatusResponse(TypedDict):
    """Response from getting job status."""

    uuid: str
    name: str
    command: str
    args: List[str]
    max_cpu: int
    cpu_cores: str
    max_memory: int
    max_iobps: int
    status: str
    start_time: str
    end_time: str
    exit_code: int
    scheduled_time: str
    environment: Dict[str, str]
    secret_environment: Dict[str, str]
    network: str
    volumes: List[str]
    runtime: str
    work_dir: str
    uploads: List[str]
    gpu_indices: List[int]
    gpu_count: int
    gpu_memory_mb: int
    node_id: str


class StopJobResponse(TypedDict):
    """Response from stopping a job."""

    uuid: str
    status: str
    end_time: str
    exit_code: int


class CancelJobResponse(TypedDict):
    """Response from canceling a scheduled job."""

    uuid: str
    status: str


class DeleteJobResponse(TypedDict):
    """Response from deleting a job."""

    uuid: str
    success: bool
    message: str


class DeleteAllJobsResponse(TypedDict):
    """Response from deleting all jobs."""

    success: bool
    message: str
    deleted_count: int
    skipped_count: int


class JobListItem(TypedDict):
    """A job item in the job list."""

    uuid: str
    name: str
    command: str
    args: List[str]
    max_cpu: int
    cpu_cores: str
    max_memory: int
    max_iobps: int
    status: str
    start_time: str
    end_time: str
    exit_code: int
    scheduled_time: str
    runtime: str
    environment: Dict[str, str]
    secret_environment: Dict[str, str]
    gpu_indices: List[int]
    gpu_count: int
    gpu_memory_mb: int
    node_id: str


class MetricsEvent(TypedDict):
    """A metrics event from job monitoring."""

    timestamp: int
    job_id: str
    cpu_percent: float
    memory_bytes: int
    memory_limit: int
    disk_read_bytes: int
    disk_write_bytes: int
    net_recv_bytes: int
    net_sent_bytes: int
    gpu_percent: float
    gpu_memory_bytes: int


class ExecEventData(TypedDict):
    """Exec event data from telematics."""

    pid: int
    ppid: int
    binary: str
    args: List[str]
    exit_code: int


class ConnectEventData(TypedDict):
    """Connect event data from telematics."""

    pid: int
    dst_addr: str
    dst_port: int
    src_addr: str
    src_port: int
    protocol: str


class AcceptEventData(TypedDict):
    """Accept event data from telematics."""

    pid: int
    src_addr: str
    src_port: int
    dst_addr: str
    dst_port: int
    protocol: str


class FileEventData(TypedDict):
    """File event data from telematics."""

    pid: int
    path: str
    operation: str
    bytes: int
    flags: int


class MmapEventData(TypedDict):
    """Mmap event data from telematics."""

    pid: int
    addr: int
    length: int
    prot: int
    flags: int
    file_path: str


class MprotectEventData(TypedDict):
    """Mprotect event data from telematics."""

    pid: int
    addr: int
    length: int
    prot: int


class SocketDataEventData(TypedDict):
    """Socket data event from telematics."""

    pid: int
    direction: str
    dst_addr: str
    dst_port: int
    src_addr: str
    src_port: int
    protocol: str
    bytes: int


class TelematicsEvent(TypedDict, total=False):
    """A telematics event from eBPF monitoring."""

    timestamp: int
    job_id: str
    type: str
    exec: ExecEventData
    connect: ConnectEventData
    accept: AcceptEventData
    file: FileEventData
    mmap: MmapEventData
    mprotect: MprotectEventData
    socket_data: SocketDataEventData


class NetworkResponse(TypedDict):
    """Response from creating a network."""

    name: str
    cidr: str
    bridge: str


class NetworkListItem(TypedDict):
    """A network item in the network list."""

    name: str
    cidr: str
    bridge: str
    job_count: int


class RemoveResponse(TypedDict):
    """Response from removing a resource."""

    success: bool
    message: str


class VolumeResponse(TypedDict):
    """Response from creating a volume."""

    name: str
    size: str
    type: str
    path: str


class VolumeListItem(TypedDict):
    """A volume item in the volume list."""

    name: str
    size: str
    type: str
    path: str
    created_time: str
    job_count: int


class RuntimeRequirements(TypedDict):
    """Runtime requirements."""

    architectures: List[str]
    gpu: bool


class RuntimeInfo(TypedDict, total=False):
    """Runtime information."""

    name: str
    language: str
    version: str
    description: str
    size_bytes: int
    packages: List[str]
    available: bool
    requirements: RuntimeRequirements


class RuntimeTestResult(TypedDict):
    """Result from testing a runtime."""

    success: bool
    output: str
    error: str
    exit_code: int


class RuntimeRemoveResult(TypedDict):
    """Result from removing a runtime."""

    success: bool
    message: str
    freed_space_bytes: int


class BuildPhase(TypedDict):
    """Build phase progress."""

    phase_number: int
    total_phases: int
    phase_name: str
    message: str


class BuildLog(TypedDict):
    """Build log entry."""

    level: str
    message: str
    timestamp: str


class BuildResult(TypedDict):
    """Build result."""

    success: bool
    message: str
    runtime_name: str
    runtime_version: str
    runtime_path: str
    build_duration_seconds: float


class BuildProgress(TypedDict, total=False):
    """Build progress event."""

    phase: BuildPhase
    log: BuildLog
    result: BuildResult


class ValidationResult(TypedDict, total=False):
    """Runtime YAML validation result."""

    valid: bool
    message: str
    parsed_spec: Dict[str, Any]
    errors: List[str]


class HostInfo(TypedDict):
    """Host system information."""

    hostname: str
    os: str
    platform: str
    platform_family: str
    platform_version: str
    kernel_version: str
    kernel_arch: str
    architecture: str
    cpu_count: int
    total_memory: int
    boot_time: int
    uptime: int
    node_id: str
    server_ips: List[str]
    mac_addresses: List[str]


class CPUMetrics(TypedDict):
    """CPU metrics."""

    cores: int
    usage_percent: float
    user_time: float
    system_time: float
    idle_time: float
    io_wait_time: float
    steal_time: float
    load_average: List[float]
    per_core_usage: List[float]


class MemoryMetrics(TypedDict):
    """Memory metrics."""

    total_bytes: int
    used_bytes: int
    free_bytes: int
    available_bytes: int
    usage_percent: float
    cached_bytes: int
    buffered_bytes: int
    swap_total: int
    swap_used: int
    swap_free: int


class DiskMetrics(TypedDict):
    """Disk metrics."""

    device: str
    mount_point: str
    filesystem: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float
    inodes_total: int
    inodes_used: int
    inodes_free: int
    inodes_usage_percent: float


class NetworkMetrics(TypedDict):
    """Network interface metrics."""

    interface: str
    bytes_received: int
    bytes_sent: int
    packets_received: int
    packets_sent: int
    errors_in: int
    errors_out: int
    drops_in: int
    drops_out: int
    receive_rate: float
    transmit_rate: float


class DiskIOMetrics(TypedDict):
    """Disk I/O metrics."""

    device: str
    reads_completed: int
    writes_completed: int
    read_bytes: int
    write_bytes: int
    read_time: int
    write_time: int
    io_time: int
    utilization: float


class IOMetrics(TypedDict, total=False):
    """I/O metrics."""

    total_reads: int
    total_writes: int
    read_bytes: int
    write_bytes: int
    read_rate: float
    write_rate: float
    disk_io: List[DiskIOMetrics]


class ProcessInfo(TypedDict):
    """Process information."""

    pid: int
    ppid: int
    name: str
    command: str
    cpu_percent: float
    memory_percent: float
    memory_bytes: int
    status: str
    start_time: int
    user: str


class ProcessMetrics(TypedDict, total=False):
    """Process metrics."""

    total_processes: int
    running_processes: int
    sleeping_processes: int
    stopped_processes: int
    zombie_processes: int
    total_threads: int
    top_by_cpu: List[ProcessInfo]
    top_by_memory: List[ProcessInfo]


class CloudInfo(TypedDict):
    """Cloud provider information."""

    provider: str
    region: str
    zone: str
    instance_id: str
    instance_type: str
    hypervisor_type: str
    metadata: Dict[str, str]


class ServerVersion(TypedDict):
    """Server version information."""

    version: str
    git_commit: str
    git_tag: str
    build_date: str
    component: str
    go_version: str
    platform: str
    proto_commit: str
    proto_tag: str


class SystemStatus(TypedDict, total=False):
    """System status response."""

    timestamp: int
    available: bool
    host: HostInfo
    cpu: CPUMetrics
    memory: MemoryMetrics
    disks: List[DiskMetrics]
    networks: List[NetworkMetrics]
    io: IOMetrics
    processes: ProcessMetrics
    cloud: CloudInfo
    server_version: ServerVersion


class SystemMetrics(TypedDict, total=False):
    """System metrics response."""

    timestamp: int
    host: HostInfo
    cpu: CPUMetrics
    memory: MemoryMetrics
    disks: List[DiskMetrics]
    networks: List[NetworkMetrics]
    io: IOMetrics
    processes: ProcessMetrics
    cloud: CloudInfo


__all__ = [
    # Job types
    "JobResponse",
    "JobStatusResponse",
    "StopJobResponse",
    "CancelJobResponse",
    "DeleteJobResponse",
    "DeleteAllJobsResponse",
    "JobListItem",
    # Metrics types
    "MetricsEvent",
    # Telematics types
    "ExecEventData",
    "ConnectEventData",
    "AcceptEventData",
    "FileEventData",
    "MmapEventData",
    "MprotectEventData",
    "SocketDataEventData",
    "TelematicsEvent",
    # Network types
    "NetworkResponse",
    "NetworkListItem",
    "RemoveResponse",
    # Volume types
    "VolumeResponse",
    "VolumeListItem",
    # Runtime types
    "RuntimeRequirements",
    "RuntimeInfo",
    "RuntimeTestResult",
    "RuntimeRemoveResult",
    "BuildPhase",
    "BuildLog",
    "BuildResult",
    "BuildProgress",
    "ValidationResult",
    # System types
    "HostInfo",
    "CPUMetrics",
    "MemoryMetrics",
    "DiskMetrics",
    "NetworkMetrics",
    "DiskIOMetrics",
    "IOMetrics",
    "ProcessInfo",
    "ProcessMetrics",
    "CloudInfo",
    "ServerVersion",
    "SystemStatus",
    "SystemMetrics",
]
