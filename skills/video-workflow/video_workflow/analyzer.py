"""
视频分析模块
提取视频关键信息、帧、字幕等
"""

import os
import json
import subprocess
from pathlib import Path

class VideoAnalyzer:
    """视频分析器"""
    
    @staticmethod
    def extract_video_info(video_path):
        """
        提取视频基本信息
        
        Returns:
            dict: 视频信息
        """
        if not os.path.exists(video_path):
            return {"error": "File not found"}
        
        # 基础文件信息
        info = {
            "file_name": os.path.basename(video_path),
            "file_size_mb": round(os.path.getsize(video_path) / (1024 * 1024), 2),
            "file_path": video_path,
        }
        
        # 尝试使用 ffprobe 获取详细信息
        try:
            import sys
            sys.path.insert(0, r'F:\openclaw1\.openclaw\workspace\skills\video-workflow')
            from video_workflow import FFmpegManager
            
            ffmpeg_dir = Path(r'F:\openclaw1\.openclaw\tools\ffmpeg\bin')
            ffprobe = ffmpeg_dir / 'ffprobe.exe' if ffmpeg_dir.exists() else 'ffprobe'
            
            cmd = [
                str(ffprobe),
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-show_entries', 'stream=width,height,r_frame_rate',
                '-of', 'json',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                probe_info = json.loads(result.stdout)
                
                # 解析 ffprobe 输出
                if 'format' in probe_info:
                    duration = float(probe_info['format'].get('duration', 0))
                    info['duration_seconds'] = round(duration, 2)
                    info['duration_formatted'] = f"{int(duration//60)}:{int(duration%60):02d}"
                
                if 'streams' in probe_info and len(probe_info['streams']) > 0:
                    stream = probe_info['streams'][0]
                    info['width'] = stream.get('width')
                    info['height'] = stream.get('height')
                    
                    # 解析帧率
                    fps_str = stream.get('r_frame_rate', '0/1')
                    if '/' in fps_str:
                        num, den = fps_str.split('/')
                        info['fps'] = round(float(num) / float(den), 2) if float(den) != 0 else 0
                    else:
                        info['fps'] = float(fps_str)
                    
                    # 计算总帧数
                    if 'duration_seconds' in info and info['fps'] > 0:
                        info['total_frames'] = int(info['duration_seconds'] * info['fps'])
                    
                    # 视频质量评估
                    if info.get('height', 0) >= 1080:
                        info['quality'] = '1080p HD'
                    elif info.get('height', 0) >= 720:
                        info['quality'] = '720p HD'
                    else:
                        info['quality'] = 'SD'
                        
        except Exception as e:
            info['ffprobe_error'] = str(e)
            info['duration_seconds'] = 0
        
        return info
    
    @staticmethod
    def generate_report(video_path, output_path=None):
        """
        生成视频分析报告
        """
        info = VideoAnalyzer.extract_video_info(video_path)
        
        report = {
            "video_info": info,
            "analysis_summary": {},
            "recommendations": []
        }
        
        # 生成摘要
        if 'duration_seconds' in info:
            duration = info['duration_seconds']
            if duration < 60:
                report['analysis_summary']['type'] = '短视频'
                report['analysis_summary']['suitable_for'] = '快速预览、社交媒体'
            elif duration < 300:
                report['analysis_summary']['type'] = '中等视频'
                report['analysis_summary']['suitable_for'] = '教程、演示'
            else:
                report['analysis_summary']['type'] = '长视频'
                report['analysis_summary']['suitable_for'] = '电影、详细教程'
        
        # 添加建议
        if info.get('duration_seconds', 0) > 300:
            report['recommendations'].append('视频较长，建议提取关键片段或生成摘要')
        
        if info.get('height', 0) >= 1080:
            report['recommendations'].append('高清视频，适合大屏观看和二次剪辑')
        
        if info.get('file_size_mb', 0) > 100:
            report['recommendations'].append('文件较大，建议压缩后再分享')
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report


# 便捷函数
__all__ = ['VideoAnalyzer']
