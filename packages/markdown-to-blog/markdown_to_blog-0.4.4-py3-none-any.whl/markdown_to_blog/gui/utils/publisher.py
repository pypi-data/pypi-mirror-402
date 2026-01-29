import os
import asyncio
from pathlib import Path
from datetime import datetime, timedelta, timezone
from PySide6.QtCore import QThread, Signal
from loguru import logger

from ..models import Setting, PublishRecord
from ...libs.blogger import upload_to_blogspot, get_datetime_after_hour
from ...libs.markdown import read_first_header_from_md

# Import for convert functionality
try:
    from markdown_to_blog.libs.markdown import upload_markdown_images
except ImportError:
    # Fallback to relative import
    from ...libs.markdown import upload_markdown_images


class ConverterThread(QThread):
    """Convert markdown images by uploading them."""
    progress = Signal(str, int, int)  # message, current, total
    finished = Signal()
    
    def __init__(self, workspace, loop):
        super().__init__()
        self.workspace = workspace
        self.loop = loop
        self.is_running = True
        
    def run(self):
        """Convert markdown images"""
        try:
            # Get records that need conversion
            records_to_convert = self.loop.run_until_complete(
                self._get_records_to_convert()
            )
            
            total_records = len(records_to_convert)
            
            if total_records == 0:
                self.progress.emit("변환할 항목이 없습니다.", 0, 0)
                return
            
            self.progress.emit(f"총 {total_records}개 항목 변환 시작", 0, total_records)
            
            converted_count = 0
            failed_count = 0
            
            for record in records_to_convert:
                if not self.is_running:
                    break
                
                try:
                    file_path = Path(record.filename)
                    if not file_path.exists():
                        logger.error(f"파일을 찾을 수 없습니다: {record.filename}")
                        failed_count += 1
                        continue
                    
                    # Upload markdown images
                    upload_markdown_images(str(file_path))
                    
                    # Mark as converted
                    record.is_converted = True
                    self.loop.run_until_complete(record.save())
                    
                    converted_count += 1
                    logger.info(f"Successfully converted: {file_path.name}")
                    
                    # Update progress
                    self.progress.emit(
                        f"변환 완료: {file_path.name} ({converted_count}/{total_records})",
                        converted_count + failed_count,
                        total_records
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to convert {record.filename}: {e}")
                    failed_count += 1
                    
                    self.progress.emit(
                        f"실패: {Path(record.filename).name} ({e})",
                        converted_count + failed_count,
                        total_records
                    )
                    
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            self.progress.emit(f"오류 발생: {e}", 0, 0)
        finally:
            self.finished.emit()
            
    def stop(self):
        """Stop conversion process"""
        self.is_running = False
        
    async def _get_records_to_convert(self):
        """Get records that need conversion"""
        records = await PublishRecord.filter(
            workspace=self.workspace,
            is_converted=False,
            status="scheduled"
        ).all()
        return records


class SchedulerThread(QThread):
    """Schedule files for publishing by creating PublishRecord entries."""
    progress = Signal(str, int, int)  # message, current, total
    finished = Signal()
    
    def __init__(self, workspace, loop):
        super().__init__()
        self.workspace = workspace
        self.loop = loop
        self.is_running = True
        
    def run(self):
        """Schedule markdown files for publishing"""
        try:
            # Get markdown files from folder
            folder_path = Path(self.workspace.folder_path)
            if not folder_path.exists():
                self.progress.emit("폴더가 존재하지 않습니다.", 0, 0)
                return
                
            md_files = list(folder_path.glob("*.md"))
            total_files = len(md_files)
            
            if total_files == 0:
                self.progress.emit("마크다운 파일이 없습니다.", 0, 0)
                return
                
            # Get settings for interval
            settings = self.loop.run_until_complete(self._get_settings())
            
            # Calculate publish schedule
            interval = self.workspace.publish_interval
            if interval == "daily":
                time_delta = timedelta(days=1)
            elif interval == "weekly":
                time_delta = timedelta(weeks=1)
            elif interval and interval.startswith("custom:"):
                hours = int(interval.split(":")[1])
                time_delta = timedelta(hours=hours)
            else:
                time_delta = timedelta(days=1)
                
            # Start scheduling
            current_time = datetime.now()
            scheduled_count = 0
            
            for i, md_file in enumerate(md_files):
                if not self.is_running:
                    break
                
                # Calculate scheduled time
                scheduled_time = current_time + (time_delta * i)
                
                # Check if already published or scheduled
                existing_record = self.loop.run_until_complete(
                    self._check_existing_record(md_file.name)
                )
                
                if existing_record:
                    if existing_record.status == "published":
                        logger.info(f"Skipping already published file: {md_file.name}")
                        continue
                    # Update existing record
                    existing_record.scheduled = scheduled_time
                    existing_record.status = "scheduled"
                    self.loop.run_until_complete(existing_record.save())
                    logger.info(f"Updated schedule for: {md_file.name}")
                else:
                    # Create new record
                    self.loop.run_until_complete(
                        self._create_publish_record(
                            str(md_file),  # Full path
                            scheduled_time,
                            self.workspace.blog_id
                        )
                    )
                    logger.info(f"Scheduled: {md_file.name} for {scheduled_time}")
                
                scheduled_count += 1
                self.progress.emit(
                    f"{scheduled_count}/{total_files} 파일 스케줄링 완료",
                    scheduled_count,
                    total_files
                )
                
        except Exception as e:
            logger.error(f"Scheduling error: {e}")
            self.progress.emit(f"오류 발생: {e}", 0, 0)
        finally:
            self.finished.emit()
            
    def stop(self):
        """Stop scheduling process"""
        self.is_running = False
        
    async def _get_settings(self):
        """Get settings from database"""
        settings = {}
        all_settings = await Setting.all()
        for setting in all_settings:
            settings[setting.key] = setting.value
        return settings
        
    async def _create_publish_record(self, filename, scheduled, blog_id):
        """Create publish record with scheduled status"""
        record = await PublishRecord.create(
            filename=filename,
            scheduled=scheduled,
            blog_id=blog_id,
            workspace=self.workspace,
            status="scheduled"
        )
        return record
        
    async def _check_existing_record(self, filename):
        """Check if record already exists for this file"""
        try:
            record = await PublishRecord.filter(
                filename=filename,
                workspace=self.workspace
            ).first()
            return record
        except Exception:
            return None


class PublisherThread(QThread):
    """Publish files based on PublishRecord entries."""
    progress = Signal(str, int, int)  # message, current, total
    finished = Signal()
    
    def __init__(self, workspace, loop):
        super().__init__()
        self.workspace = workspace
        self.loop = loop
        self.is_running = True
        
    def run(self):
        """Publish based on PublishRecord entries"""
        try:
            # Get records that need publishing (failed or scheduled)
            records_to_publish = self.loop.run_until_complete(
                self._get_records_to_publish()
            )
            
            total_records = len(records_to_publish)
            
            if total_records == 0:
                self.progress.emit("발행할 항목이 없습니다.", 0, 0)
                return
            
            self.progress.emit(f"총 {total_records}개 항목 발행 시작", 0, total_records)
            
            published_count = 0
            failed_count = 0
            
            for record in records_to_publish:
                if not self.is_running:
                    break
                
                try:
                    # Update status to publishing
                    record.status = "publishing"
                    self.loop.run_until_complete(record.save())
                    
                    # Get file path
                    file_path = Path(record.filename)
                    if not file_path.exists():
                        logger.error(f"파일을 찾을 수 없습니다: {record.filename}")
                        record.status = "failed"
                        record.error_message = f"파일 없음: {record.filename}"
                        self.loop.run_until_complete(record.save())
                        failed_count += 1
                        self.progress.emit(
                            f"실패: {file_path.name} (파일 없음)",
                            published_count + failed_count,
                            total_records
                        )
                        continue
                    
                    # Get title from markdown file
                    title = read_first_header_from_md(str(file_path))
                    if not title:
                        title = file_path.stem
                    
                    # Determine if scheduled or immediate
                    datetime_string = None
                    if record.scheduled:
                        try:
                            # Check if record.scheduled is timezone-aware
                            if record.scheduled.tzinfo is None:
                                # Make it timezone-aware (assume UTC)
                                scheduled_time = record.scheduled.replace(tzinfo=timezone.utc)
                            else:
                                scheduled_time = record.scheduled
                            
                            # Make datetime.now() timezone-aware
                            now = datetime.now(timezone.utc)
                            
                            # Calculate hours until scheduled time
                            hours_until = (scheduled_time - now).total_seconds() / 3600
                            if hours_until > 0:
                                # Schedule for future time
                                datetime_string = get_datetime_after_hour(hours_until)
                                logger.info(f"Publishing on schedule: {record.filename} at {record.scheduled}")
                            else:
                                # Past scheduled time, publish now
                                logger.info(f"Scheduled time passed, publishing now: {record.filename}")
                        except Exception as e:
                            logger.error(f"Error calculating schedule time: {e}, publishing now")
                    else:
                        # No schedule, publish immediately
                        logger.info(f"Publishing immediately: {record.filename}")
                    
                    # Publish with is_draft=False (always publish, never draft)
                    result = upload_to_blogspot(
                        title=title,
                        fn=str(file_path),
                        BLOG_ID=record.blog_id,
                        is_draft=False,
                        datetime_string=datetime_string,
                        labels=None,
                        search_description=title,
                        thumbnail=None
                    )
                    
                    # Update record with success
                    record.status = "published"
                    record.post_id = result.get("id")
                    record.post_url = result.get("url")
                    record.published_at = datetime.now()
                    self.loop.run_until_complete(record.save())
                    
                    published_count += 1
                    logger.info(f"Successfully published: {file_path.name}")
                    
                    # Update progress
                    self.progress.emit(
                        f"발행 완료: {file_path.name} ({published_count}/{total_records})",
                        published_count + failed_count,
                        total_records
                    )
                    
                    # Wait 10 seconds between publishes to avoid rate limiting
                    if published_count + failed_count < total_records:
                        self.progress.emit(
                            f"10초 대기 중... (API rate limit 방지)",
                            published_count + failed_count,
                            total_records
                        )
                        self.msleep(10000)  # 10 seconds
                    
                except Exception as e:
                    logger.error(f"Failed to publish {record.filename}: {e}")
                    record.status = "failed"
                    record.error_message = str(e)
                    self.loop.run_until_complete(record.save())
                    failed_count += 1
                    
                    self.progress.emit(
                        f"실패: {Path(record.filename).name} ({e})",
                        published_count + failed_count,
                        total_records
                    )
                    
        except Exception as e:
            logger.error(f"Publishing error: {e}")
            self.progress.emit(f"오류 발생: {e}", 0, 0)
        finally:
            self.finished.emit()
            
    def stop(self):
        """Stop publishing process"""
        self.is_running = False
        
    async def _get_records_to_publish(self):
        """Get records that need publishing (failed or scheduled)"""
        records = await PublishRecord.filter(
            workspace=self.workspace,
            status__in=["scheduled"]
        ).all()
        return records
