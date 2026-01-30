import asyncio
import contextlib
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from obs import ObsClient
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    MofNCompleteColumn
)
from rich.progress import TaskProgressColumn


class LoongObsClient:
    def __init__(self, access_key_id='HPUATWPNH6CPOZKR2MCL',
                          secret_access_key='xWC2J5gdw53G9MHvjKeIUer22K0rEKqitRUroEfq',
                          server='http://obs.cn-east-3.myhuaweicloud.com'):
        self.obs_client = ObsClient(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            server=server
        )

    def list_objects(self, bucket_name, prefix=None, max_keys=1000, delimiter=None, marker=None):
        resp = self.obs_client.listObjects(bucket_name, prefix, max_keys=max_keys,
                                           delimiter=delimiter, marker=marker, encoding_type='url')

        result = []
        if resp.status < 300:
            for content in resp.body.contents:
                result.append({
                    'key': content.key,
                    'size': content.size,
                    'lastModified': content.lastModified,
                })
        return result

    def download_file(self, bucket_name, object_key, local_file_path, callback=None):
        resp = self.obs_client.getObject(bucket_name, object_key, downloadPath=local_file_path, progressCallback=callback)
        return resp.status < 300

class RichMultiThreadDownloader:
    def __init__(self, max_workers=5):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.futures = []
        self.lock = threading.Lock()
        self.console = Console()
        self.client = LoongObsClient()

        # 创建进度显示
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(binary_units=True),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.console
        )
        self.overall_progress = Progress(
            TextColumn("[bold red]{task.description}"),
            BarColumn(bar_width=None),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console
        )
        self.overall_cnt_task_id = self.overall_progress.add_task("[red]Overall Counts", total=0)
        # self.overall_byte_task_id = self.overall_progress.add_task("[red]Overall Bytes", total=0)
        self.layout = self.make_layout()

    def make_layout(self) -> Layout:
        """生成页面布局"""
        layout = Layout()
        # 将屏幕分为上下两部分：主区域和页脚
        layout.split_column(
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)  # 固定页脚高度为 5
        )
        return layout

    @contextlib.contextmanager
    def live(self, screen=True, output=''):
        self.layout["main"].update(Panel(self.progress, title="[bold blue]Downloading Progress", border_style="blue"))
        self.layout["footer"].update(Panel(self.overall_progress, title="[bold red]Overall Progress", border_style="red"))
        self.update_overall(complete_cnt=0, total_cnt=1)
        with Live(self.layout, console=self.console, screen=screen) as live:
            try:
                yield live
            finally:
                self.wait_finish()
                # 任务结束，更新底部提示框
                self.layout["footer"].update(
                    Panel(f"[bold green]数据已下载至 {output} 目录，请按 [Enter] 键退出程序...",
                          border_style="green", title_align="center")
                )
                # 等待用户输入
                input("")  # 阻塞等待用户按回车

    def update_overall(self, complete_cnt=-1, complete_bytes=-1, advance_cnt=-1, advance_bytes=-1, total_cnt=-1, total_bytes=-1):
        """更新整体进度"""
        with self.lock:
            if complete_cnt >= 0:
                self.overall_progress.update(self.overall_cnt_task_id, completed=complete_cnt)
            if complete_bytes >= 0:
                self.overall_progress.update(self.overall_byte_task_id, completed=complete_bytes)
            if advance_cnt >= 0:
                self.overall_progress.advance(self.overall_cnt_task_id, advance=advance_cnt)
            if advance_bytes >= 0:
                self.overall_progress.advance(self.overall_byte_task_id, advance=advance_bytes)
            if total_cnt >= 0:
                self.overall_progress.update(self.overall_cnt_task_id, total=total_cnt)
            if total_bytes >= 0:
                self.overall_progress.update(self.overall_byte_task_id, total=total_bytes)

    def download_with_progress(self, bucket_name, url, filename, save_dir: Path):
        """使用rich进度条下载文件"""
        tmp_path = save_dir / (filename + '.tmp')
        save_path = save_dir / filename

        with self.progress:
            task_id = self.progress.add_task(
                f"[cyan]Download {filename}",
                filename=filename,
                start=True
            )
            if save_path.exists():
                total = save_path.stat().st_size
                self.progress.update(task_id, completed=total, total=total)
            else:
                def _progress_callback(bytes_transferred, bytes_total, seconds):
                    self.progress.update(task_id, completed=bytes_transferred, total=bytes_total)
                self.client.download_file(bucket_name, url, tmp_path, _progress_callback)
                if tmp_path.exists():
                    tmp_path.rename(save_path)
                else:
                    self.console.print(f"[red]Download {url} failed[/red]")
            self.update_overall(advance_cnt=1)

        return filename, True

    def download_item(self, bucket_name, obs_path, output_dir, filename):
        future = self.executor.submit(
            self.download_with_progress,
            bucket_name, obs_path, filename, output_dir
        )
        self.futures.append(future)

    def wait_finish(self):
        results = []
        for future in self.futures:
            try:
                result = future.result()
                results.append(result)
            except asyncio.CancelledError:
                self.console.print("[red]✗ Download interrupted by user")
            except Exception as e:
                self.console.print(f"[red]✗ 下载失败: {e}")
                results.append((None, False))
        return results
