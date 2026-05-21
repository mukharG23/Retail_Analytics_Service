def get_congestion_level(people_count):
    if people_count <= 5:
        return 'LOW'
    elif people_count <= 15:
        return 'MEDIUM'
    else:
        return 'HIGH'

def get_top_congested_aisles(logs, n=3):
    sorted_logs = sorted(logs, key=lambda x: x['people_count'], reverse=True)
    return sorted_logs[:n]