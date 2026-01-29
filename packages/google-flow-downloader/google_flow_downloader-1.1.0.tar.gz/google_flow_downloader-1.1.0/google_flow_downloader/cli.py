"""命令行接口"""

import click
import requests
import json
import urllib.parse
import os
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree
from rich import box
from . import BROWSER_SCRIPT

console = Console()

DEFAULT_OUTPUT_DIR = Path.home() / "Code/GenAI/google_flow_images"


def parse_cookies(cookie_string):
    """解析 Cookie 字符串"""
    cookies = {}
    for item in cookie_string.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()
    return cookies


def extract_project_id_from_url(url):
    """从 URL 中提取 project ID"""
    import re
    match = re.search(r'project/([a-f0-9-]+)', url)
    return match.group(1) if match else None


@click.group()
@click.version_option()
def main():
    """Google Flow 图片批量下载工具"""
    pass


@main.command()
@click.option('--output', '-o', type=click.Path(), default=str(DEFAULT_OUTPUT_DIR), 
              help='输出目录')
@click.option('--cookie', '-c', envvar='GFLOW_COOKIE', 
              help='完整 Cookie 字符串 (或设置环境变量 GFLOW_COOKIE)')
@click.option('--token', '-t', envvar='GFLOW_SESSION_TOKEN',
              help='Session token (或设置环境变量 GFLOW_SESSION_TOKEN)')
@click.option('--project-id', '-p', envvar='GFLOW_PROJECT_ID',
              help='Project ID (或设置环境变量 GFLOW_PROJECT_ID)')
