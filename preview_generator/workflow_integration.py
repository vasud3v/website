#!/usr/bin/env python3
"""
Workflow Integration for GitHub Actions
Integrates preview generation with video processing pipeline
"""
import os
import sys
import json
from typing import Dict, Optional
from preview_generator import PreviewGenerator

class WorkflowIntegration:
    """
    Integrates preview generation into video processing workflow
    """
    
    def __init__(self, video_path: str, video_code: str, video_title: str):
        self.video_path = video_path
        self.video_code = video_code
        self.video_title = video_title
        self.temp_dir = os.path.dirname(video_path)
        
    def generate_and_upload_preview(
        self,
        upload_function,
        folder_name: str = None,
        num_clips: int = 10,
        clip_duration: float = 3.0,
        resolution: str = "720",
        create_gif: bool = False,
        parallel: bool = True
    ) -> Dict:
        """
        Generate preview and upload to hosting
        
        Args:
            upload_function: Function to upload preview (e.g., upload_to_streamwish)
            folder_name: Folder name for upload (e.g., "JAV_VIDEOS/CODE-123")
            num_clips: Number of clips to extract
            clip_duration: Duration of each clip
            resolution: Target resolution
            create_gif: Also create GIF
            parallel: Use parallel processing
        
        Returns:
            Dict with preview URLs and metadata
        """
        print("\n" + "=" * 60)
        print("PREVIEW GENERATION & UPLOAD")
        print("=" * 60)
        
        result = {
            'success': False,
            'preview_video_url': None,
            'preview_gif_url': None,
            'preview_file_size_mb': 0,
            'preview_duration': 0,
            'num_clips': 0,
            'error': None
        }
        
        # Validate inputs
        if not os.path.exists(self.video_path):
            result['error'] = f'Video file not found: {self.video_path}'
            print(f"✗ {result['error']}")
            return result
        
        if not upload_function:
            result['error'] = 'Upload function not provided'
            print(f"✗ {result['error']}")
            return result
        
        try:
            # Step 1: Generate preview
            print(f"\n[1/3] Generating preview for {self.video_code}...")
            
            preview_output = os.path.join(self.temp_dir, f"{self.video_code}_preview.mp4")
            gif_output = os.path.join(self.temp_dir, f"{self.video_code}_preview.gif") if create_gif else None
            
            generator = PreviewGenerator(self.video_path, self.temp_dir)
            
            preview_result = generator.generate_preview(
                output_path=preview_output,
                num_clips=num_clips,
                clip_duration=clip_duration,
                resolution=resolution,
                crf=28,  # Good compression for previews
                fps=30,
                create_gif=create_gif,
                gif_width=480,
                cleanup=True,
                parallel=parallel
            )
            
            if not preview_result or not preview_result.get('success'):
                result['error'] = 'Preview generation failed'
                print(f"✗ Preview generation failed")
                return result
            
            if not os.path.exists(preview_output):
                result['error'] = 'Preview file not created'
                print(f"✗ Preview file not found after generation")
                return result
            
            print(f"✓ Preview generated: {preview_result['file_size_mb']:.1f} MB")
            
            # Step 2: Upload preview video
            print(f"\n[2/3] Uploading preview video...")
            
            preview_title = f"{self.video_code} - PREVIEW"
            
            upload_result = upload_function(
                preview_output,
                self.video_code,
                preview_title,
                folder_name
            )
            
            if upload_result and upload_result.get('success'):
                result['preview_video_url'] = upload_result.get('embed_url')
                print(f"✓ Preview uploaded: {result['preview_video_url']}")
            else:
                result['error'] = 'Preview upload failed'
                print(f"✗ Preview upload failed")
                # Cleanup and return
                try:
                    if os.path.exists(preview_output):
                        os.remove(preview_output)
                except:
                    pass
                return result
            
            # Step 3: Upload GIF (if created)
            if create_gif and preview_result.get('gif_path') and os.path.exists(preview_result['gif_path']):
                print(f"\n[3/3] Uploading preview GIF...")
                
                gif_title = f"{self.video_code} - PREVIEW GIF"
                
                try:
                    gif_upload_result = upload_function(
                        preview_result['gif_path'],
                        self.video_code,
                        gif_title,
                        folder_name
                    )
                    
                    if gif_upload_result and gif_upload_result.get('success'):
                        result['preview_gif_url'] = gif_upload_result.get('embed_url')
                        print(f"✓ GIF uploaded: {result['preview_gif_url']}")
                    else:
                        print(f"⚠️ GIF upload failed, continuing...")
                except Exception as e:
                    print(f"⚠️ GIF upload error: {e}")
            else:
                print(f"\n[3/3] Skipping GIF upload")
            
            # Cleanup preview files
            print(f"\nCleaning up preview files...")
            try:
                if os.path.exists(preview_output):
                    os.remove(preview_output)
                    print(f"✓ Removed {preview_output}")
                
                if gif_output and os.path.exists(gif_output):
                    os.remove(gif_output)
                    print(f"✓ Removed {gif_output}")
            except Exception as e:
                print(f"⚠️ Cleanup warning: {e}")
            
            # Build result
            result.update({
                'success': True,
                'preview_file_size_mb': preview_result['file_size_mb'],
                'preview_duration': preview_result['total_duration'],
                'num_clips': preview_result['num_clips'],
                'resolution': preview_result['resolution'],
                'error': None
            })
            
            print("\n" + "=" * 60)
            print("PREVIEW UPLOAD COMPLETE")
            print("=" * 60)
            print(f"Video URL: {result['preview_video_url']}")
            if result['preview_gif_url']:
                print(f"GIF URL: {result['preview_gif_url']}")
            print(f"Size: {result['preview_file_size_mb']:.1f} MB")
            print(f"Duration: {result['preview_duration']:.1f}s")
            print(f"Clips: {result['num_clips']}")
            print("=" * 60)
            
            return result
            
        except Exception as e:
            print(f"\n✗ Error in preview workflow: {e}")
            import traceback
            traceback.print_exc()
            
            result['error'] = str(e)
            return result
    
    def add_preview_to_metadata(
        self,
        video_data: Dict,
        preview_result: Dict
    ) -> Dict:
        """
        Add preview information to video metadata
        
        Args:
            video_data: Existing video metadata dict
            preview_result: Result from generate_and_upload_preview
        
        Returns:
            Updated video metadata
        """
        if preview_result['success']:
            video_data['preview_video_url'] = preview_result['preview_video_url']
            video_data['preview_gif_url'] = preview_result.get('preview_gif_url')
            video_data['preview_duration'] = preview_result['preview_duration']
            video_data['preview_clips'] = preview_result['num_clips']
            video_data['preview_file_size_mb'] = preview_result['preview_file_size_mb']
            video_data['preview_generated'] = True
        else:
            video_data['preview_generated'] = False
            video_data['preview_error'] = preview_result.get('error')
        
        return video_data


