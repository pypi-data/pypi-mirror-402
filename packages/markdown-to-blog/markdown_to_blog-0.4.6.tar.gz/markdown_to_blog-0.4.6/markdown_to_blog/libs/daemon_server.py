"""
ZeroMQ 기반 Daemon 서버 구현

모든 CLI 명령어를 원격에서 실행할 수 있도록 구현합니다.
"""

import json
import sys
import signal
import os
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime, timedelta, timezone

import zmq
from loguru import logger
import click

from markdown_to_blog.libs.blogger import (
    check_config,
    get_blogger_service,
    get_blogid,
    get_datetime_after,
    get_datetime_after_hour,
    set_blogid,
    list_my_blogs,
    set_client_secret,
    upload_html_to_blogspot,
    upload_to_blogspot,
    get_all_posts,
    update_post,
    delete_post,
    DEFAULT_MARKDOWN_EXTRAS,
)
from markdown_to_blog.libs.markdown import convert, read_first_header_from_md, upload_markdown_images
from markdown_to_blog.libs.image_uploader import ImageUploader
from markdown_to_blog.libs.web_to_markdown import fetch_html_with_playwright, convert_html_to_markdown, HTMLFetchError
from cryptography.fernet import Fernet
import base64
import hashlib
from markdown2 import Markdown


