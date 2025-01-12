import requests
from datetime import datetime
from datetime import timedelta
import xml.etree.ElementTree as ET

def format_time(seconds):
    return str(timedelta(seconds=seconds)).split('.')[0][2:].zfill(5)

def create_confluence_page(meeting_data, api_url, confluence_secret):
    auth = (confluence_secret['email'], confluence_secret['api_token'])

    # Build the page title
    current_date = datetime.now().strftime("%Y-%m-%d")
    page_title = f"Meeting Minutes - {current_date}"

    # Create HTML structure using xml.etree.ElementTree
    root = ET.Element("html")
    body = ET.SubElement(root, "body")

    h2 = ET.SubElement(body, "h2")
    h2.text = "Meeting Minutes"

    date_paragraph = ET.SubElement(body, "h3")
    date_paragraph.text = f"Date: {current_date}"

    participants_paragraph = ET.SubElement(body, "h3")
    participants_paragraph.text = f"Participants: {', '.join(meeting_data.get('Participants', []))}"

    goals_paragraph = ET.SubElement(body, "h3")
    goals_paragraph.text = f"Goals: {meeting_data.get('Goals', 'N/A')}"

    # Discussion Topics Table
    discussion_topics_header = ET.SubElement(body, "h3")
    discussion_topics_header.text = "Discussion Topics"
    table = ET.SubElement(body, "table")

    # Table headers
    header_row = ET.SubElement(table, "tr")
    headers = ["Time", "Item", "Presenter", "Notes"]
    for header in headers:
        th = ET.SubElement(header_row, "th")
        th.text = header

    # Add table rows for each discussion topic
    for topic in meeting_data.get('DiscussionTopics', []):
        row = ET.SubElement(table, "tr")
        for key in headers:
            td = ET.SubElement(row, "td")
            if key == "Time":
                time_range = topic.get('Time', '0.0 - 0.0')
                start_time_str, end_time_str = time_range.split(' - ')
                start_time = format_time(float(start_time_str))
                end_time = format_time(float(end_time_str))
                td.text = f"{start_time} - {end_time}"
            else:
                td.text = topic.get(key, 'N/A')

    # Action Items List
    action_items_header = ET.SubElement(body, "h3")
    action_items_header.text = "Action Items"
    action_items_list = ET.SubElement(body, "ul")
    for item in meeting_data.get('ActionItems', []):
        li = ET.SubElement(action_items_list, "li")
        li.text = item

    # Decisions List
    decisions_header = ET.SubElement(body, "h3")
    decisions_header.text = "Decisions"
    decisions_list = ET.SubElement(body, "ul")
    for decision in meeting_data.get('Decisions', []):
        li = ET.SubElement(decisions_list, "li")
        li.text = decision

    html_content = ET.tostring(root, encoding='unicode')

    storage_format_content = {
        "type": "page",
        "title": page_title,
        "space": {
            "key": confluence_secret['space_key']
        },
        "body": {
            "storage": {
                "value": html_content,
                "representation": "storage"
            }
        }
    }

    return requests.post(
        api_url, 
        json=storage_format_content, 
        auth=auth, 
        headers={'Content-Type': 'application/json'}
    )