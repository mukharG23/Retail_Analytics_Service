import os
from groq import Groq
from dotenv import load_dotenv
from traffic_analyzer import analyze_traffic
from database import get_traffic_logs
from datetime import datetime

load_dotenv()

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

def generate_ai_report():
    analysis = analyze_traffic()

    if analysis is None:
        print("No data to generate report")
        return None

    logs = get_traffic_logs()

    video_logs = [l for l in logs if l['filename'].endswith(('.mp4', '.avi', '.mov', '.mkv'))]
    image_logs = [l for l in logs if not l['filename'].endswith(('.mp4', '.avi', '.mov', '.mkv'))]

    video_section = ""
    if video_logs:
        video_section = f"""
Video Analysis Results:
- Total videos analyzed: {len(video_logs)}
- Videos processed: {', '.join(set(l['filename'] for l in video_logs))}
- Peak people count across videos: {max(l['people_count'] for l in video_logs)}
- Video congestion levels: {', '.join(set(l['congestion_level'] for l in video_logs))}
"""

    image_section = ""
    if image_logs:
        image_section = f"""
Static Image Analysis Results:
- Total images analyzed: {len(image_logs)}
- Peak people count across images: {max(l['people_count'] for l in image_logs)}
"""

    prompt = f"""
You are a retail analytics assistant for a mall management system.
Based on the following foot traffic data collected from both CCTV video footage and static store images, write a professional executive summary report for mall management.

Overall Traffic Statistics:
- Total uploads analyzed: {analysis['total_uploads']}
- Total people detected: {analysis['total_people_detected']}
- Busiest aisle: {analysis['busiest_aisle']}
- Peak shopping hour: {analysis['peak_hour']}
- Average people per aisle: {analysis['average_per_aisle']}

{video_section}
{image_section}

Write a concise professional report covering:
1. Overall traffic summary combining both video and image analysis
2. Key findings from CCTV video footage specifically
3. Peak congestion patterns and timings
4. Specific recommendations for mall management
5. Staffing suggestions based on peak hours and congestion levels

Keep the tone professional and the report under 400 words.
"""

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="llama-3.3-70b-versatile",
    )

    report_content = chat_completion.choices[0].message.content

    report_filename = f"ai_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path = os.path.join(os.path.dirname(__file__), '..', 'logs', report_filename)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# AI Generated Executive Report\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Data Sources:** {len(video_logs)} video(s), {len(image_logs)} image(s)\n\n")
        f.write("---\n\n")
        f.write(report_content)

    print(f"AI report saved to: {report_path}")
    return report_path