class DaemonServer:
    """ZeroMQ 기반 Daemon 서버"""
    
    def __init__(self, bind_address: str = "tcp://127.0.0.1:5555"):
        self.bind_address = bind_address
        self.context = None
        self.socket = None
        self.running = False
        self.start_time = datetime.now()
        
    def start(self):
        """Daemon 서버 시작"""
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)  # REP: Reply socket
        self.socket.bind(self.bind_address)
        self.running = True
        
        logger.info(f"Daemon 서버가 시작되었습니다: {self.bind_address}")
        
        # 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            while self.running:
                # 메시지 수신
                message = self.socket.recv_string()
                logger.debug(f"메시지 수신: {message}")
                
                try:
                    request = json.loads(message)
                    response = self._handle_request(request)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 파싱 오류: {e}")
                    response = self._create_error_response(uuid4().hex, "Invalid JSON format")
                except Exception as e:
                    logger.error(f"요청 처리 오류: {e}")
                    response = self._create_error_response(
                        request.get("id", uuid4().hex) if isinstance(request, dict) else uuid4().hex,
                        str(e)
                    )
                
                # 응답 전송
                self.socket.send_string(json.dumps(response))
                
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중지되었습니다.")
        finally:
            self.stop()
    
    def stop(self):
        """Daemon 서버 중지"""
        logger.info("Daemon 서버를 중지합니다...")
        self.running = False
        
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        
        logger.info("Daemon 서버가 중지되었습니다.")
    
    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        logger.info(f"시그널 {signum} 수신, 서버 종료 중...")
        self.stop()
        sys.exit(0)
    
    def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """요청 처리"""
        request_id = request.get("id", uuid4().hex)
        command = request.get("command")
        params = request.get("params", {})
        
        if not command:
            return self._create_error_response(request_id, "Command is required")
        
        # 명령어 핸들러 호출
        handler = self._get_command_handler(command)
        if not handler:
            return self._create_error_response(request_id, f"Unknown command: {command}")
        
        try:
            result = handler(params)
            return self._create_success_response(request_id, result)
        except Exception as e:
            logger.exception(f"명령어 실행 오류: {command}")
            return self._create_error_response(request_id, str(e))
    
    def _get_command_handler(self, command: str):
        """명령어 핸들러 반환"""
        handlers = {
            "ping": self._handle_ping,
            "shutdown": self._handle_shutdown,
            "set_blogid": self._handle_set_blogid,
            "get_blogid": self._handle_get_blogid,
            "list_my_blogs": self._handle_list_my_blogs,
            "convert": self._handle_convert,
            "refresh_auth": self._handle_refresh_auth,
            "set_client_secret": self._handle_set_client_secret,
            "encode_secret": self._handle_encode_secret,
            "decode_secret": self._handle_decode_secret,
            "backup_posting": self._handle_backup_posting,
            "sync_posting": self._handle_sync_posting,
            "update_posting": self._handle_update_posting,
            "delete_posting": self._handle_delete_posting,
            "save_as_markdown": self._handle_save_as_markdown,
            "publish": self._handle_publish,
            "publish_html": self._handle_publish_html,
            "upload_image": self._handle_upload_image,
            "upload_images": self._handle_upload_images,
            "publish_folder": self._handle_publish_folder,
        }
        return handlers.get(command)
    
    def _create_success_response(self, request_id: str, data: Any = None) -> Dict[str, Any]:
        """성공 응답 생성"""
        return {
            "id": request_id,
            "status": "success",
            "data": data
        }
    
    def _create_error_response(self, request_id: str, error: str) -> Dict[str, Any]:
        """에러 응답 생성"""
        return {
            "id": request_id,
            "status": "error",
            "error": error
        }
    
    # 명령어 핸들러들
    def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """ping 핸들러 - 서버 상태 확인"""
        uptime = datetime.now() - self.start_time
        return {
            "message": "pong",
            "uptime": str(uptime),
            "server_address": self.bind_address
        }
    
    def _handle_shutdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """shutdown 핸들러 - 서버 종료"""
        self.running = False
        return {"message": "Daemon server shutting down..."}
    
    def _handle_set_blogid(self, params: Dict[str, Any]) -> Dict[str, Any]:
        blogid = params.get("blogid")
        if not blogid:
            raise ValueError("blogid is required")
        check_config()
        set_blogid(blogid)
        return {"message": f"블로그 ID가 설정되었습니다: {blogid}"}
    
    def _handle_get_blogid(self, params: Dict[str, Any]) -> Dict[str, Any]:
        check_config()
        blog_id = get_blogid()
        return {"blogid": blog_id}
    
    def _handle_list_my_blogs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        check_config()
        blogs = list_my_blogs()
        return {"blogs": blogs}
    
    def _handle_convert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_ = params.get("input")
        output_ = params.get("output")
        if not input_ or not output_:
            raise ValueError("input and output are required")
        convert(input_, output_)
        return {"message": f"변환 완료: {input_} -> {output_}"}
    
    def _handle_refresh_auth(self, params: Dict[str, Any]) -> Dict[str, Any]:
        sys.argv = ["mdb", "--noauth_local_webserver"]
        get_blogger_service()
        return {"message": "인증 정보가 갱신되었습니다"}
    
    def _handle_set_client_secret(self, params: Dict[str, Any]) -> Dict[str, Any]:
        filename = params.get("filename")
        if not filename:
            raise ValueError("filename is required")
        set_client_secret(filename)
        return {"message": f"클라이언트 시크릿 파일이 설정되었습니다: {filename}"}
    
    def _handle_encode_secret(self, params: Dict[str, Any]) -> Dict[str, Any]:
        client_secret_path = params.get("client_secret_path")
        output_path = params.get("output_path")
        key = params.get("key")
        if not all([client_secret_path, output_path, key]):
            raise ValueError("client_secret_path, output_path, and key are required")
        
        derived_key = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
        fernet = Fernet(derived_key)
        
        with open(client_secret_path, "rb") as f:
            client_secret_content = f.read()
        
        encrypted_content = fernet.encrypt(client_secret_content)
        
        with open(output_path, "wb") as f:
            f.write(encrypted_content)
        
        return {"message": f"File '{client_secret_path}' encrypted to '{output_path}'"}
    
    def _handle_decode_secret(self, params: Dict[str, Any]) -> Dict[str, Any]:
        encoded_secret_path = params.get("encoded_secret_path")
        output_path = params.get("output_path")
        key = params.get("key")
        if not all([encoded_secret_path, output_path, key]):
            raise ValueError("encoded_secret_path, output_path, and key are required")
        
        derived_key = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
        fernet = Fernet(derived_key)
        
        with open(encoded_secret_path, "rb") as f:
            encrypted_content = f.read()
        
        decrypted_content = fernet.decrypt(encrypted_content)
        
        with open(output_path, "wb") as f:
            f.write(decrypted_content)
        
        return {"message": f"File '{encoded_secret_path}' decrypted to '{output_path}'"}
    
    def _handle_backup_posting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        blog_id = params.get("blog_id")
        target_dir = params.get("target_dir")
        if not blog_id or not target_dir:
            raise ValueError("blog_id and target_dir are required")
        
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        posts = get_all_posts(blog_id)
        if not posts:
            return {"message": "No posts found", "saved_count": 0}
        
        posts_info = {}
        saved_count = 0
        
        for post in posts:
            post_id = post.get("id")
            content = post.get("content")
            
            if not post_id or content is None:
                continue
            
            filename = f"post_{post_id}.html"
            file_path = target_dir / filename
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            hash_value = hashlib.sha256(content.encode('utf-8')).hexdigest()
            posts_info[post_id] = {"filename": filename, "hash": hash_value}
            saved_count += 1
        
        info_file_path = target_dir / "posting_info.json"
        with open(info_file_path, "w", encoding="utf-8") as f:
            json.dump(posts_info, f, indent=4, ensure_ascii=False)
        
        return {"message": "Backup complete", "saved_count": saved_count}
    
    def _handle_sync_posting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        blog_id = params.get("blog_id")
        posting_info_path = params.get("posting_info")
        target_dir = params.get("target_dir")
        if not all([blog_id, posting_info_path, target_dir]):
            raise ValueError("blog_id, posting_info, and target_dir are required")
        
        target_dir = Path(target_dir)
        posting_info_file = Path(posting_info_path)
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        local_posts_info = {}
        if posting_info_file.exists() and posting_info_file.stat().st_size > 0:
            with open(posting_info_file, "r", encoding="utf-8") as f:
                local_posts_info = json.load(f)
        
        remote_posts = get_all_posts(blog_id)
        if not remote_posts:
            with open(posting_info_file, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4, ensure_ascii=False)
            return {"message": "No remote posts found", "new_count": 0, "updated_count": 0}
        
        new_posts_count = 0
        updated_posts_count = 0
        updated_local_posts_info = {}
        
        for remote_post in remote_posts:
            post_id = remote_post.get("id")
            content = remote_post.get("content")
            
            if not post_id or content is None:
                continue
            
            remote_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            filename = f"post_{post_id}.html"
            
            local_entry = local_posts_info.get(post_id)
            
            if local_entry:
                if local_entry.get('hash') == remote_hash:
                    updated_local_posts_info[post_id] = local_entry.copy()
                    filename = local_entry.get('filename', filename)
                else:
                    filename = local_entry.get('filename', filename)
                    file_path = target_dir / filename
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    updated_local_posts_info[post_id] = {"filename": filename, "hash": remote_hash}
                    updated_posts_count += 1
            else:
                file_path = target_dir / filename
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                updated_local_posts_info[post_id] = {"filename": filename, "hash": remote_hash}
                new_posts_count += 1
        
        with open(posting_info_file, "w", encoding="utf-8") as f:
            json.dump(updated_local_posts_info, f, indent=4, ensure_ascii=False)
        
        return {"message": "Sync complete", "new_count": new_posts_count, "updated_count": updated_posts_count}
    
    def _handle_update_posting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        blog_id = params.get("blog_id")
        post_id = params.get("post_id")
        title = params.get("title")
        markdown_file_path = params.get("markdown_file_path")
        if not all([blog_id, post_id, title, markdown_file_path]):
            raise ValueError("blog_id, post_id, title, and markdown_file_path are required")
        
        md_file_path = Path(markdown_file_path)
        with open(md_file_path, "r", encoding="utf-8") as f:
            raw_markdown_content = f.read()
        
        markdowner = Markdown(extras=DEFAULT_MARKDOWN_EXTRAS)
        html_content = markdowner.convert(raw_markdown_content)
        
        labels_to_pass = params.get("labels")
        draft_option = params.get("draft", False)
        description_option = params.get("description")
        
        updated_post_data = update_post(
            blog_id=blog_id,
            post_id=post_id,
            title=title,
            html_content=html_content,
            is_draft=draft_option,
            labels=labels_to_pass,
            search_description=description_option,
        )
        
        return {"message": "Post updated successfully", "post_data": updated_post_data}
    
    def _handle_delete_posting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        blog_id = params.get("blog_id")
        post_id = params.get("post_id")
        if not blog_id or not post_id:
            raise ValueError("blog_id and post_id are required")
        
        delete_post(blog_id=blog_id, post_id=post_id)
        return {"message": f"Post {post_id} deleted successfully"}
    
    def _handle_save_as_markdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        url = params.get("url")
        output = params.get("output")
        if not url or not output:
            raise ValueError("url and output are required")
        
        start_comment = params.get("start_comment")
        end_comment = params.get("end_comment")
        
        html_content = fetch_html_with_playwright(
            url,
            start_comment=start_comment,
            end_comment=end_comment
        )
        
        markdown_content = convert_html_to_markdown(html_content)
        
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_content, encoding='utf-8')
        
        return {"message": f"Markdown saved to {output}"}
    
    def _handle_publish(self, params: Dict[str, Any]) -> Dict[str, Any]:
        filename = params.get("filename")
        if not filename:
            raise ValueError("filename is required")
        
        blog_id = params.get("blogid") or get_blogid()
        
        title = params.get("title")
        if not title:
            title = read_first_header_from_md(filename)
            if title is None:
                raise ValueError(f"title is None: {filename}")
            title = title.replace("# ", "")
        
        after_hour = params.get("after_hour")
        after = params.get("after", "now")
        
        datetime_string = (
            get_datetime_after_hour(after_hour)
            if after_hour is not None
            else get_datetime_after(after)
        )
        
        is_draft = params.get("is_draft", False)
        labels_list = params.get("labels")
        description = params.get("description")
        
        post_id = upload_to_blogspot(
            title,
            filename,
            blog_id,
            is_draft=is_draft,
            datetime_string=datetime_string,
            labels=labels_list,
            search_description=description,
        )
        
        return {"message": f"Post published successfully", "post_id": post_id}
    
    def _handle_publish_html(self, params: Dict[str, Any]) -> Dict[str, Any]:
        filename = params.get("filename")
        title = params.get("title")
        if not filename or not title:
            raise ValueError("filename and title are required")
        
        blog_id = params.get("blogid") or get_blogid()
        
        post_id = upload_html_to_blogspot(title, filename, blog_id)
        
        return {"message": f"HTML published successfully", "post_id": post_id}
    
    def _handle_upload_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        image_path = params.get("image_path")
        if not image_path:
            raise ValueError("image_path is required")
        
        service = params.get("service")
        uploader = ImageUploader(service=service)
        url = uploader.upload(image_path)
        
        return {"message": "Upload successful", "url": url}
    
    def _handle_upload_images(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_ = params.get("input")
        if not input_:
            raise ValueError("input is required")
        
        upload_markdown_images(input_)
        
        return {"message": "Images uploaded successfully"}
    
    def _handle_publish_folder(self, params: Dict[str, Any]) -> Dict[str, Any]:
        folder_path = params.get("folder_path")
        if not folder_path:
            raise ValueError("folder_path is required")
        
        blog_id = params.get("blogid") or get_blogid()
        interval = params.get("interval", 1)
        service = params.get("service")
        draft = params.get("draft", False)
        labels_list = params.get("labels")
        
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            raise ValueError(f"{folder_path}는 유효한 폴더가 아닙니다")
        
        seoul_timezone = timezone(timedelta(hours=9))
        current_dt = datetime.now(seoul_timezone)
        
        file_list = list(folder.glob("*.md"))
        if not file_list:
            return {"message": "No markdown files found", "success_count": 0}
        
        success_count = 0
        error_count = 0
        
        for idx, file in enumerate(file_list, 1):
            try:
                file_path = file.resolve()
                file_name = file.name
                file_title = read_first_header_from_md(file_path)
                
                if not file_title:
                    file_title = file.stem
                else:
                    file_title = file_title.replace("# ", "")
                
                target_dt = current_dt + timedelta(hours=interval * idx)
                datetime_string = target_dt.isoformat(timespec="seconds")
                
                upload_markdown_images(str(file_path))
                
                upload_to_blogspot(
                    file_title,
                    file_path,
                    blog_id,
                    is_draft=draft,
                    datetime_string=datetime_string,
                    labels=labels_list,
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Error processing file {file_name}: {str(e)}")
                error_count += 1
        
        return {
            "message": "Folder publishing complete",
            "success_count": success_count,
            "error_count": error_count
        }


def run_daemon_server(bind_address: str = "tcp://127.0.0.1:5555"):
    """Daemon 서버 실행"""
    server = DaemonServer(bind_address)
    try:
        server.start()
    except Exception as e:
        logger.error(f"Daemon 서버 실행 오류: {e}")
        sys.exit(1)

