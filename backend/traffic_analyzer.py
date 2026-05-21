import pandas as pd
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.db')
LOGS_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs')
CAPACITY_THRESHOLD = 15

def get_dataframe():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('SELECT * FROM traffic_logs', conn)
    conn.close()
    return df

def analyze_traffic():
    df = get_dataframe()

    if df.empty:
        print("No data to analyze")
        return None

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour

    avg_per_aisle = df.groupby('aisle')['people_count'].mean().round(2)
    peak_hour = df.groupby('hour')['people_count'].sum().idxmax()
    busiest_aisle = df.groupby('aisle')['people_count'].sum().idxmax()
    total_uploads = len(df)
    total_people = df['people_count'].sum()

    analysis = {
        'total_uploads': total_uploads,
        'total_people_detected': int(total_people),
        'busiest_aisle': busiest_aisle,
        'peak_hour': f"{peak_hour}:00 - {peak_hour+1}:00",
        'average_per_aisle': avg_per_aisle.to_dict()
    }

    print(f"Analysis complete: {analysis}")
    return analysis

def generate_audit_log():
    df = get_dataframe()

    if df.empty:
        print("No data for audit log")
        return None

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report_lines = [
        f"# Retail Mall Audit Log",
        f"**Generated:** {timestamp}\n",
        f"## Traffic Summary",
    ]

    total_uploads = len(df)
    total_people = df['people_count'].sum()
    report_lines.append(f"- Total images analyzed: {total_uploads}")
    report_lines.append(f"- Total people detected: {total_people}\n")

    report_lines.append(f"## Capacity Alerts (threshold: {CAPACITY_THRESHOLD} people)\n")

    alerts = df[df['people_count'] >= CAPACITY_THRESHOLD]

    if alerts.empty:
        report_lines.append("No capacity alerts. All aisles within normal limits.")
    else:
        for _, row in alerts.iterrows():
            report_lines.append(
                f"- ⚠️ **{row['aisle']}** exceeded capacity with "
                f"**{row['people_count']} people** at {row['timestamp']}"
            )

    report_lines.append(f"\n## Per Aisle Summary\n")
    aisle_summary = df.groupby('aisle')['people_count'].agg(['mean', 'max', 'min']).round(2)
    for aisle, stats in aisle_summary.iterrows():
        report_lines.append(f"### {aisle}")
        report_lines.append(f"- Average: {stats['mean']} people")
        report_lines.append(f"- Peak: {stats['max']} people")
        report_lines.append(f"- Minimum: {stats['min']} people\n")

    report_content = '\n'.join(report_lines)

    report_filename = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path = os.path.join(LOGS_PATH, report_filename)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"Audit log saved to: {report_path}")
    return report_path