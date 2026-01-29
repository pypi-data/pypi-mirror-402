#!/usr/bin/env python3
"""
抖音和小红书内容提取 MCP 服务器

该服务器提供以下功能：
1. 抖音：解析分享链接获取无水印视频链接、提取文本内容
2. 小红书：解析分享链接获取视频/图文内容、提取文案和文章
3. 自动清理中间文件
"""

import os
import re
import json
import requests
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Tuple, Dict, List
import ffmpeg
from tqdm.asyncio import tqdm
from urllib import request, parse
from http import HTTPStatus
import dashscope
from bs4 import BeautifulSoup

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import Context


# 创建 MCP 服务器实例
mcp = FastMCP("Social Media Content Extractor MCP Server", 
              dependencies=["requests", "ffmpeg-python", "tqdm", "dashscope", "beautifulsoup4"])

# 请求头，模拟移动端访问
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/121.0.2277.107 Version/17.0 Mobile/15E148 Safari/604.1'
}

# 默认 API 配置
DEFAULT_MODEL = "paraformer-v2"

# 配置文件路径
CONFIG_FILE = Path(__file__).parent.parent / "config.json"

def load_config():
    """加载配置文件"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 如果配置文件不存在，尝试从环境变量读取
            api_key = os.getenv('DASHSCOPE_API_KEY')
            if api_key:
                return {
                    "api_key": api_key,
                    "model": DEFAULT_MODEL,
                    "language_hints": ["zh", "en"],
                    "temp_dir": "temp"
                }
            else:
                raise FileNotFoundError("未找到配置文件 config.json，且未设置环境变量 DASHSCOPE_API_KEY")
    except Exception as e:
        raise Exception(f"加载配置文件失败: {e}")

# 加载配置
try:
    CONFIG = load_config()
except Exception as e:
    print(f"配置加载失败: {e}")
    CONFIG = {
        "api_key": os.getenv('DASHSCOPE_API_KEY', ''),
        "model": DEFAULT_MODEL,
        "language_hints": ["zh", "en"],
        "temp_dir": "temp"
    }


class DouyinProcessor:
    """抖音视频处理器"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # 如果没有提供api_key，从配置文件读取
        if api_key is None:
            api_key = CONFIG.get("api_key", "")

        if not api_key:
            raise ValueError("未设置API密钥，请在config.json中配置或传入api_key参数")

        self.api_key = api_key
        self.model = model or CONFIG.get("model", DEFAULT_MODEL)
        self.temp_dir = Path(tempfile.mkdtemp())
        # 设置阿里云百炼API密钥
        dashscope.api_key = api_key
    
    def __del__(self):
        """清理临时目录"""
        import shutil
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def parse_share_url(self, share_text: str) -> dict:
        """从分享文本中提取无水印视频链接"""
        # 提取分享链接
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', share_text)
        if not urls:
            raise ValueError("未找到有效的分享链接")
        
        share_url = urls[0]
        share_response = requests.get(share_url, headers=HEADERS)
        video_id = share_response.url.split("?")[0].strip("/").split("/")[-1]
        share_url = f'https://www.iesdouyin.com/share/video/{video_id}'
        
        # 获取视频页面内容
        response = requests.get(share_url, headers=HEADERS)
        response.raise_for_status()
        
        pattern = re.compile(
            pattern=r"window\._ROUTER_DATA\s*=\s*(.*?)</script>",
            flags=re.DOTALL,
        )
        find_res = pattern.search(response.text)

        if not find_res or not find_res.group(1):
            raise ValueError("从HTML中解析视频信息失败")

        # 解析JSON数据
        json_data = json.loads(find_res.group(1).strip())
        VIDEO_ID_PAGE_KEY = "video_(id)/page"
        NOTE_ID_PAGE_KEY = "note_(id)/page"
        
        if VIDEO_ID_PAGE_KEY in json_data["loaderData"]:
            original_video_info = json_data["loaderData"][VIDEO_ID_PAGE_KEY]["videoInfoRes"]
        elif NOTE_ID_PAGE_KEY in json_data["loaderData"]:
            original_video_info = json_data["loaderData"][NOTE_ID_PAGE_KEY]["videoInfoRes"]
        else:
            raise Exception("无法从JSON中解析视频或图集信息")

        data = original_video_info["item_list"][0]

        # 获取视频信息
        video_url = data["video"]["play_addr"]["url_list"][0].replace("playwm", "play")
        desc = data.get("desc", "").strip() or f"douyin_{video_id}"
        
        # 替换文件名中的非法字符
        desc = re.sub(r'[\\/:*?"<>|]', '_', desc)
        
        return {
            "url": video_url,
            "title": desc,
            "video_id": video_id
        }
    
    async def download_video(self, video_info: dict, ctx: Context) -> Path:
        """异步下载视频到临时目录"""
        filename = f"{video_info['video_id']}.mp4"
        filepath = self.temp_dir / filename
        
        ctx.info(f"正在下载视频: {video_info['title']}")
        
        response = requests.get(video_info['url'], headers=HEADERS, stream=True)
        response.raise_for_status()
        
        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))
        
        # 异步下载文件，显示进度
        with open(filepath, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = downloaded / total_size
                        await ctx.report_progress(downloaded, total_size)
        
        ctx.info(f"视频下载完成: {filepath}")
        return filepath
    
    def extract_audio(self, video_path: Path) -> Path:
        """从视频文件中提取音频"""
        audio_path = video_path.with_suffix('.mp3')
        
        try:
            (
                ffmpeg
                .input(str(video_path))
                .output(str(audio_path), acodec='libmp3lame', q=0)
                .run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
            )
            return audio_path
        except Exception as e:
            raise Exception(f"提取音频时出错: {str(e)}")
    
    def extract_text_from_video_url(self, video_url: str) -> str:
        """从视频URL中提取文字（使用阿里云百炼API）"""
        try:
            # 发起异步转录任务
            task_response = dashscope.audio.asr.Transcription.async_call(
                model=self.model,
                file_urls=[video_url],
                language_hints=['zh', 'en']
            )
            
            # 等待转录完成
            transcription_response = dashscope.audio.asr.Transcription.wait(
                task=task_response.output.task_id
            )
            
            if transcription_response.status_code == HTTPStatus.OK:
                # 获取转录结果
                for transcription in transcription_response.output['results']:
                    if 'transcription_url' in transcription:
                        url = transcription['transcription_url']
                        result = json.loads(request.urlopen(url).read().decode('utf8'))

                        # 保存结果到临时文件
                        temp_json_path = self.temp_dir / 'transcription.json'
                        with open(temp_json_path, 'w') as f:
                            json.dump(result, f, indent=4, ensure_ascii=False)

                        # 提取文本内容
                        if 'transcripts' in result and len(result['transcripts']) > 0:
                            return result['transcripts'][0]['text']
                        else:
                            return "未识别到文本内容"
                    else:
                        # 检查是否有错误信息
                        if transcription.get('code') == 'SUCCESS_WITH_NO_VALID_FRAGMENT':
                            return "视频中未检测到有效的音频内容，可能原因：视频过短、无音频、格式不支持"
                        elif transcription.get('subtask_status') == 'FAILED':
                            return f"语音识别失败: {transcription.get('message', '未知错误')}"
                        else:
                            return f"API响应异常: {transcription}"

            else:
                raise Exception(f"转录失败: {transcription_response.output.message}")
                
        except Exception as e:
            raise Exception(f"提取文字时出错: {str(e)}")
    
    def cleanup_files(self, *file_paths: Path):
        """清理指定的文件"""
        for file_path in file_paths:
            if file_path.exists():
                file_path.unlink()


class XiaohongshuProcessor:
    """小红书内容处理器"""
    
    def __init__(self, api_key: Optional[str] = None):
        # 小红书处理不需要API密钥（除非需要语音识别）
        self.api_key = api_key or CONFIG.get("api_key", "")
        self.temp_dir = Path(tempfile.mkdtemp())
        if self.api_key:
            dashscope.api_key = self.api_key
    
    def __del__(self):
        """清理临时目录"""
        import shutil
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def remove_watermark_from_image_url(self, image_url: str) -> str:
        """去除图片URL中的水印参数，获取无水印图片"""
        if not image_url:
            return image_url
        
        original_url = image_url
        
        # 处理方式1: 移除 !h5_1080jpg 等水印标记
        # 例如: .../xxx!h5_1080jpg -> .../xxx.jpg
        if '!h5_' in image_url:
            # 找到 !h5_ 的位置，保留前面的部分
            parts = image_url.split('!h5_')
            if len(parts) > 1:
                base_part = parts[0]
                # 确保有文件扩展名
                if not base_part.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    # 尝试从原始URL中提取扩展名
                    if 'jpg' in original_url.lower():
                        image_url = base_part + '.jpg'
                    elif 'png' in original_url.lower():
                        image_url = base_part + '.png'
                    else:
                        image_url = base_part + '.jpg'
                else:
                    image_url = base_part
        
        # 处理方式2: 移除尺寸参数 @r_xxxw_xxxh
        # 例如: .../xxx@r_320w_320h.jpg -> .../xxx.jpg
        if '@r_' in image_url:
            image_url = re.sub(r'@r_\d+w_\d+h', '', image_url)
        
        # 处理方式3: 对于 ci.xiaohongshu.com 的图片
        # 尝试获取原图（移除尺寸限制）
        if 'ci.xiaohongshu.com' in image_url and '@' in image_url:
            match = re.search(r'/([a-f0-9-]+)@', image_url)
            if match:
                image_id = match.group(1)
                # 尝试原图URL（不带尺寸参数）
                image_url = f"https://ci.xiaohongshu.com/{image_id}.jpg"
        
        # 处理方式4: 对于 sns-webpic 的图片，保留完整路径但移除水印参数
        if 'sns-webpic' in image_url:
            # 移除 !h5_ 参数但保留完整路径
            if '!h5_' in image_url:
                # 找到最后一个 / 和 !h5_ 之间的内容
                parts = image_url.split('!h5_')
                if len(parts) > 1:
                    base = parts[0]
                    # 确保有扩展名
                    if not base.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        # 从原始URL提取文件名部分
                        filename_match = re.search(r'/([^/]+)!h5_', original_url)
                        if filename_match:
                            filename = filename_match.group(1)
                            # 移除可能的其他参数，保留基础文件名
                            filename = re.sub(r'@[^/]+', '', filename)
                            # 构建新URL
                            path_match = re.search(r'(https?://[^/]+/.+/)', original_url)
                            if path_match:
                                image_url = path_match.group(1) + filename + '.jpg'
                        else:
                            image_url = base + '.jpg'
                    else:
                        image_url = base
        
        return image_url
    
    def parse_share_url(self, share_text: str) -> dict:
        """从分享文本中提取小红书笔记信息"""
        # 提取分享链接
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', share_text)
        if not urls:
            raise ValueError("未找到有效的小红书分享链接")
        
        share_url = urls[0]
        
        # 如果是短链接（xhslink.com），先获取真实链接
        if 'xhslink.com' in share_url or 'xhslink.com' in share_url:
            try:
                response = requests.get(share_url, headers=HEADERS, allow_redirects=True, timeout=10)
                share_url = response.url
            except Exception as e:
                raise ValueError(f"无法解析短链接: {str(e)}")
        
        # 提取笔记ID - 支持多种格式
        note_id = None
        
        # 格式1: /explore/{note_id}
        note_id_match = re.search(r'/explore/([a-zA-Z0-9]+)', share_url)
        if note_id_match:
            note_id = note_id_match.group(1)
        
        # 格式2: /note/{note_id}
        if not note_id:
            note_id_match = re.search(r'/note/([a-zA-Z0-9]+)', share_url)
            if note_id_match:
                note_id = note_id_match.group(1)
        
        # 格式3: /discovery/item/{note_id}
        if not note_id:
            note_id_match = re.search(r'/discovery/item/([a-zA-Z0-9]+)', share_url)
            if note_id_match:
                note_id = note_id_match.group(1)
        
        # 格式4: 从URL参数中提取
        if not note_id:
            parsed_url = parse.urlparse(share_url)
            if 'noteId' in parse.parse_qs(parsed_url.query):
                note_id = parse.parse_qs(parsed_url.query)['noteId'][0]
        
        if not note_id:
            raise ValueError(f"无法从小红书链接中提取笔记ID: {share_url}")
        
        # 使用第三方API或直接解析（这里使用模拟方式）
        # 实际实现中可以使用官方API或第三方解析服务
        try:
            # 尝试使用第三方解析API（示例）
            # 注意：实际使用时需要替换为真实的API端点
            return self._parse_note_content(note_id, share_url)
        except Exception as e:
            # 如果API失败，尝试网页解析
            return self._parse_note_from_web(share_url, note_id)
    
    def _parse_note_content(self, note_id: str, share_url: str) -> dict:
        """解析小红书笔记内容（使用API方式）"""
        # 这里可以使用第三方解析API，如BugPK等
        # 示例实现
        try:
            # 第三方API调用示例（需要替换为真实API）
            api_url = f"https://api.example.com/xhs/note/{note_id}"
            response = requests.get(api_url, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "note_id": note_id,
                    "title": data.get("title", ""),
                    "desc": data.get("desc", ""),
                    "video_url": data.get("video_url", ""),
                    "images": data.get("images", []),
                    "author": data.get("author", {}),
                    "type": "video" if data.get("video_url") else "image",
                    "tags": data.get("tags", []),
                    "metrics": {
                        "likes": data.get("liked_count", 0),
                        "comments": data.get("comment_count", 0),
                        "collected": data.get("collected_count", 0)
                    }
                }
        except:
            pass
        
        # 如果API失败，抛出异常使用网页解析
        raise Exception("API解析失败，尝试网页解析")
    
    def _parse_note_from_web(self, share_url: str, note_id: str) -> dict:
        """从网页解析小红书笔记内容"""
        try:
            # 访问分享链接获取重定向后的真实URL
            response = requests.get(share_url, headers=HEADERS, allow_redirects=True, timeout=15)
            response.raise_for_status()
            
            final_url = response.url
            html_content = response.text
            
            # 解析HTML内容
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取标题 - 多种方式尝试
            title = ""
            # 方式1: og:title
            title_tag = soup.find('meta', property='og:title')
            if title_tag:
                title = title_tag.get('content', '').strip()
            
            # 方式2: title标签
            if not title:
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()
            
            # 方式3: 从script标签中的JSON数据提取 - 增强版
            if not title:
                script_tags = soup.find_all('script')
                all_titles = []
                
                for script in script_tags:
                    script_text = script.string
                    if script_text and ('title' in script_text.lower() or 'note' in script_text.lower()):
                        try:
                            # 方式3.1: 从JSON对象中提取
                            if '__INITIAL_STATE__' in script_text or 'noteDetail' in script_text:
                                json_match = re.search(r'\{.*"note".*\}', script_text, re.DOTALL)
                                if json_match:
                                    data = json.loads(json_match.group(0))
                                    if 'note' in data:
                                        note_title = data['note'].get('title', '')
                                        if note_title and len(note_title) > 3:
                                            all_titles.append(note_title)
                            
                            # 方式3.2: 直接搜索title字段
                            title_matches = re.findall(r'"title"\s*:\s*"([^"]+)"', script_text)
                            for match in title_matches:
                                clean_title = match.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
                                if len(clean_title) > 3 and clean_title not in all_titles:
                                    all_titles.append(clean_title)
                        except:
                            pass
                
                # 选择最合适的标题（优先选择较长的，过滤掉"小红书"等默认值）
                if all_titles:
                    valid_titles = [t for t in all_titles if len(t) > 5 and t.strip() != '小红书']
                    if valid_titles:
                        title = max(valid_titles, key=len)
                    elif all_titles:
                        title = all_titles[0]
            
            # 提取描述 - 多种方式尝试
            desc = ""
            # 方式1: og:description
            desc_tag = soup.find('meta', property='og:description')
            if desc_tag:
                desc = desc_tag.get('content', '').strip()
            
            # 方式2: description meta
            if not desc:
                desc_tag = soup.find('meta', attrs={'name': 'description'})
                if desc_tag:
                    desc = desc_tag.get('content', '').strip()
            
            # 方式3: 从script标签中的JSON数据提取 - 增强版
            if not desc:
                script_tags = soup.find_all('script')
                all_descs = []
                
                for script in script_tags:
                    script_text = script.string
                    if script_text and ('desc' in script_text.lower() or 'note' in script_text.lower()):
                        try:
                            # 方式3.1: 从JSON对象中提取
                            if '__INITIAL_STATE__' in script_text or 'noteDetail' in script_text:
                                json_match = re.search(r'\{.*"note".*\}', script_text, re.DOTALL)
                                if json_match:
                                    data = json.loads(json_match.group(0))
                                    if 'note' in data:
                                        note_desc = data['note'].get('desc', '') or data['note'].get('description', '')
                                        if note_desc and len(note_desc) > 20:
                                            all_descs.append(note_desc)
                            
                            # 方式3.2: 直接搜索desc字段（处理转义字符）
                            desc_matches = re.findall(r'"desc"\s*:\s*"((?:[^"\\\\]|\\\\.)+)"', script_text)
                            for match in desc_matches:
                                # 处理转义字符
                                clean_desc = match.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
                                if len(clean_desc) > 20 and clean_desc not in all_descs:
                                    all_descs.append(clean_desc)
                            
                            # 方式3.3: 搜索简单格式的desc
                            simple_desc_matches = re.findall(r'"desc"\s*:\s*"([^"]+)"', script_text)
                            for match in simple_desc_matches:
                                if len(match) > 20 and match not in all_descs:
                                    all_descs.append(match)
                        except:
                            pass
                
                # 选择最长的描述（通常是最完整的）
                if all_descs:
                    desc = max(all_descs, key=len)
            
            # 提取图片 - 改进提取逻辑
            images = []
            raw_images = []  # 保存原始图片URL
            
            # 方式1: og:image
            img_tag = soup.find('meta', property='og:image')
            if img_tag:
                img_url = img_tag.get('content', '')
                if img_url:
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    raw_images.append(img_url)
            
            # 方式2: 从所有img标签提取
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if src:
                    # 过滤掉无效图片
                    if any(keyword in src for keyword in ['sns-web', 'xingyun', 'xhslink', 'xiaohongshu']):
                        if src.startswith('//'):
                            src = 'https:' + src
                        if src not in raw_images:
                            raw_images.append(src)
            
            # 方式3: 从script中的JSON提取图片列表
            if not raw_images:
                script_tags = soup.find_all('script')
                for script in script_tags:
                    script_text = script.string
                    if script_text and 'image' in script_text.lower():
                        try:
                            if '__INITIAL_STATE__' in script_text or 'noteDetail' in script_text:
                                json_match = re.search(r'\{.*"note".*\}', script_text, re.DOTALL)
                                if json_match:
                                    data = json.loads(json_match.group(0))
                                    if 'note' in data and 'images' in data['note']:
                                        raw_images = data['note']['images']
                                        break
                        except:
                            pass
            
            # 处理图片URL，去除水印
            for img_url in raw_images:
                clean_url = self.remove_watermark_from_image_url(img_url)
                if clean_url and clean_url not in images:
                    images.append(clean_url)
            
            # 提取视频URL - 增强提取逻辑
            video_url = ""
            
            # 方式1: video标签
            video_tag = soup.find('video')
            if video_tag:
                video_url = video_tag.get('src') or video_tag.get('data-src') or video_tag.get('data-video-url', '')
            
            # 方式2: og:video
            if not video_url:
                video_tag = soup.find('meta', property='og:video')
                if video_tag:
                    video_url = video_tag.get('content', '')
            
            # 方式3: 从script中的JSON提取 - 增强搜索
            if not video_url:
                script_tags = soup.find_all('script')
                for script in script_tags:
                    script_text = script.string
                    if script_text and ('video' in script_text.lower() or 'media' in script_text.lower()):
                        try:
                            # 尝试多种JSON格式
                            # 格式1: window.__INITIAL_STATE__
                            if '__INITIAL_STATE__' in script_text:
                                json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script_text, re.DOTALL)
                                if json_match:
                                    data = json.loads(json_match.group(1))
                                    # 递归查找video字段
                                    def find_video_url(obj):
                                        if isinstance(obj, dict):
                                            if 'video' in obj:
                                                video_obj = obj['video']
                                                if isinstance(video_obj, dict):
                                                    return video_obj.get('url') or video_obj.get('videoUrl') or video_obj.get('src')
                                            if 'media' in obj:
                                                media_obj = obj['media']
                                                if isinstance(media_obj, dict):
                                                    return media_obj.get('videoUrl') or media_obj.get('url')
                                            for value in obj.values():
                                                result = find_video_url(value)
                                                if result:
                                                    return result
                                        elif isinstance(obj, list):
                                            for item in obj:
                                                result = find_video_url(item)
                                                if result:
                                                    return result
                                        return None
                                    
                                    video_url = find_video_url(data)
                                    if video_url:
                                        break
                            
                            # 格式2: noteDetail 或其他格式
                            if not video_url:
                                # 搜索包含video的JSON对象
                                json_matches = re.findall(r'\{[^{}]*"video"[^{}]*\}', script_text)
                                for match in json_matches:
                                    try:
                                        data = json.loads(match)
                                        if 'video' in data:
                                            video_obj = data['video']
                                            if isinstance(video_obj, dict):
                                                video_url = video_obj.get('url') or video_obj.get('videoUrl') or video_obj.get('src')
                                            elif isinstance(video_obj, str):
                                                video_url = video_obj
                                            if video_url:
                                                break
                                    except:
                                        continue
                            
                            # 格式3: 搜索masterUrl字段（小红书视频常用）
                            if not video_url:
                                # 搜索包含masterUrl的JSON
                                master_url_match = re.search(r'"masterUrl"\s*:\s*"([^"]+)"', script_text)
                                if master_url_match:
                                    video_url = master_url_match.group(1)
                                    # 处理Unicode转义字符
                                    video_url = video_url.replace('\\u002F', '/').replace('\\/', '/')
                                    if video_url:
                                        break
                            
                            # 格式4: 直接搜索视频URL模式
                            if not video_url:
                                # 搜索常见的视频URL模式
                                video_url_patterns = [
                                    r'https?://[^"\s]+\.mp4[^"\s]*',
                                    r'https?://[^"\s]+video[^"\s]+',
                                    r'https?://[^"\s]+xhscdn[^"\s]+video[^"\s]+',
                                    r'https?://[^"\s]+sns-video[^"\s]+',
                                ]
                                for pattern in video_url_patterns:
                                    matches = re.findall(pattern, script_text)
                                    if matches:
                                        # 过滤掉明显不是视频的URL
                                        for match in matches:
                                            if any(ext in match.lower() for ext in ['.mp4', 'video', 'media', 'stream']):
                                                video_url = match
                                                break
                                    if video_url:
                                        break
                        except Exception as e:
                            pass
            
            # 判断类型
            note_type = "video" if video_url else "image"
            
            # 提取作者信息
            author_name = ""
            author_id = ""
            author_tag = soup.find('meta', property='og:site_name')
            if author_tag:
                author_name = author_tag.get('content', '')
            
            # 提取标签
            tags = []
            # 从描述中提取标签（#标签#格式）
            if desc:
                tag_matches = re.findall(r'#([^#]+)#', desc)
                tags = tag_matches
            
            return {
                "note_id": note_id,
                "title": title or f"小红书笔记_{note_id}",
                "desc": desc,
                "video_url": video_url,
                "images": images[:9] if images else [],  # 最多返回9张图片
                "author": {
                    "name": author_name,
                    "id": author_id
                },
                "type": note_type,
                "tags": tags,
                "metrics": {
                    "likes": 0,
                    "comments": 0,
                    "collected": 0
                }
            }
        except Exception as e:
            raise Exception(f"解析小红书笔记失败: {str(e)}")
    
    def extract_text_from_video_url(self, video_url: str) -> str:
        """从视频URL中提取文字（使用阿里云百炼API）"""
        if not self.api_key:
            raise ValueError("需要API密钥才能提取视频文本")
        
        try:
            # 发起异步转录任务
            task_response = dashscope.audio.asr.Transcription.async_call(
                model=CONFIG.get("model", DEFAULT_MODEL),
                file_urls=[video_url],
                language_hints=['zh', 'en']
            )
            
            # 等待转录完成
            transcription_response = dashscope.audio.asr.Transcription.wait(
                task=task_response.output.task_id
            )
            
            if transcription_response.status_code == HTTPStatus.OK:
                for transcription in transcription_response.output['results']:
                    if 'transcription_url' in transcription:
                        url = transcription['transcription_url']
                        result = json.loads(request.urlopen(url).read().decode('utf8'))
                        
                        if 'transcripts' in result and len(result['transcripts']) > 0:
                            return result['transcripts'][0]['text']
                        else:
                            return "未识别到文本内容"
                    else:
                        if transcription.get('code') == 'SUCCESS_WITH_NO_VALID_FRAGMENT':
                            return "视频中未检测到有效的音频内容"
                        elif transcription.get('subtask_status') == 'FAILED':
                            return f"语音识别失败: {transcription.get('message', '未知错误')}"
                        else:
                            return f"API响应异常: {transcription}"
            else:
                raise Exception(f"转录失败: {transcription_response.output.message}")
        except Exception as e:
            raise Exception(f"提取文字时出错: {str(e)}")


