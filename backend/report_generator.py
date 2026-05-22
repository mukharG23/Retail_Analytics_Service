import os
from groq import Groq
from dotenv import load_dotenv
from traffic_analyzer import analyze_traffic
from datetime import datetime

load_dotenv()

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

def generate_ai_report():
    analysis = analyze_traffic()

    if analysis is None:
        print("No data to generate report")
        return None

    prompt = f"""
You are a retail analytics assistant for a mall management system.
Based on the following foot traffic data, write a professional executive summary report for mall management.

Traffic Data:
- Total images analyzed: {analysis['total_uploads']}
- Total people detected: {analysis['total_people_detected']}
- Busiest aisle: {analysis['busiest_aisle']}
- Peak shopping hour: {analysis['peak_hour']}
- Average people per aisle: {analysis['average_per_aisle']}

Write a concise professional report covering:
1. Overall traffic summary
2. Key findings and patterns
3. Specific recommendations for mall management
4. Staffing suggestions based on peak hours

Keep the tone professional and the report under 300 words.
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
        f.write(report_content)

    print(f"AI report saved to: {report_path}")
    return report_path