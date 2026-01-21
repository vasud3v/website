"""
Test gallery viewer for scraped screenshots
Creates an HTML page to view screenshots in a gallery
"""

import json
import sys
from pathlib import Path

def create_gallery_html(video_code: str, video_data: dict):
    """Create HTML gallery page"""
    
    screenshots = video_data.get('screenshots', [])
    title = video_data.get('title', video_code)
    cast = video_data.get('cast', [])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{video_code} - Screenshot Gallery</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #0a0a0a;
            color: #fff;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #333;
        }}
        
        .header h1 {{
            font-size: 24px;
            margin-bottom: 10px;
            color: #ff1744;
        }}
        
        .header p {{
            color: #999;
            font-size: 14px;
        }}
        
        .cast-info {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        
        .cast-card {{
            background: #1a1a1a;
            padding: 15px;
            border-radius: 8px;
            display: flex;
            gap: 15px;
            align-items: center;
        }}
        
        .cast-image {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #ff1744;
        }}
        
        .cast-details {{
            flex: 1;
        }}
        
        .cast-name {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .cast-name-jp {{
            color: #999;
            font-size: 14px;
            margin-bottom: 8px;
        }}
        
        .cast-stats {{
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
        }}
        
        .cast-stat {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        
        .gallery-item {{
            position: relative;
            aspect-ratio: 16/9;
            overflow: hidden;
            border-radius: 8px;
            cursor: pointer;
            transition: transform 0.3s ease;
            background: #1a1a1a;
        }}
        
        .gallery-item:hover {{
            transform: scale(1.05);
        }}
        
        .gallery-item img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .gallery-item .number {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255, 23, 68, 0.9);
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        
        /* Lightbox */
        .lightbox {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }}
        
        .lightbox.active {{
            display: flex;
        }}
        
        .lightbox-content {{
            max-width: 90%;
            max-height: 90%;
            position: relative;
        }}
        
        .lightbox-content img {{
            max-width: 100%;
            max-height: 90vh;
            object-fit: contain;
        }}
        
        .lightbox-close {{
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 40px;
            color: white;
            cursor: pointer;
            background: rgba(255, 23, 68, 0.8);
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            line-height: 1;
        }}
        
        .lightbox-nav {{
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            font-size: 40px;
            color: white;
            cursor: pointer;
            background: rgba(255, 23, 68, 0.8);
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .lightbox-prev {{
            left: 20px;
        }}
        
        .lightbox-next {{
            right: 20px;
        }}
        
        .stats {{
            display: flex;
            gap: 30px;
            margin: 20px 0;
            padding: 15px;
            background: #1a1a1a;
            border-radius: 8px;
        }}
        
        .stat-item {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
        }}
        
        .stat-value {{
            color: #fff;
            font-size: 16px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{video_code}</h1>
            <p>{title}</p>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <span class="stat-label">Screenshots</span>
                <span class="stat-value">{len(screenshots)}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Release</span>
                <span class="stat-value">{video_data.get('release_date', 'N/A')}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Runtime</span>
                <span class="stat-value">{video_data.get('runtime_minutes', 'N/A')} min</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Studio</span>
                <span class="stat-value">{video_data.get('studio', 'N/A')}</span>
            </div>
        </div>
"""
    
    # Add cast info
    if cast:
        html += '        <div class="cast-info">\n'
        for actress in cast:
            age_text = f"{actress.get('age')} years" if actress.get('age') else "N/A"
            height_text = f"{actress.get('height_cm')}cm" if actress.get('height_cm') else "N/A"
            
            html += f"""            <div class="cast-card">
                <img src="{actress.get('image_url', '')}" alt="{actress.get('name', '')}" class="cast-image" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22%3E%3Crect fill=%22%23333%22 width=%22100%22 height=%22100%22/%3E%3Ctext fill=%22%23666%22 x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 font-size=%2240%22%3E?%3C/text%3E%3C/svg%3E'">
                <div class="cast-details">
                    <div class="cast-name">{actress.get('name', 'Unknown')}</div>
                    <div class="cast-name-jp">{actress.get('name_jp', '')}</div>
                    <div class="cast-stats">
                        <span class="cast-stat">👤 {age_text}</span>
                        <span class="cast-stat">📏 {height_text}</span>
                        <span class="cast-stat">🎬 {actress.get('debut_date', 'N/A')}</span>
                    </div>
                </div>
            </div>
"""
        html += '        </div>\n'
    
    # Add gallery
    html += '        <div class="gallery">\n'
    for i, screenshot in enumerate(screenshots, 1):
        html += f"""            <div class="gallery-item" onclick="openLightbox({i-1})">
                <img src="{screenshot}" alt="Screenshot {i}" loading="lazy">
                <div class="number">{i}</div>
            </div>
"""
    html += '        </div>\n'
    
    # Add lightbox
    html += """        
        <div class="lightbox" id="lightbox" onclick="closeLightbox(event)">
            <div class="lightbox-close" onclick="closeLightbox(event)">&times;</div>
            <div class="lightbox-prev" onclick="prevImage(event)">&#8249;</div>
            <div class="lightbox-next" onclick="nextImage(event)">&#8250;</div>
            <div class="lightbox-content">
                <img id="lightbox-img" src="" alt="Screenshot">
            </div>
        </div>
    </div>
    
    <script>
        const screenshots = """ + json.dumps(screenshots) + """;
        let currentIndex = 0;
        
        function openLightbox(index) {
            currentIndex = index;
            document.getElementById('lightbox-img').src = screenshots[currentIndex];
            document.getElementById('lightbox').classList.add('active');
        }
        
        function closeLightbox(event) {
            if (event.target.id === 'lightbox' || event.target.classList.contains('lightbox-close')) {
                document.getElementById('lightbox').classList.remove('active');
            }
        }
        
        function nextImage(event) {
            event.stopPropagation();
            currentIndex = (currentIndex + 1) % screenshots.length;
            document.getElementById('lightbox-img').src = screenshots[currentIndex];
        }
        
        function prevImage(event) {
            event.stopPropagation();
            currentIndex = (currentIndex - 1 + screenshots.length) % screenshots.length;
            document.getElementById('lightbox-img').src = screenshots[currentIndex];
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', function(e) {
            if (!document.getElementById('lightbox').classList.contains('active')) return;
            
            if (e.key === 'Escape') {
                document.getElementById('lightbox').classList.remove('active');
            } else if (e.key === 'ArrowRight') {
                nextImage(e);
            } else if (e.key === 'ArrowLeft') {
                prevImage(e);
            }
        });
    </script>
</body>
</html>
"""
    
    return html


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_gallery.py <video_code>")
        print("Example: python test_gallery.py MIDA-486")
        sys.exit(1)
    
    video_code = sys.argv[1].upper()
    
    # Import scraper
    from scrape_clean import CleanJAVDBScraper
    from dataclasses import asdict
    
    # Run scraper
    print(f"Scraping {video_code}...")
    scraper = CleanJAVDBScraper(headless=True)
    
    try:
        scraper._init_driver()
        video_data_obj = scraper.scrape_video_by_code(video_code)
        
        if not video_data_obj:
            print("Video not found")
            sys.exit(1)
        
        video_data = asdict(video_data_obj)
        
        # Create gallery HTML
        html = create_gallery_html(video_code, video_data)
        
        # Save to file
        output_file = f"database/{video_code}_gallery.html"
        Path(output_file).parent.mkdir(exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✓ Gallery created: {output_file}")
        print(f"✓ Screenshots: {len(video_data.get('screenshots', []))}")
        print(f"✓ Cast: {len(video_data.get('cast', []))}")
        
        # Get absolute path
        abs_path = Path(output_file).absolute()
        print(f"\nOpen in browser:")
        print(f"file:///{abs_path}")
        
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