def integrate_with_workflow(
    video_path: str,
    video_code: str,
    video_title: str,
    upload_function,
    folder_name: str = None,
    enable_preview: bool = True,
    enable_gif: bool = False
) -> Optional[Dict]:
    """
    Convenience function for workflow integration
    
    Args:
        video_path: Path to video file
        video_code: Video code (e.g., "START-451")
        video_title: Video title
        upload_function: Upload function (e.g., upload_to_streamwish)
        folder_name: Upload folder name
        enable_preview: Enable preview generation
        enable_gif: Also create GIF
    
    Returns:
        Preview result dict or None if disabled
    """
    if not enable_preview:
        print("[Preview] Preview generation disabled")
        return None
    
    try:
        integration = WorkflowIntegration(video_path, video_code, video_title)
        
        result = integration.generate_and_upload_preview(
            upload_function=upload_function,
            folder_name=folder_name,
            num_clips=10,
            clip_duration=3.0,
            resolution="720",
            create_gif=enable_gif,
            parallel=True
        )
        
        return result
        
    except Exception as e:
        print(f"[Preview] Error in workflow integration: {e}")
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    # Test integration
    if len(sys.argv) < 4:
        print("Usage: python workflow_integration.py <video_file> <code> <title>")
        sys.exit(1)
    
    video_file = sys.argv[1]
    code = sys.argv[2]
    title = sys.argv[3]
    
    # Mock upload function for testing
    def mock_upload(file_path, code, title, folder):
        print(f"[Mock] Uploading {file_path} to {folder}")
        return {
            'success': True,
            'embed_url': f'https://example.com/e/{code}_preview'
        }
    
    integration = WorkflowIntegration(video_file, code, title)
    result = integration.generate_and_upload_preview(
        upload_function=mock_upload,
        folder_name=f"JAV_VIDEOS/{code}",
        create_gif=True
    )
    
    print(f"\nResult: {json.dumps(result, indent=2)}")