@mcp.tool()
def get_douyin_download_link(share_link: str) -> str:
    """
    获取抖音视频的无水印下载链接

    参数:
    - share_link: 抖音分享链接或包含链接的文本

    返回:
    - 包含下载链接和视频信息的JSON字符串
    """
    try:
        # 获取下载链接不需要API密钥，直接创建解析器
        processor = DouyinProcessor.__new__(DouyinProcessor)
        processor.temp_dir = Path(tempfile.mkdtemp())
        video_info = processor.parse_share_url(share_link)
        
        return json.dumps({
            "status": "success",
            "video_id": video_info["video_id"],
            "title": video_info["title"],
            "download_url": video_info["url"],
            "description": f"视频标题: {video_info['title']}",
            "usage_tip": "可以直接使用此链接下载无水印视频"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"获取下载链接失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
async def extract_douyin_text(
    share_link: str,
    model: Optional[str] = None,
    ctx: Context = None
) -> str:
    """
    从抖音分享链接提取视频中的文本内容

    参数:
    - share_link: 抖音分享链接或包含链接的文本
    - model: 语音识别模型（可选，默认使用paraformer-v2）

    返回:
    - 提取的文本内容

    注意: 需要在config.json中配置API密钥
    """
    try:
        processor = DouyinProcessor(model=model)
        
        # 解析视频链接
        if ctx:
            ctx.info("正在解析抖音分享链接...")
        video_info = processor.parse_share_url(share_link)

        # 直接使用视频URL进行文本提取
        if ctx:
            ctx.info("正在从视频中提取文本...")
        text_content = processor.extract_text_from_video_url(video_info['url'])

        if ctx:
            ctx.info("文本提取完成!")
        return text_content

    except Exception as e:
        if ctx:
            ctx.error(f"处理过程中出现错误: {str(e)}")
        raise Exception(f"提取抖音视频文本失败: {str(e)}")


@mcp.tool()
def parse_douyin_video_info(share_link: str) -> str:
    """
    解析抖音分享链接，获取视频基本信息

    参数:
    - share_link: 抖音分享链接或包含链接的文本

    返回:
    - 视频信息（JSON格式字符串）
    """
    try:
        # 解析视频信息不需要API密钥，直接创建解析器
        processor = DouyinProcessor.__new__(DouyinProcessor)
        processor.temp_dir = Path(tempfile.mkdtemp())
        video_info = processor.parse_share_url(share_link)
        
        return json.dumps({
            "video_id": video_info["video_id"],
            "title": video_info["title"],
            "download_url": video_info["url"],
            "status": "success"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, ensure_ascii=False, indent=2)


@mcp.resource("douyin://video/{video_id}")
def get_video_info(video_id: str) -> str:
    """
    获取指定视频ID的详细信息

    参数:
    - video_id: 抖音视频ID

    返回:
    - 视频详细信息
    """
    share_url = f"https://www.iesdouyin.com/share/video/{video_id}"
    try:
        processor = DouyinProcessor.__new__(DouyinProcessor)
        processor.temp_dir = Path(tempfile.mkdtemp())
        video_info = processor.parse_share_url(share_url)
        return json.dumps(video_info, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取视频信息失败: {str(e)}"


# ==================== 小红书相关工具 ====================

@mcp.tool()
def get_xiaohongshu_content(share_link: str) -> str:
    """
    获取小红书笔记的完整内容（视频/图文）

    参数:
    - share_link: 小红书分享链接或包含链接的文本

    返回:
    - 包含视频链接、文案、图片等完整信息的JSON字符串
    """
    try:
        processor = XiaohongshuProcessor()
        note_info = processor.parse_share_url(share_link)
        
        return json.dumps({
            "status": "success",
            "note_id": note_info.get("note_id", ""),
            "title": note_info.get("title", ""),
            "description": note_info.get("desc", ""),
            "type": note_info.get("type", "unknown"),  # video 或 image
            "video_url": note_info.get("video_url", ""),
            "images": note_info.get("images", []),
            "images_no_watermark": note_info.get("images", []),  # 无水印图片（已处理）
            "author": note_info.get("author", {}),
            "tags": note_info.get("tags", []),
            "metrics": note_info.get("metrics", {}),
            "usage_tip": "images数组已去除水印参数，可以直接下载无水印图片"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"获取小红书内容失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
def extract_xiaohongshu_text(share_link: str) -> str:
    """
    提取小红书笔记的文案内容

    参数:
    - share_link: 小红书分享链接或包含链接的文本

    返回:
    - 笔记的文案内容（纯文本）
    """
    try:
        processor = XiaohongshuProcessor()
        note_info = processor.parse_share_url(share_link)
        
        # 组合标题和描述
        text_content = ""
        if note_info.get("title"):
            text_content += f"标题: {note_info['title']}\n\n"
        if note_info.get("desc"):
            text_content += note_info['desc']
        
        # 如果有标签，也加上
        if note_info.get("tags"):
            text_content += f"\n\n标签: {', '.join(note_info['tags'])}"
        
        return text_content if text_content else "未找到文案内容"
        
    except Exception as e:
        return f"提取小红书文案失败: {str(e)}"


@mcp.tool()
async def extract_xiaohongshu_video_text(
    share_link: str,
    model: Optional[str] = None,
    ctx: Context = None
) -> str:
    """
    从小红书视频笔记中提取语音文本内容

    参数:
    - share_link: 小红书分享链接或包含链接的文本
    - model: 语音识别模型（可选，默认使用paraformer-v2）

    返回:
    - 提取的文本内容

    注意: 需要在config.json中配置API密钥
    """
    try:
        processor = XiaohongshuProcessor()
        
        # 解析笔记信息
        if ctx:
            ctx.info("正在解析小红书分享链接...")
        note_info = processor.parse_share_url(share_link)
        
        # 检查是否有视频
        video_url = note_info.get("video_url")
        if not video_url:
            return "该笔记不是视频类型，无法提取语音内容"
        
        # 提取视频文本
        if ctx:
            ctx.info("正在从视频中提取文本...")
        text_content = processor.extract_text_from_video_url(video_url)
        
        # 如果有文案，也加上
        desc = note_info.get("desc", "")
        if desc:
            text_content = f"文案内容: {desc}\n\n语音内容: {text_content}"
        
        if ctx:
            ctx.info("文本提取完成!")
        return text_content
        
    except Exception as e:
        if ctx:
            ctx.error(f"处理过程中出现错误: {str(e)}")
        raise Exception(f"提取小红书视频文本失败: {str(e)}")


@mcp.tool()
def get_xiaohongshu_images(share_link: str) -> str:
    """
    获取小红书笔记中的所有图片链接

    参数:
    - share_link: 小红书分享链接或包含链接的文本

    返回:
    - 图片链接列表（JSON格式）
    """
    try:
        processor = XiaohongshuProcessor()
        note_info = processor.parse_share_url(share_link)
        
        images = note_info.get("images", [])
        
        return json.dumps({
            "status": "success",
            "note_id": note_info.get("note_id", ""),
            "title": note_info.get("title", ""),
            "image_count": len(images),
            "images": images,
            "usage_tip": "图片链接已去除水印参数，可以直接下载无水印图片"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"获取图片失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@mcp.resource("xiaohongshu://note/{note_id}")
def get_xiaohongshu_note_info(note_id: str) -> str:
    """
    获取指定笔记ID的详细信息

    参数:
    - note_id: 小红书笔记ID

    返回:
    - 笔记详细信息
    """
    share_url = f"https://www.xiaohongshu.com/explore/{note_id}"
    try:
        processor = XiaohongshuProcessor()
        note_info = processor.parse_share_url(share_url)
        return json.dumps(note_info, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取笔记信息失败: {str(e)}"


@mcp.prompt()
def douyin_text_extraction_guide() -> str:
    """抖音视频文本提取使用指南"""
    return """
# 抖音视频文本提取使用指南

## 功能说明
这个MCP服务器可以从抖音分享链接中提取视频的文本内容，以及获取无水印下载链接。

## 环境变量配置
请确保设置了以下环境变量：
- `DASHSCOPE_API_KEY`: 阿里云百炼API密钥

## 使用步骤
1. 复制抖音视频的分享链接
2. 在Claude Desktop配置中设置环境变量 DASHSCOPE_API_KEY
3. 使用相应的工具进行操作

## 工具说明
- `extract_douyin_text`: 完整的文本提取流程（需要API密钥）
- `get_douyin_download_link`: 获取无水印视频下载链接（无需API密钥）
- `parse_douyin_video_info`: 仅解析视频基本信息
- `douyin://video/{video_id}`: 获取指定视频的详细信息

## Claude Desktop 配置示例
```json
{
  "mcpServers": {
    "douyin-mcp": {
      "command": "uvx",
      "args": ["douyin-mcp-server"],
      "env": {
        "DASHSCOPE_API_KEY": "your-dashscope-api-key-here"
      }
    }
  }
}
```

## 注意事项
- 需要提供有效的阿里云百炼API密钥（通过环境变量）
- 使用阿里云百炼的paraformer-v2模型进行语音识别
- 支持大部分抖音视频格式
- 获取下载链接无需API密钥
"""


def main():
    """启动MCP服务器"""
    mcp.run()


if __name__ == "__main__":
    main()