@click.option('--url', '-u', help='项目 URL (自动提取 project ID)')
def download(output, cookie, token, project_id, url):
    """从 API 直接下载图片
    
    支持三种方式提供认证信息：
    
    1. 完整 Cookie (推荐):
       gflow download --cookie "完整cookie字符串"
    
    2. Session Token + Project ID:
       gflow download --token "xxx" --project-id "xxx"
    
    3. 项目 URL (自动提取 ID):
       gflow download --cookie "xxx" --url "https://labs.google/fx/tools/flow/project/xxx"
    """
    
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(Panel.fit("🚀 Google Flow 图片下载", style="bold blue"))
    
    # 解析认证信息
    cookies_dict = {}
    
    if cookie:
        cookies_dict = parse_cookies(cookie)
        # 从 Cookie 中提取 token
        if not token:
            token = cookies_dict.get('__Secure-next-auth.session-token')
    
    if not token:
        console.print("[red]❌ 缺少认证信息[/red]")
        console.print("请提供 --cookie 或 --token")
        return
    
    # 提取 project ID
    if url and not project_id:
        project_id = extract_project_id_from_url(url)
    
    if not project_id:
        console.print("[red]❌ 缺少 Project ID[/red]")
        console.print("请提供 --project-id 或 --url")
        return
    
    console.print(f"📋 Project ID: [dim]{project_id[:20]}...[/dim]")
    
    # 获取已下载
    downloaded = get_downloaded_keys(output_dir)
    console.print(f"📊 已下载: [cyan]{len(downloaded)}[/cyan] 张")
    
    # 获取所有图片
    with console.status("[bold green]📥 从 API 获取图片列表..."):
        try:
            images = fetch_all_images(token, project_id, cookies_dict)
        except Exception as e:
            console.print(f"[red]❌ 获取失败: {e}[/red]")
            return
    
    console.print(f"📊 API 返回: [cyan]{len(images)}[/cyan] 张")
    
    # 去重
    to_download = [img for img in images if img["key"] not in downloaded]
    
    if not to_download:
        console.print("[green]✅ 所有图片已下载完毕！[/green]")
        return
    
    console.print(f"📥 需要下载: [yellow]{len(to_download)}[/yellow] 张\n")
    
    # 下载
    success = 0
    failed = 0
    total_bytes = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]下载图片...", total=len(to_download))
        
        for img in to_download:
            filepath = output_dir / f"{img['key']}.jpg"
            try:
                # 下载并统计大小
                resp = requests.get(img["url"], stream=True, timeout=30)
                resp.raise_for_status()
                
                file_size = 0
                with open(filepath, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
                        file_size += len(chunk)
                
                total_bytes += file_size
                success += 1
            except:
                failed += 1
            progress.update(task, advance=1)
    
    # 结果表格
    table = Table(title="📊 下载结果", box=box.ROUNDED, show_header=False)
    table.add_row("✅ 成功", f"[green]{success}[/green] 张")
    if failed > 0:
        table.add_row("❌ 失败", f"[red]{failed}[/red] 张")
    table.add_row("📦 下载大小", f"[cyan]{total_bytes / 1024 / 1024:.1f}[/cyan] MB")
    table.add_row("📊 总计", f"[bold cyan]{len(downloaded) + success}[/bold cyan] 张")
    table.add_row("📁 位置", f"[dim]{output_dir}[/dim]")
    
    console.print("\n")
    console.print(table)


@main.command()
@click.argument('json_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), default=str(DEFAULT_OUTPUT_DIR),
              help='输出目录')
def from_json(json_file, output):
    """从浏览器导出的 JSON 文件下载"""
    
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(Panel.fit("📥 从 JSON 下载图片", style="bold blue"))
    
    # 读取 JSON
    with open(json_file) as f:
        images = json.load(f)
    
    console.print(f"📊 JSON 中有: [cyan]{len(images)}[/cyan] 张")
    
    # 去重
    downloaded = get_downloaded_keys(output_dir)
    console.print(f"📊 已下载: [cyan]{len(downloaded)}[/cyan] 张")
    
    to_download = [img for img in images if img["key"] not in downloaded]
    
    if not to_download:
        console.print("[green]✅ 所有图片已下载！[/green]")
        return
    
    console.print(f"📥 需要下载: [yellow]{len(to_download)}[/yellow] 张\n")
    
    # 下载
    success = 0
    total_bytes = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        DownloadColumn(),
        TransferSpeedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]下载图片...", total=len(to_download))
        
        for img in to_download:
            try:
                resp = requests.get(img["url"], stream=True, timeout=30)
                resp.raise_for_status()
                
                file_size = 0
                filepath = output_dir / f"{img['key']}.jpg"
                with open(filepath, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
                        file_size += len(chunk)
                
                total_bytes += file_size
                success += 1
            except:
                pass
            progress.update(task, advance=1)
    
    # 结果
    table = Table(title="📊 下载结果", box=box.ROUNDED, show_header=False)
    table.add_row("✅ 成功", f"[green]{success}[/green] 张")
    table.add_row("📦 下载大小", f"[cyan]{total_bytes / 1024 / 1024:.1f}[/cyan] MB")
    table.add_row("📊 总计", f"[bold cyan]{len(downloaded) + success}[/bold cyan] 张")
    table.add_row("📁 位置", f"[dim]{output_dir}[/dim]")


@main.command()
@click.option('--copy', '-c', is_flag=True, help='复制到剪贴板 (macOS)')
def script(copy):
    """显示浏览器提取脚本"""
    
    console.print(Panel.fit("📋 浏览器提取脚本", style="bold magenta", border_style="magenta"))
    
    # macOS 自动复制到剪贴板
    if copy:
        import subprocess
        try:
            subprocess.run(['pbcopy'], input=BROWSER_SCRIPT.encode(), check=True)
            console.print("\n[bold green]✅ 已复制到剪贴板！[/bold green]")
            console.print("[dim]直接在浏览器 Console 粘贴 (Cmd+V) 即可[/dim]\n")
        except Exception as e:
            console.print(f"[yellow]⚠️  复制失败: {e}[/yellow]\n")
            copy = False
    
    if not copy:
        # 显示使用步骤
        steps = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        steps.add_row("[bold cyan]1.[/bold cyan]", "打开 Google Flow 项目页面")
        steps.add_row("", "[dim]https://labs.google/fx/tools/flow/project/YOUR_PROJECT_ID[/dim]")
        steps.add_row("[bold cyan]2.[/bold cyan]", "按 [bold]F12[/bold] → [bold]Console[/bold] 标签")
        steps.add_row("[bold cyan]3.[/bold cyan]", "运行: [cyan]gflow script -c[/cyan] (自动复制)")
        steps.add_row("[bold cyan]4.[/bold cyan]", "在浏览器 Console 粘贴 ([bold]Cmd+V[/bold]) 并回车")
        steps.add_row("[bold cyan]5.[/bold cyan]", "等待自动滚动完成，下载 JSON 文件")
        steps.add_row("[bold cyan]6.[/bold cyan]", "运行: [cyan]gflow from-json ~/Downloads/google_flow_complete_XXX.json[/cyan]")
        
        console.print("\n[bold yellow]📖 使用步骤：[/bold yellow]")
        console.print(steps)
        
        console.print("\n[bold]📝 JavaScript 脚本：[/bold]")
        syntax = Syntax(BROWSER_SCRIPT, "javascript", theme="monokai", line_numbers=True, word_wrap=True)
        console.print(syntax)
        
        console.print("\n[bold green]💡 提示：[/bold green]")
        console.print("  • 使用 [cyan]-c[/cyan] 参数自动复制到剪贴板")
        console.print("  • 脚本会自动滚动并收集所有图片")
        console.print("  • 完成后自动导出 JSON 文件")


@main.command()
@click.option('--output', '-o', type=click.Path(), default=str(DEFAULT_OUTPUT_DIR))
def status(output):
    """查看下载状态"""
    
    output_dir = Path(output)
    
    console.print(Panel.fit("📊 下载状态", style="bold blue"))
    
    if not output_dir.exists():
        console.print(f"\n[yellow]📁 目录不存在: {output_dir}[/yellow]")
        return
    
    downloaded = get_downloaded_keys(output_dir)
    
    if not downloaded:
        console.print("\n[yellow]📊 还没有下载任何图片[/yellow]")
        console.print("\n💡 开始使用:")
        console.print("  [cyan]gflow script -c[/cyan]  # 复制浏览器脚本")
        return
    
    # 统计文件大小和时间
    total_size = 0
    oldest_time = None
    newest_time = None
    
    for key in downloaded:
        filepath = output_dir / f"{key}.jpg"
        if filepath.exists():
            stat = filepath.stat()
            total_size += stat.st_size
            mtime = stat.st_mtime
            if oldest_time is None or mtime < oldest_time:
                oldest_time = mtime
            if newest_time is None or mtime > newest_time:
                newest_time = mtime
    
    # 显示详细信息
    from datetime import datetime
    
    table = Table(box=box.ROUNDED, show_header=False, title="📊 下载统计")
    table.add_row("📷 图片数量", f"[bold cyan]{len(downloaded)}[/bold cyan] 张")
    table.add_row("💾 总大小", f"[cyan]{total_size / 1024 / 1024:.1f}[/cyan] MB")
    table.add_row("📁 保存位置", f"[dim]{output_dir}[/dim]")
    
    if oldest_time and newest_time:
        oldest = datetime.fromtimestamp(oldest_time).strftime("%Y-%m-%d %H:%M")
        newest = datetime.fromtimestamp(newest_time).strftime("%Y-%m-%d %H:%M")
        table.add_row("📅 最早下载", f"[dim]{oldest}[/dim]")
        table.add_row("📅 最新下载", f"[dim]{newest}[/dim]")
    
    console.print("\n")
    console.print(table)
    
    # 显示最近下载的图片
    recent_files = sorted(
        [(output_dir / f"{key}.jpg", key) for key in list(downloaded)[:5] if (output_dir / f"{key}.jpg").exists()],
        key=lambda x: x[0].stat().st_mtime,
        reverse=True
    )[:5]
    
    if recent_files:
        console.print("\n[bold]📸 最近下载的图片:[/bold]")
        tree = Tree("🖼️  图片列表", guide_style="dim")
        for filepath, key in recent_files:
            size = filepath.stat().st_size / 1024
            tree.add(f"[cyan]{key[:20]}...[/cyan] [dim]({size:.1f} KB)[/dim]")
        console.print(tree)


# 辅助函数
def get_downloaded_keys(output_dir):
    """获取已下载的图片 key"""
    keys = set()
    if output_dir.exists():
        for f in output_dir.glob("*.jpg"):
            key = f.stem.split('_')[-1]
            if len(key) == 36 and key.count('-') == 4:
                keys.add(key)
    return keys


def fetch_all_images(token, project_id, cookies_dict=None):
    """从 API 获取所有图片"""
    params = {
        "json": {
            "pageSize": 500,
            "projectId": project_id,
            "toolName": "PINHOLE",
            "fetchBookmarked": False,
            "rawQuery": "",
            "mediaType": "MEDIA_TYPE_IMAGE"
        }
    }
    
    url = f"https://labs.google/fx/api/trpc/project.searchProjectWorkflows?input={urllib.parse.quote(json.dumps(params))}"
    
    # 使用完整 Cookie 或只用 token
    if cookies_dict:
        cookies = cookies_dict
    else:
        cookies = {"__Secure-next-auth.session-token": token}
    
    resp = requests.get(
        url,
        cookies=cookies,
        headers={"user-agent": "Mozilla/5.0"},
        timeout=30
    )
    resp.raise_for_status()
    
    data = resp.json()
    workflows = data["result"]["data"]["json"]["result"]["workflows"]
    
    images = []
    for wf in workflows:
        for step in wf.get("workflowSteps", []):
            for media in step.get("mediaGenerations", []):
                key = media.get("mediaGenerationId", {}).get("mediaKey")
                url = media.get("mediaData", {}).get("imageData", {}).get("fifeUri")
                if key and url:
                    images.append({"key": key, "url": url})
    
    return images


def download_image(url, filepath):
    """下载图片"""
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()
    with open(filepath, "wb") as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)


if __name__ == "__main__":
    main()
